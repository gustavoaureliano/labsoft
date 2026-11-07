import asyncio
import hashlib
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID
import secrets

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Response, Request
from pydantic import BaseModel
from sqlalchemy import UniqueConstraint, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from .db import Base, engine, get_session, init_db, utcnow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment")

PSP_URL = os.getenv("PSP_URL", "http://localhost:8007")
SUBSCRIPTION_URL = os.getenv("SUBSCRIPTION_URL", "http://localhost:8003")
METERING_URL = os.getenv("METERING_URL", "http://localhost:8005")
CONTENT_URL = os.getenv("CONTENT_URL", "http://localhost:8006")  # mock of media team (item owners)
SELF_URL = os.getenv("PAYMENT_SELF_URL", "http://localhost:8004")  # where the PSP sends webhooks
RECONCILE_INTERVAL_S = float(os.getenv("RECONCILE_INTERVAL_S", "2"))
RECONCILE_MIN_AGE_S = float(os.getenv("RECONCILE_MIN_AGE_S", "5"))  # give the webhook a chance first
TEACHER_SHARE = float(os.getenv("TEACHER_SHARE", "0.7"))  # share of paid revenue paid out to teachers

METHODS = {"pix", "credito", "boleto"}


class Payment(Base):
    __tablename__ = "payment"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    idempotency_key: Mapped[str] = mapped_column(unique=True)
    request_hash: Mapped[str]
    user_id: Mapped[UUID]
    item_id: Mapped[UUID | None]
    amount: Mapped[int]  # cents
    method: Mapped[str]
    kind: Mapped[str]  # initial | renewal
    plan: Mapped[str]  # one_time | monthly
    status: Mapped[str]  # pending | paid | failed
    psp_charge_id: Mapped[str | None]
    notified: Mapped[bool] = mapped_column(default=False)  # subscription service told about the outcome
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    settled_at: Mapped[datetime | None]

    def view(self) -> dict:
        return {"id": self.id, "user_id": str(self.user_id),
                "course_id": str(self.item_id) if self.item_id else None,
                "amount": self.amount, "method": self.method, "kind": self.kind,
                "plan": self.plan, "status": self.status, "psp_charge_id": self.psp_charge_id}


class Payout(Base):
    __tablename__ = "payout"
    __table_args__ = (UniqueConstraint("period", "item_id"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    period: Mapped[str]  # YYYY-MM
    item_id: Mapped[int]
    teacher_id: Mapped[int]
    seconds: Mapped[int]
    amount: Mapped[int]
    status: Mapped[str]  # due | paid
    psp_transfer_id: Mapped[str | None]

    def view(self) -> dict:
        return {c: getattr(self, c) for c in ("id", "period", "item_id", "teacher_id", "seconds", "amount", "status")}


# ---- PSP + notification plumbing ------------------------------------------------

def submit_to_psp(db: Session, p: Payment) -> None:
    """Idempotent on the PSP side (key = payment id), so safe to retry after any failure."""
    try:
        r = httpx.post(
            f"{PSP_URL}/v1/charges",
            headers={"Idempotency-Key": f"payment-{p.id}"},
            json={"amount": p.amount, "method": p.method, "reference": str(p.id),
                  "webhook_url": f"{SELF_URL}/api/payments/webhooks/psp"},
            timeout=5,
        )
        r.raise_for_status()
        p.psp_charge_id = r.json()["id"]
        db.commit()
    except httpx.HTTPError as e:
        logger.warning("PSP submit failed for payment %s, reconcile will retry: %s", p.id, e)


def notify_subscription(db: Session, p: Payment) -> None:
    """Tell Subscription the outcome. Receiver is idempotent by payment_id; retried by reconcile."""
    try:
        key = os.environ["INTERNAL_SERVICE_TOKEN"]
        r = httpx.post(f"{SUBSCRIPTION_URL}/api/subscriptions/events/payment", timeout=5,
            headers={"X-Service-Token": key}, json={
            "payment_id": p.id, "user_id": str(p.user_id),
            "course_id": str(p.item_id) if p.item_id else None, "amount": p.amount,
            "method": p.method, "kind": p.kind, "plan": p.plan, "status": p.status})
        r.raise_for_status()
        p.notified = True
        db.commit()
    except httpx.HTTPError as e:
        logger.warning("notify failed for payment %s, reconcile will retry: %s", p.id, e)


def settle(db: Session, p: Payment, status: str) -> None:
    """Apply a final outcome. Duplicates / out-of-order events are no-ops once terminal."""
    if p.status == "pending":
        p.status = status
        p.settled_at = utcnow()
        db.commit()
    if p.status != "pending" and not p.notified:
        notify_subscription(db, p)


def reconcile(db: Session, min_age_s: float = RECONCILE_MIN_AGE_S) -> dict:
    """Heal anything the happy path (webhook) missed: unsent charges, lost webhooks, lost notifications."""
    cutoff = utcnow() - timedelta(seconds=min_age_s)
    stats = {"resubmitted": 0, "settled": 0, "renotified": 0}
    for p in db.scalars(select(Payment).where(Payment.status == "pending", Payment.created_at <= cutoff)):
        if p.psp_charge_id is None:
            submit_to_psp(db, p)
            stats["resubmitted"] += 1
        if p.psp_charge_id is None:
            continue
        try:
            charge = httpx.get(f"{PSP_URL}/v1/charges/{p.psp_charge_id}", timeout=5).json()
        except (httpx.HTTPError, ValueError):
            continue
        if charge["status"] in ("succeeded", "failed"):
            settle(db, p, "paid" if charge["status"] == "succeeded" else "failed")
            stats["settled"] += 1
    for p in db.scalars(select(Payment).where(Payment.status != "pending", Payment.notified.is_(False))):
        notify_subscription(db, p)
        stats["renotified"] += 1
    return stats


async def reconcile_loop() -> None:
    while True:
        await asyncio.sleep(RECONCILE_INTERVAL_S)
        try:
            with Session(engine) as db:
                await asyncio.to_thread(reconcile, db)
        except Exception:
            logger.exception("reconcile loop error")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if len(os.getenv("INTERNAL_SERVICE_TOKEN", "")) < 16:
        raise RuntimeError("Configure INTERNAL_SERVICE_TOKEN for the payment service")
    task = asyncio.create_task(reconcile_loop())
    yield
    task.cancel()


app = FastAPI(title="Servico de Pagamentos", lifespan=lifespan)


@app.middleware("http")
async def private_responses(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers.setdefault("Vary", "Cookie, Authorization")
    return response


def require_service_token(value: str | None):
    expected = os.getenv("INTERNAL_SERVICE_TOKEN", "")
    if len(expected) < 16 or not value or not secrets.compare_digest(value, expected):
        raise HTTPException(403, "Serviço não autorizado")


class PaymentIn(BaseModel):
    user_id: UUID
    course_id: UUID | None = None
    amount: int  # cents
    method: Literal["pix", "credito", "boleto"]
    kind: Literal["initial", "renewal"] = "initial"
    plan: Literal["one_time", "monthly"] = "one_time"


def _digest(body: BaseModel) -> str:
    return hashlib.sha256(json.dumps(body.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/payments/methods")
def methods() -> list[str]:
    return sorted(METHODS)


@app.post("/api/payments", status_code=201)
def create_payment(
    body: PaymentIn, response: Response,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    service_token: str | None = Header(default=None, alias="X-Service-Token"),
    db: Session = Depends(get_session),
) -> dict:
    """Creates a `pending` payment; the outcome arrives later (webhook or reconcile).
    Same Idempotency-Key + same body returns the same payment; different body -> 409."""
    require_service_token(service_token)
    if (body.plan == "one_time" and body.course_id is None) or (body.plan == "monthly" and body.course_id is not None) or (body.kind == "renewal" and body.plan != "monthly"):
        raise HTTPException(422, "Escopo de pagamento inválido")
    digest = _digest(body)
    p = db.scalar(select(Payment).where(Payment.idempotency_key == idempotency_key))
    if p is None:
        if body.method not in METHODS:
            raise HTTPException(400, f"unknown method, use one of {sorted(METHODS)}")
        if body.amount <= 0:
            raise HTTPException(400, "amount must be positive")
        p = Payment(idempotency_key=idempotency_key, request_hash=digest, status="pending",
                    user_id=body.user_id, item_id=body.course_id, amount=body.amount,
                    method=body.method, kind=body.kind, plan=body.plan)
        db.add(p)
        try:
            db.commit()
        except IntegrityError:  # concurrent request with the same key won the race
            db.rollback()
            p = db.scalar(select(Payment).where(Payment.idempotency_key == idempotency_key))
            response.status_code = 200
        if response.status_code != 200:
            response.status_code = 201
    else:
        response.status_code = 200
    if p.request_hash != digest:
        raise HTTPException(409, "Idempotency-Key was already used with a different request")
    if p.psp_charge_id is None:
        submit_to_psp(db, p)
    return p.view()


@app.get("/api/payments/{payment_id}")
def get_payment(payment_id: int, service_token: str | None = Header(default=None, alias="X-Service-Token"),
                db: Session = Depends(get_session)) -> dict:
    require_service_token(service_token)
    p = db.get(Payment, payment_id)
    if p is None:
        raise HTTPException(404, "payment not found")
    return p.view()


class PspEvent(BaseModel):
    event_id: str
    type: str
    charge_id: str


@app.post("/api/payments/webhooks/psp")
def psp_webhook(event: PspEvent, service_token: str | None = Header(default=None, alias="X-Webhook-Token"),
                db: Session = Depends(get_session)) -> dict:
    require_service_token(service_token)
    status = {"charge.succeeded": "paid", "charge.failed": "failed"}.get(event.type)
    if status is None:
        raise HTTPException(400, "unknown event type")
    p = db.scalar(select(Payment).where(Payment.psp_charge_id == event.charge_id))
    if p is None:  # may arrive before we stored the charge id; non-2xx makes the PSP retry
        raise HTTPException(404, "unknown charge")
    settle(db, p, status)
    return {"received": True}


def reconcile_now(min_age: float = 0, db: Session = Depends(get_session)) -> dict:
    return reconcile(db, min_age)


# ---- teacher payouts ---------------------------------------------------------------

def _settle_payouts(db: Session, payouts: list[Payout]) -> None:
    for payout in payouts:
        if payout.status == "paid":
            continue
        r = httpx.post(
            f"{PSP_URL}/v1/transfers", headers={"Idempotency-Key": f"payout-{payout.id}"}, timeout=5,
            json={"amount": payout.amount, "destination": str(payout.teacher_id)})
        r.raise_for_status()
        payout.psp_transfer_id = r.json()["id"]
        payout.status = "paid"
        db.commit()


def run_payouts(period: str, db: Session = Depends(get_session)) -> dict:
    """Pay teachers for a period (YYYY-MM): TEACHER_SHARE of the revenue paid in that period,
    split across items by watch time (Metering); each item's share goes to its owner.
    Idempotent: a period is computed once, re-running only finishes unsettled transfers."""
    try:
        start = datetime.strptime(period, "%Y-%m")
    except ValueError:
        raise HTTPException(400, "period must be YYYY-MM")
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)

    payouts = list(db.scalars(select(Payout).where(Payout.period == period)))
    revenue = db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(
        Payment.status == "paid", Payment.settled_at >= start, Payment.settled_at < end))
    if not payouts:
        try:
            usage = httpx.get(f"{METERING_URL}/api/usage/summary", timeout=5,
                              params={"from": start.isoformat(), "to": end.isoformat()}).json()["items"]
            owners = httpx.get(f"{CONTENT_URL}/api/items/owners", timeout=5).json()
        except (httpx.HTTPError, ValueError, KeyError) as e:
            raise HTTPException(502, f"upstream service error: {e}")
        watched = [(u["item_id"], u["seconds"], owners[str(u["item_id"])]) for u in usage if str(u["item_id"]) in owners]
        total, pool = sum(s for _, s, _ in watched), int(revenue * TEACHER_SHARE)
        if pool > 0 and total > 0:
            for item_id, seconds, teacher_id in watched:
                db.add(Payout(period=period, item_id=item_id, teacher_id=teacher_id, seconds=seconds,
                              amount=pool * seconds // total, status="due"))
            try:
                db.commit()
            except IntegrityError:  # concurrent run created them first
                db.rollback()
            payouts = list(db.scalars(select(Payout).where(Payout.period == period)))
    try:
        _settle_payouts(db, payouts)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"PSP transfer failed, re-run to retry: {e}")
    return {"period": period, "revenue": revenue, "teacher_pool": int(revenue * TEACHER_SHARE),
            "payouts": [p.view() for p in payouts]}


def list_payouts(period: str, db: Session = Depends(get_session)) -> list[dict]:
    return [p.view() for p in db.scalars(select(Payout).where(Payout.period == period))]
