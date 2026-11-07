import os
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite://")

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import auth, db as database, main


@pytest.fixture
def api(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'checkout.db'}", connect_args={"check_same_thread": False})
    engine = engine.execution_options(schema_translate_map={"checkout": None})
    database.Base.metadata.create_all(engine)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setenv("IDENTITY_URL", "http://identity")
    monkeypatch.setenv("CATALOG_URL", "http://catalog")
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://testserver")
    monkeypatch.setenv("CHECKOUT_PAYMENT_TOKEN", "checkout-to-payment")
    monkeypatch.setattr(main, "PAYMENT_URL", "http://payment")
    monkeypatch.setattr(main, "SUBSCRIPTION_URL", "http://subscription")
    users = {"alice": str(uuid4()), "bob": str(uuid4())}
    course_id = str(uuid4())
    state = {"price": "12.50", "status": "published", "access_type": "paid", "calls": [],
             "subscriptions":{"user_id":users["alice"],"items":[],"complete_plan":None}}
    original = httpx.Client

    def handler(req):
        assert "cookie" not in req.headers
        who = req.headers.get("authorization", "").removeprefix("Bearer ")
        if req.url.host == "identity":
            if who not in users: return httpx.Response(401)
            return httpx.Response(200, json={"id": users[who], "role": "student"})
        if req.url.host == "catalog" and str(course_id) in req.url.path:
            if state.get("unavailable"): return httpx.Response(503)
            return httpx.Response(200, json={"id": course_id, "status": state["status"],
                                              "access_type": state["access_type"], "price": state["price"]})
        return httpx.Response(404)

    monkeypatch.setattr(auth.httpx, "Client", lambda **kw: original(transport=httpx.MockTransport(handler), **kw))

    def payment(method, url, **kwargs):
        state["calls"].append((method, kwargs))
        assert kwargs["headers"]["X-Service-Token"] == "checkout-to-payment"
        if method == "POST":
            return httpx.Response(201, json={"id": 42}, request=httpx.Request("POST", url))
        return httpx.Response(200, json={"status": "paid"})

    def get(url, **kwargs):
        if url.startswith("http://subscription"):
            assert kwargs["headers"]["Authorization"] == "Bearer alice"
            return httpx.Response(200, json=state["subscriptions"],request=httpx.Request('GET',url))
        return payment("GET", url, **kwargs)

    monkeypatch.setattr(main.httpx, "post", lambda url, **kwargs: payment("POST", url, **kwargs))
    monkeypatch.setattr(main.httpx, "get", get)

    def session():
        with Session(engine) as db: yield db
    main.app.dependency_overrides[database.get_session] = session
    try:
        with TestClient(main.app) as client:
            client.headers["Authorization"] = "Bearer alice"
            yield client, engine, course_id, state, users
    finally:
        main.app.dependency_overrides.clear()
        engine.dispose()


def test_quote_is_trusted_and_plan_price_is_authoritative(api):
    client, _, course_id, _, _ = api
    individual = client.get("/api/checkout/quote", params={"course_id": course_id})
    assert individual.json()["amount_cents"] == 1250
    assert individual.headers["cache-control"] == "private, no-store"
    assert client.get("/api/checkout/quote", params={"plan":"monthly"}).json()["amount_cents"] == 4990
    assert client.get("/api/checkout/quote", params={"plan":"monthly","course_id":course_id}).status_code == 422
    del client.headers['Authorization']
    assert client.get('/api/checkout/quote',params={'plan':'monthly'}).json()['amount_cents']==4990
    assert client.get('/api/checkout/quote',params={'course_id':course_id}).json()['amount_cents']==1250
    assert client.post("/api/checkout",headers={"Idempotency-Key":"attempt-123"},json={"course_id":course_id,"amount":1}).status_code == 422


@pytest.mark.parametrize("field,value,status", [("status","draft",409),("access_type","free",409),
    ("price","NaN",503),("price","12.345",503),("price","0.00",503)])
def test_invalid_catalog_state_never_creates_checkout(api, field, value, status):
    client, engine, course_id, state, _ = api
    state[field] = value
    r = client.post("/api/checkout",headers={"Idempotency-Key":"attempt-123"},json={"course_id":course_id})
    assert r.status_code == status
    with Session(engine) as db: assert list(db.scalars(select(main.Checkout))) == []


def test_idempotent_request_does_not_charge_twice_and_is_private(api):
    client, engine, course_id, state, users = api
    headers={"Idempotency-Key":"attempt-123456"}
    body={"course_id":course_id,"method":"pix"}
    first=client.post("/api/checkout",headers=headers,json=body)
    assert first.status_code==200, first.text
    first_id=first.json()["checkout_id"]
    second=client.post("/api/checkout",headers=headers,json=body)
    assert second.json()["checkout_id"]==first_id
    assert len([call for call in state["calls"] if call[0]=="POST"])==1
    assert client.get(f"/api/checkout/{first_id}").status_code==200
    client.headers["Authorization"]="Bearer bob"
    assert client.get(f"/api/checkout/{first_id}").status_code==404
    assert client.post("/api/checkout",headers=headers,json=body).status_code==409


def test_price_snapshot_is_persisted_without_user_supplied_amount(api):
    client, engine, course_id, state, users=api
    client.post("/api/checkout", headers={"Idempotency-Key":"attempt-123"},json={"course_id":course_id})
    with Session(engine) as db:
        record=db.scalar(select(main.Checkout))
        assert record.amount==1250 and str(record.user_id)==users["alice"] and str(record.item_id)==course_id
    assert state['calls'][0][1]['json']['amount']==1250


def test_new_attempt_cannot_buy_existing_course_but_original_key_can_retry(api):
    client, engine, course_id, state, users=api
    body={'course_id':course_id}
    original=client.post('/api/checkout',headers={'Idempotency-Key':'original-123'},json=body)
    assert original.status_code==200
    state['subscriptions']['items']=[{'course_id':course_id,'status':'active','price':1250}]
    assert client.post('/api/checkout',headers={'Idempotency-Key':'new-attempt-123'},json=body).status_code==409
    assert client.post('/api/checkout',headers={'Idempotency-Key':'original-123'},json=body).json()['status']=='ok'
    with Session(engine) as db:assert len(list(db.scalars(select(main.Checkout))))==1


def test_cookie_write_requires_allowed_origin(api):
    client, engine, course_id, state, users=api
    del client.headers['Authorization']
    client.cookies.set('aprovaai_access','alice',path='/api')
    assert client.post('/api/checkout',headers={'Idempotency-Key':'attempt-123'},json={'course_id':course_id}).status_code==403
    assert client.post('/api/checkout',headers={'Idempotency-Key':'attempt-123','Origin':'http://testserver'},json={'course_id':course_id}).status_code==200


def test_dependency_outage_fails_before_persisting(api):
    client, engine, course_id, state, _=api
    state['unavailable']=True
    assert client.post('/api/checkout',headers={'Idempotency-Key':'attempt-123'},json={'course_id':course_id}).status_code==503
    with Session(engine) as db: assert list(db.scalars(select(main.Checkout)))==[]
