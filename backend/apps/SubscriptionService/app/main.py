import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
from typing import Literal

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from .db import Base, get_session, init_db, utcnow
from .auth import remote, student

PAYMENT_URL = os.getenv("PAYMENT_URL", "http://localhost:8004")
BILLING_PERIOD_DAYS = int(os.getenv("BILLING_PERIOD_DAYS", "30"))


class Subscription(Base):
    __tablename__ = "subscription"
    user_id: Mapped[UUID] = mapped_column(primary_key=True)
    item_id: Mapped[UUID] = mapped_column(primary_key=True)
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


class CompletePlan(Base):
    __tablename__ = "complete_plan"
    user_id: Mapped[UUID] = mapped_column(primary_key=True)
    price: Mapped[int] = mapped_column(default=4990)
    method: Mapped[str] = mapped_column(default="pix")
    status: Mapped[str] = mapped_column(default="active")
    next_billing_at: Mapped[datetime | None]
    attempt: Mapped[int] = mapped_column(default=0)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Servico de Inscricoes", lifespan=lifespan)


@app.middleware("http")
async def private_responses(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers.setdefault("Vary", "Cookie, Authorization")
    return response


class SubscriptionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    course_id: UUID


class CourseLookup(BaseModel):
    id: UUID
    status: str
    access_type: str
    price: Decimal | None


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/subscriptions", status_code=201)
def create_free_subscription(body: SubscriptionIn, request: Request, response: Response, db: Session = Depends(get_session)) -> dict:
    """Create only the authenticated student's validated free enrollment."""
    user_id, access = student(request)
    try:
        course = CourseLookup.model_validate(remote("CATALOG_URL", f"/api/courses/{body.course_id}/summary", access))
    except ValueError as exc:
        raise HTTPException(503, "Resposta de curso inválida") from exc
    if course.id != body.course_id:
        raise HTTPException(503, "Curso divergente")
    if course.status != "published" or course.access_type != "free" or course.price not in (None, Decimal(0)):
        raise HTTPException(409, "Matrícula gratuita exige curso publicado e gratuito")
    key = (user_id, body.course_id)
    sub = db.get(Subscription, key)
    if sub is None:
        db.add(Subscription(user_id=user_id, item_id=body.course_id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            sub = db.get(Subscription, key)
            if sub is None:
                raise
            if sub.status != "active":
                raise HTTPException(409, "Matrícula inativa não pode ser reativada automaticamente")
            response.status_code = 200
    else:
        if sub.status != "active":
            raise HTTPException(409, "Matrícula inativa não pode ser reativada automaticamente")
        response.status_code = 200
    return {"user_id": str(user_id), "course_id": str(body.course_id), "active": True}


class PaymentEvent(BaseModel):
    payment_id: int
    user_id: UUID
    course_id: UUID | None = None
    amount: int
    method: str
    kind: Literal["initial", "renewal"]
    plan: Literal["one_time", "monthly"]
    status: Literal["paid", "failed"]


@app.post("/api/subscriptions/events/payment")
def payment_event(ev: PaymentEvent,
                  service_token: str | None = Header(default=None, alias="X-Service-Token"),
                  db: Session = Depends(get_session)) -> dict:
    """Payment outcome -> subscription state. Idempotent by payment_id."""
    expected = os.getenv("PAYMENT_SUBSCRIPTION_TOKEN", "")
    if len(expected) < 16 or not service_token or not secrets.compare_digest(service_token, expected):
        raise HTTPException(403, "Serviço não autorizado")
    if (ev.plan == "monthly" and ev.course_id is not None) or (ev.plan == "one_time" and ev.course_id is None):
        raise HTTPException(422, "Escopo de pagamento inválido")
    if ev.plan == "monthly" and ev.amount != 4990:
        raise HTTPException(422, "Preço do plano divergente")
    if ev.kind == "renewal" and (ev.plan != "monthly" or ev.amount <= 0):
        raise HTTPException(422, "Renovação inválida")
    if db.get(ProcessedPayment, ev.payment_id):
        return {"status": "duplicate"}
    db.add(ProcessedPayment(payment_id=ev.payment_id))
    sub = db.get(CompletePlan, ev.user_id) if ev.plan == "monthly" else db.get(Subscription, (ev.user_id, ev.course_id))
    if ev.kind == "renewal" and (sub is None or sub.status == "cancelled"):
        raise HTTPException(409, "Assinatura não renovável")
    now = utcnow()
    period = timedelta(days=BILLING_PERIOD_DAYS)
    if ev.status == "paid":
        if ev.kind == "initial" or sub is None:
            if sub is None:
                sub = CompletePlan(user_id=ev.user_id) if ev.plan == "monthly" else Subscription(user_id=ev.user_id, item_id=ev.course_id)
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
def run_billing(as_of: datetime | None = None,
                service_token: str | None = Header(default=None, alias="X-Service-Token"),
                db: Session = Depends(get_session)) -> dict:
    """Create renewal charges for monthly subscriptions that are due (active, or past_due = retry).
    Run it from cron. Safe to run repeatedly: the idempotency key is derived from the billing cycle
    and attempt, so Payment returns the existing charge instead of creating a second one.
    `as_of` lets you simulate a later date."""
    expected = os.getenv("BILLING_JOB_TOKEN", "")
    if len(expected) < 16 or not service_token or not secrets.compare_digest(service_token, expected):
        raise HTTPException(403, "Agendamento não autorizado")
    now = as_of.replace(tzinfo=None) if as_of else utcnow()
    due = db.scalars(select(CompletePlan).where(
        CompletePlan.status.in_(["active", "past_due"]),
        CompletePlan.next_billing_at <= now)).all()
    charged, errors = [], 0
    payment_token = os.getenv("SUBSCRIPTION_PAYMENT_TOKEN", "")
    if len(payment_token) < 16:
        raise HTTPException(503, "Pagamento de renovação não configurado")
    for s in due:
        key = f"renewal-{s.user_id}-{s.next_billing_at.date().isoformat()}-{s.attempt}"
        try:
            r = httpx.post(f"{PAYMENT_URL}/api/payments", headers={"Idempotency-Key": key,
                "X-Service-Token": payment_token}, timeout=5, json={
                "user_id": str(s.user_id), "course_id": None, "amount": s.price, "method": s.method,
                "kind": "renewal", "plan": "monthly"})
            r.raise_for_status()
            charged.append({"user_id": str(s.user_id), "payment_id": r.json()["id"],
                            "status": r.json()["status"]})
        except httpx.HTTPError:
            errors += 1
    return {"as_of": now.isoformat(), "charged": charged, "errors": errors}


@app.get("/api/subscriptions/me")
def list_subscriptions(request: Request, db: Session = Depends(get_session)) -> dict:
    user_id, _ = student(request)
    subs = db.scalars(select(Subscription).where(Subscription.user_id == user_id)).all()
    complete = db.get(CompletePlan, user_id)
    return {"user_id": str(user_id), "items": [
        {"course_id": str(s.item_id), "status": s.status, "price": s.price} for s in subs
    ], "complete_plan": {"status": complete.status, "price": complete.price,
                          "next_billing_at": complete.next_billing_at.isoformat() if complete.next_billing_at else None} if complete else None}


@app.delete("/api/subscriptions/me/complete-plan", status_code=204)
def cancel_complete_plan(request: Request, db: Session = Depends(get_session)) -> Response:
    user_id, _ = student(request)
    plan = db.get(CompletePlan, user_id)
    if plan is not None and plan.status != "cancelled":
        plan.status = "cancelled"
        plan.next_billing_at = None
        db.commit()
    return Response(status_code=204)


@app.get("/api/subscriptions/me/{course_id}")
def get_subscription(course_id: UUID, request: Request, db: Session = Depends(get_session)) -> dict:
    user_id, _ = student(request)
    sub = db.get(Subscription, (user_id, course_id))
    return {"user_id": str(user_id), "course_id": str(course_id), "active": sub is not None and sub.status == "active",
            "status": sub.status if sub else None}


@app.delete("/api/subscriptions/me/{course_id}", status_code=204)
def cancel_subscription(course_id: UUID, request: Request, db: Session = Depends(get_session)) -> None:
    """Cancel: access ends and no more renewals are billed. Idempotent."""
    user_id, _ = student(request)
    sub = db.get(Subscription, (user_id, course_id))
    if sub is not None and sub.status != "cancelled":
        if sub.price > 0:
            raise HTTPException(409, "Compra individual não é cancelável por esta rota")
        sub.status, sub.next_billing_at = "cancelled", None
        db.commit()
