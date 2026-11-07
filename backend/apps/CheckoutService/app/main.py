import hashlib
import json
import os
import uuid
from decimal import Decimal, InvalidOperation
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from .db import Base, get_session, init_db, utcnow
from .auth import Course, read, student

PAYMENT_URL = os.getenv("PAYMENT_URL", "http://localhost:8004")
SUBSCRIPTION_URL = os.getenv("SUBSCRIPTION_URL", "http://localhost:8003")


class Checkout(Base):
    """One row per purchase attempt, keyed by the client's Idempotency-Key. Persisting it first means a
    crash/retry resumes the same purchase instead of charging twice."""
    __tablename__ = "checkout"
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: uuid.uuid4().hex)
    idempotency_key: Mapped[str] = mapped_column(unique=True)
    request_hash: Mapped[str]
    user_id: Mapped[uuid.UUID]
    item_id: Mapped[uuid.UUID | None]
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


@app.middleware("http")
async def private_responses(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers.setdefault("Vary", "Cookie, Authorization")
    return response


class CheckoutIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    course_id: uuid.UUID | None = None
    method: Literal["pix", "credito", "boleto"] = "pix"
    plan: Literal["one_time", "monthly"] = "one_time"


PLAN_MONTHLY_CENTS = 4990


def quote(body: CheckoutIn, access: str | None) -> int:
    if body.plan == "monthly":
        if body.course_id is not None:
            raise HTTPException(422, "Assinatura completa não aceita course_id")
        return PLAN_MONTHLY_CENTS
    if body.course_id is None:
        raise HTTPException(422, "Compra individual exige course_id")
    course = read("CATALOG_URL", f"/api/courses/{body.course_id}/summary", access, Course)
    if course.id != body.course_id:
        raise HTTPException(503, "Curso divergente")
    if course.status != "published" or course.access_type != "paid" or course.price is None:
        raise HTTPException(409, "Compra exige curso pago e publicado")
    try:
        price = Decimal(course.price)
        cents = price * 100
        if not cents.is_finite() or cents != cents.to_integral_value() or cents <= 0:
            raise ValueError("Preço inválido")
        return int(cents)
    except (InvalidOperation, ValueError) as exc:
        raise HTTPException(503, "Preço do catálogo inválido") from exc


def _digest(body: BaseModel) -> str:
    return hashlib.sha256(json.dumps(body.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()


def view(c: Checkout, access_token: str) -> dict:
    """processing -> ok | payment_failed. Eventually consistent: 'ok' only once the subscription is
    actually active, since payment -> subscription happens asynchronously."""
    base = {"checkout_id": c.id, "payment_id": c.payment_id}
    if c.payment_id is None:
        return {**base, "status": "processing"}
    try:
        key = os.getenv("CHECKOUT_PAYMENT_TOKEN", "")
        if not key: return {**base, "status": "processing"}
        payment = httpx.get(f"{PAYMENT_URL}/api/payments/{c.payment_id}", timeout=5, headers={"X-Service-Token": key}).json()
        if payment["status"] == "failed":
            return {**base, "status": "payment_failed"}
        if payment["status"] == "paid":
            sub = httpx.get(f"{SUBSCRIPTION_URL}/api/subscriptions/me", timeout=5,
                            headers={"Authorization": f"Bearer {access_token}"}).json()
            if sub["user_id"] != str(c.user_id):
                return {**base, "status": "processing"}
            if c.plan == "monthly":
                active = (sub.get("complete_plan") or {}).get("status") == "active"
            else:
                active = any(item["course_id"] == str(c.item_id) and item["status"] == "active"
                             for item in sub["items"])
            if active:
                return {**base, "status": "ok"}
    except (httpx.HTTPError, ValueError, KeyError):
        pass
    return {**base, "status": "processing"}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/checkout/quote")
def price_quote(request: Request, plan: Literal["one_time", "monthly"] = "one_time",
                course_id: uuid.UUID | None = None) -> dict:
    amount = quote(CheckoutIn(plan=plan, course_id=course_id), None)
    return {"plan": plan, "course_id": str(course_id) if course_id else None, "amount_cents": amount}


@app.post("/api/checkout")
def start_checkout(
    body: CheckoutIn, request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=128), db: Session = Depends(get_session),
) -> dict:
    """Start (or resume) a purchase. Same Idempotency-Key + same body returns the same checkout;
    different body -> 409. Poll GET /api/checkout/{id} for the outcome."""
    user_id, access = student(request)
    amount = quote(body, access)
    key = os.getenv("CHECKOUT_PAYMENT_TOKEN", "")
    if not key:
        raise HTTPException(503, "Pagamento interno não configurado")
    digest = hashlib.sha256(f"{user_id}:{amount}:{_digest(body)}".encode()).hexdigest()
    c = db.scalar(select(Checkout).where(Checkout.idempotency_key == idempotency_key))
    if c is None:
        try:
            subscriptions = httpx.get(f"{SUBSCRIPTION_URL}/api/subscriptions/me", timeout=5,
                                      headers={"Authorization": f"Bearer {access}"})
            subscriptions.raise_for_status()
            grants = subscriptions.json()
            if grants["user_id"] != str(user_id):
                raise HTTPException(503, "Matrículas de outro usuário")
            if body.plan == "monthly":
                acquired = (grants.get("complete_plan") or {}).get("status") == "active"
            else:
                acquired = any(item["course_id"] == str(body.course_id) and item["status"] == "active"
                               for item in grants["items"])
            if acquired:
                raise HTTPException(409, "Você já possui acesso por esta compra ou matrícula")
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise HTTPException(503, "Não foi possível consultar aquisições existentes") from exc
        c = Checkout(idempotency_key=idempotency_key, request_hash=digest, user_id=user_id,
                     item_id=body.course_id, amount=amount, method=body.method, plan=body.plan)
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
            r = httpx.post(f"{PAYMENT_URL}/api/payments", headers={"Idempotency-Key": f"checkout-{c.id}", "X-Service-Token": key}, timeout=5, json={
                "user_id": str(c.user_id), "course_id": str(c.item_id) if c.item_id else None,
                "amount": c.amount, "method": c.method,
                "kind": "initial", "plan": c.plan})
            if r.status_code == 400:
                raise HTTPException(400, r.json()["detail"])
            r.raise_for_status()
        except httpx.HTTPError:
            raise HTTPException(502, "payment service unavailable; retry with the same Idempotency-Key")
        c.payment_id = r.json()["id"]
        db.commit()
    return view(c, access)


@app.get("/api/checkout/{checkout_id}")
def get_checkout(checkout_id: str, request: Request, db: Session = Depends(get_session)) -> dict:
    user_id, access = student(request)
    c = db.get(Checkout, checkout_id)
    if c is None or c.user_id != user_id:
        raise HTTPException(404, "checkout not found")
    return view(c, access)
