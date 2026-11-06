import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import httpx
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from .db import Base, get_session, init_db, utcnow

PAYMENT_URL = os.getenv("PAYMENT_URL", "http://localhost:8004")
BILLING_PERIOD_DAYS = int(os.getenv("BILLING_PERIOD_DAYS", "30"))


class Subscription(Base):
    __tablename__ = "subscription"
    user_id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(primary_key=True)
    plan: Mapped[str] = mapped_column(default="one_time")  # one_time | monthly
    price: Mapped[int] = mapped_column(default=0)  # cents per cycle
    method: Mapped[str] = mapped_column(default="pix")  # payment method used for renewals
    status: Mapped[str] = mapped_column(default="active")  # active | past_due | cancelled
    next_billing_at: Mapped[datetime | None]
    attempt: Mapped[int] = mapped_column(default=0)  # failed renewals in the current cycle

    def view(self) -> dict:
        return {"item_id": self.item_id, "plan": self.plan, "price": self.price, "status": self.status,
                "next_billing_at": self.next_billing_at.isoformat() if self.next_billing_at else None}


class ProcessedPayment(Base):
    """Dedup table: payment events are delivered at-least-once, applied exactly once."""
    __tablename__ = "processed_payment"
    payment_id: Mapped[int] = mapped_column(primary_key=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Servico de Inscricoes", lifespan=lifespan)


class SubscriptionIn(BaseModel):
    user_id: int
    item_id: int


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/subscriptions", status_code=201)
def create_free_subscription(body: SubscriptionIn, db: Session = Depends(get_session)) -> dict:
    """Free enrollment (no payment). Idempotent. Paid access arrives via payment events instead."""
    sub = db.get(Subscription, (body.user_id, body.item_id))
    if sub is None:
        db.add(Subscription(user_id=body.user_id, item_id=body.item_id))
    elif sub.status != "active":
        sub.status = "active"
    db.commit()
    return {"user_id": body.user_id, "item_id": body.item_id, "active": True}


class PaymentEvent(BaseModel):
    payment_id: int
    user_id: int
    item_id: int
    amount: int
    method: str
    kind: str  # initial | renewal
    plan: str  # one_time | monthly
    status: str  # paid | failed


@app.post("/api/subscriptions/events/payment")
def payment_event(ev: PaymentEvent, db: Session = Depends(get_session)) -> dict:
    """Payment outcome -> subscription state. Idempotent by payment_id."""
    if db.get(ProcessedPayment, ev.payment_id):
        return {"status": "duplicate"}
    db.add(ProcessedPayment(payment_id=ev.payment_id))
    sub = db.get(Subscription, (ev.user_id, ev.item_id))
    now = utcnow()
    period = timedelta(days=BILLING_PERIOD_DAYS)
    if ev.status == "paid":
        if ev.kind == "initial" or sub is None:
            if sub is None:
                sub = Subscription(user_id=ev.user_id, item_id=ev.item_id)
                db.add(sub)
            sub.plan, sub.price, sub.method = ev.plan, ev.amount, ev.method
            sub.status, sub.attempt = "active", 0
            sub.next_billing_at = now + period if ev.plan == "monthly" else None
        elif sub.status != "cancelled":  # successful renewal
            sub.status, sub.attempt = "active", 0
            sub.next_billing_at = (sub.next_billing_at or now) + period
    elif ev.kind == "renewal" and sub is not None and sub.status != "cancelled":
        sub.status = "past_due"
        sub.attempt += 1
    try:
        db.commit()
    except IntegrityError:  # same event processed concurrently
        db.rollback()
        return {"status": "duplicate"}
    return {"status": "applied"}


@app.post("/api/billing/run")
def run_billing(as_of: datetime | None = None, db: Session = Depends(get_session)) -> dict:
    """Create renewal charges for monthly subscriptions that are due (active, or past_due = retry).
    Run it from cron. Safe to run repeatedly: the idempotency key is derived from the billing cycle
    and attempt, so Payment returns the existing charge instead of creating a second one.
    `as_of` lets you simulate a later date."""
    now = as_of.replace(tzinfo=None) if as_of else utcnow()
    due = db.scalars(select(Subscription).where(
        Subscription.plan == "monthly", Subscription.status.in_(["active", "past_due"]),
        Subscription.next_billing_at <= now)).all()
    charged, errors = [], 0
    for s in due:
        key = f"renewal-{s.user_id}-{s.item_id}-{s.next_billing_at.date().isoformat()}-{s.attempt}"
        try:
            r = httpx.post(f"{PAYMENT_URL}/api/payments", headers={"Idempotency-Key": key}, timeout=5, json={
                "user_id": s.user_id, "item_id": s.item_id, "amount": s.price, "method": s.method,
                "kind": "renewal", "plan": "monthly"})
            r.raise_for_status()
            charged.append({"user_id": s.user_id, "item_id": s.item_id, "payment_id": r.json()["id"],
                            "status": r.json()["status"]})
        except httpx.HTTPError:
            errors += 1
    return {"as_of": now.isoformat(), "charged": charged, "errors": errors}


@app.get("/api/subscriptions/{user_id}")
def list_subscriptions(user_id: int, db: Session = Depends(get_session)) -> dict:
    """`item_ids` = items the user can access right now (active only); `items` has full detail."""
    subs = db.scalars(select(Subscription).where(Subscription.user_id == user_id)).all()
    return {"user_id": user_id, "item_ids": sorted(s.item_id for s in subs if s.status == "active"),
            "items": [s.view() for s in subs]}


@app.get("/api/subscriptions/{user_id}/{item_id}")
def get_subscription(user_id: int, item_id: int, db: Session = Depends(get_session)) -> dict:
    sub = db.get(Subscription, (user_id, item_id))
    return {"user_id": user_id, "item_id": item_id, "active": sub is not None and sub.status == "active",
            "status": sub.status if sub else None}


@app.delete("/api/subscriptions/{user_id}/{item_id}", status_code=204)
def cancel_subscription(user_id: int, item_id: int, db: Session = Depends(get_session)) -> None:
    """Cancel: access ends and no more renewals are billed. Idempotent."""
    sub = db.get(Subscription, (user_id, item_id))
    if sub is not None and sub.status != "cancelled":
        sub.status, sub.next_billing_at = "cancelled", None
        db.commit()
