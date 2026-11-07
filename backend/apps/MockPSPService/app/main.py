"""MOCK of an external payment provider. In-memory, resets on restart.

Behaviors it imitates (so our services must cope with them):
- Idempotency: POST with the same Idempotency-Key + same body returns the SAME object
  (no second charge); same key + different body -> 409.
- Eventual consistency: a charge is created `pending` and only settles after
  PSP_SETTLE_DELAY_S. Reading it earlier shows `pending`.
- Webhooks: delivered at-least-once (retried until 2xx, then once more as a duplicate).
- Failure knobs: amount 13 -> charge fails; amount 77 -> webhook is never sent
  (must be found by polling); POST /admin/fail-next {"count": n} fails the next n charges.
"""
import asyncio
import hashlib
import json
import logging
import os
import time
import uuid

import httpx
from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel

logger = logging.getLogger("psp")
SETTLE_DELAY = float(os.getenv("PSP_SETTLE_DELAY_S", "2"))

app = FastAPI(title="Mock PSP")

_charges: dict[str, dict] = {}
_transfers: dict[str, dict] = {}
_idempotency: dict[str, tuple[str, str]] = {}  # key -> (request hash, object id)
_tasks: set[asyncio.Task] = set()
_fail_next = 0


class ChargeIn(BaseModel):
    amount: int
    method: str
    reference: str | None = None
    webhook_url: str | None = None


class TransferIn(BaseModel):
    amount: int
    destination: str


def _digest(body: BaseModel) -> str:
    return hashlib.sha256(json.dumps(body.model_dump(), sort_keys=True).encode()).hexdigest()


def _replay_or_none(scope: str, key: str, body: BaseModel, store: dict) -> dict | None:
    entry = _idempotency.get(f"{scope}:{key}")
    if entry is None:
        return None
    if entry[0] != _digest(body):
        raise HTTPException(409, "Idempotency-Key was already used with a different request")
    return store[entry[1]]


def _charge_view(c: dict) -> dict:
    status = c["final"] if time.time() >= c["settle_at"] else "pending"
    return {"id": c["id"], "status": status, "amount": c["amount"], "method": c["method"], "reference": c["reference"]}


async def _deliver_webhook(c: dict) -> None:
    await asyncio.sleep(SETTLE_DELAY)
    if not c["webhook_url"] or c["amount"] == 77:  # 77: simulate a lost webhook
        return
    payload = {
        "event_id": f"evt_{c['id']}",
        "type": "charge.succeeded" if c["final"] == "succeeded" else "charge.failed",
        "charge_id": c["id"],
    }
    async with httpx.AsyncClient(timeout=5) as client:
        delivered = False
        for _ in range(5):  # retry until the receiver answers 2xx
            try:
                if (await client.post(c["webhook_url"], json=payload,
                    headers={"X-Webhook-Token": os.environ.get("PSP_WEBHOOK_TOKEN", "")})).status_code < 300:
                    delivered = True
                    break
            except httpx.HTTPError:
                pass
            await asyncio.sleep(1)
        if delivered:  # at-least-once: send a duplicate
            try:
                await client.post(c["webhook_url"], json=payload,
                    headers={"X-Webhook-Token": os.environ.get("PSP_WEBHOOK_TOKEN", "")})
            except httpx.HTTPError:
                pass


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/charges", status_code=201)
async def create_charge(
    body: ChargeIn, response: Response, idempotency_key: str = Header(alias="Idempotency-Key")
) -> dict:
    global _fail_next
    existing = _replay_or_none("charge", idempotency_key, body, _charges)
    if existing is not None:
        response.status_code = 200
        response.headers["Idempotent-Replay"] = "true"
        return _charge_view(existing)

    fail = body.amount == 13 or _fail_next > 0
    if _fail_next > 0 and body.amount != 13:
        _fail_next -= 1
    c = {
        "id": f"ch_{uuid.uuid4().hex[:12]}", "amount": body.amount, "method": body.method,
        "reference": body.reference, "webhook_url": body.webhook_url,
        "final": "failed" if fail else "succeeded", "settle_at": time.time() + SETTLE_DELAY,
    }
    _charges[c["id"]] = c
    _idempotency[f"charge:{idempotency_key}"] = (_digest(body), c["id"])
    task = asyncio.create_task(_deliver_webhook(c))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return _charge_view(c)


@app.get("/v1/charges/{charge_id}")
def get_charge(charge_id: str) -> dict:
    if charge_id not in _charges:
        raise HTTPException(404, "charge not found")
    return _charge_view(_charges[charge_id])


@app.post("/v1/transfers", status_code=201)
def create_transfer(body: TransferIn, response: Response, idempotency_key: str = Header(alias="Idempotency-Key")) -> dict:
    existing = _replay_or_none("transfer", idempotency_key, body, _transfers)
    if existing is not None:
        response.status_code = 200
        response.headers["Idempotent-Replay"] = "true"
        return existing
    t = {"id": f"tr_{uuid.uuid4().hex[:12]}", "status": "paid", **body.model_dump()}
    _transfers[t["id"]] = t
    _idempotency[f"transfer:{idempotency_key}"] = (_digest(body), t["id"])
    return t


class FailNext(BaseModel):
    count: int


@app.post("/admin/fail-next")
def fail_next(body: FailNext) -> dict:
    global _fail_next
    _fail_next = body.count
    return {"fail_next": _fail_next}
