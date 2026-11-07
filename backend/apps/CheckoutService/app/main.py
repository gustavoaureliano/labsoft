import hashlib
import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from .db import Base, get_session, init_db, utcnow

PAYMENT_URL = os.getenv("PAYMENT_URL", "http://localhost:8004")
SUBSCRIPTION_URL = os.getenv("SUBSCRIPTION_URL", "http://localhost:8003")


class Checkout(Base):
    """One row per purchase attempt, keyed by the client's Idempotency-Key. Persisting it first means a
    crash/retry resumes the same purchase instead of charging twice."""
    __tablename__ = "checkout"
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: uuid.uuid4().hex)
    idempotency_key: Mapped[str] = mapped_column(unique=True)
    request_hash: Mapped[str]
    user_id: Mapped[int]
    item_id: Mapped[int]
    amount: Mapped[int]
    method: Mapped[str]
    plan: Mapped[str]
    payment_id: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Servico de Compras", lifespan=lifespan)


class CheckoutIn(BaseModel):
    user_id: int
    item_id: int
    amount: int  # cents (per cycle for monthly)
    method: str = "pix"
    plan: Literal["one_time", "monthly"] = "one_time"


def _digest(body: BaseModel) -> str:
    return hashlib.sha256(json.dumps(body.model_dump(), sort_keys=True).encode()).hexdigest()


def view(c: Checkout) -> dict:
    """processing -> ok | payment_failed. Eventually consistent: 'ok' only once the subscription is
    actually active, since payment -> subscription happens asynchronously."""
    base = {"checkout_id": c.id, "payment_id": c.payment_id}
    if c.payment_id is None:
        return {**base, "status": "processing"}
    try:
        payment = httpx.get(f"{PAYMENT_URL}/api/payments/{c.payment_id}", timeout=5).json()
        if payment["status"] == "failed":
            return {**base, "status": "payment_failed"}
        if payment["status"] == "paid":
            sub = httpx.get(f"{SUBSCRIPTION_URL}/api/subscriptions/{c.user_id}/{c.item_id}", timeout=5).json()
            if sub["active"]:
                return {**base, "status": "ok"}
    except (httpx.HTTPError, ValueError, KeyError):
        pass
    return {**base, "status": "processing"}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/checkout")
def start_checkout(
    body: CheckoutIn, idempotency_key: str = Header(alias="Idempotency-Key"), db: Session = Depends(get_session),
) -> dict:
    """Start (or resume) a purchase. Same Idempotency-Key + same body returns the same checkout;
    different body -> 409. Poll GET /api/checkout/{id} for the outcome."""
    digest = _digest(body)
    c = db.scalar(select(Checkout).where(Checkout.idempotency_key == idempotency_key))
    if c is None:
        c = Checkout(idempotency_key=idempotency_key, request_hash=digest, **body.model_dump())
        db.add(c)
        try:
            db.commit()
        except IntegrityError:  # concurrent request with the same key won the race
            db.rollback()
            c = db.scalar(select(Checkout).where(Checkout.idempotency_key == idempotency_key))
    if c.request_hash != digest:
        raise HTTPException(409, "Idempotency-Key was already used with a different request")

    if c.payment_id is None:  # first attempt, or a previous attempt died before saving the payment id
        try:
            r = httpx.post(f"{PAYMENT_URL}/api/payments", headers={"Idempotency-Key": f"checkout-{c.id}"}, timeout=5, json={
                "user_id": c.user_id, "item_id": c.item_id, "amount": c.amount, "method": c.method,
                "kind": "initial", "plan": c.plan})
            if r.status_code == 400:
                raise HTTPException(400, r.json()["detail"])
            r.raise_for_status()
        except httpx.HTTPError:
            raise HTTPException(502, "payment service unavailable; retry with the same Idempotency-Key")
        c.payment_id = r.json()["id"]
        db.commit()
    return view(c)


@app.get("/api/checkout/{checkout_id}")
def get_checkout(checkout_id: str, db: Session = Depends(get_session)) -> dict:
    c = db.get(Checkout, checkout_id)
    if c is None:
        raise HTTPException(404, "checkout not found")
    return view(c)
