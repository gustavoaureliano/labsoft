import os
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite://")

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app import db as database, main


@pytest.fixture
def api(tmp_path, monkeypatch):
    engine=create_engine(f"sqlite:///{tmp_path/'payment.db'}",connect_args={"check_same_thread":False})
    engine=engine.execution_options(schema_translate_map={"payment":None})
    database.Base.metadata.create_all(engine)
    monkeypatch.setattr(database,"engine",engine)
    monkeypatch.setattr(main,"engine",engine)
    for name in ["CHECKOUT_PAYMENT_TOKEN","SUBSCRIPTION_PAYMENT_TOKEN","PAYMENT_SUBSCRIPTION_TOKEN","PSP_WEBHOOK_TOKEN"]:
        monkeypatch.setenv(name, name+'-test-secret')
    monkeypatch.setattr(main,"PSP_URL","http://psp")
    monkeypatch.setattr(main,"SUBSCRIPTION_URL","http://subscription")
    notifications=[]

    def post(url,**kwargs):
        if url.startswith('http://psp'):
            assert kwargs['headers']['Idempotency-Key'].startswith('payment-')
            return httpx.Response(201,json={'id':'ch_test'},request=httpx.Request('POST',url))
        assert kwargs['headers']['X-Service-Token']==os.environ['PAYMENT_SUBSCRIPTION_TOKEN']
        notifications.append(kwargs['json'])
        return httpx.Response(200,json={'status':'applied'},request=httpx.Request('POST',url))

    monkeypatch.setattr(main.httpx,'post',post)
    def session():
        with Session(engine) as db:yield db
    main.app.dependency_overrides[database.get_session]=session
    try:
        with TestClient(main.app) as client:
            yield client, engine, notifications
    finally:
        main.app.dependency_overrides.clear()
        engine.dispose()


def payload(plan='one_time',kind='initial',amount=1250):
    return {'user_id':str(uuid4()),'course_id':str(uuid4()) if plan=='one_time' else None,
            'amount':amount,'method':'pix','kind':kind,'plan':plan}


def token(name='CHECKOUT_PAYMENT_TOKEN'):
    return {'X-Service-Token':os.environ[name],'Idempotency-Key':'checkout-test-123'}


def test_payment_requires_scoped_service_credential(api):
    client, engine, _=api
    body=payload()
    for headers in ({'Idempotency-Key':'checkout-test-123'},{'X-Service-Token':'wrong','Idempotency-Key':'checkout-test-123'},
                    token('SUBSCRIPTION_PAYMENT_TOKEN')):
        assert client.post('/api/payments',json=body,headers=headers).status_code==403
    with Session(engine) as db:assert list(db.scalars(select(main.Payment)))==[]
    assert client.get('/api/payments/1').status_code==403
    for path in ['/api/payments/reconcile','/api/payouts/run']:
        assert client.post(path).status_code in (404,405)


def test_idempotent_payment_and_authenticated_webhook(api):
    client, engine, notifications=api
    body=payload()
    first=client.post('/api/payments',json=body,headers=token())
    assert first.status_code==201,first.text
    payment_id=first.json()['id']
    assert first.json()['user_id']==body['user_id'] and first.json()['course_id']==body['course_id']
    replay=client.post('/api/payments',json=body,headers=token())
    assert replay.status_code==200 and replay.json()['id']==payment_id
    assert client.get(f'/api/payments/{payment_id}',headers=token()).json()['status']=='pending'
    webhook={'event_id':'evt_test','type':'charge.succeeded','charge_id':'ch_test'}
    assert client.post('/api/payments/webhooks/psp',json=webhook).status_code==403
    received=client.post('/api/payments/webhooks/psp',json=webhook,headers={'X-Webhook-Token':os.environ['PSP_WEBHOOK_TOKEN']})
    assert received.status_code==200
    assert client.post('/api/payments/webhooks/psp',json=webhook,headers={'X-Webhook-Token':os.environ['PSP_WEBHOOK_TOKEN']}).status_code==200
    assert len(notifications)==1 and notifications[0]['user_id']==body['user_id'] and notifications[0]['course_id']==body['course_id']
    assert client.get(f'/api/payments/{payment_id}',headers=token()).json()['status']=='paid'
    with Session(engine) as db:assert len(list(db.scalars(select(main.Payment))))==1


def test_different_request_same_key_is_rejected(api):
    client, _, _=api
    body=payload()
    client.post('/api/payments',json=body,headers=token()).raise_for_status()
    assert client.post('/api/payments',json={**body,'amount':1337},headers=token()).status_code==409


def test_subscription_renewal_only_with_own_credential(api):
    client, _, _=api
    body=payload(plan='monthly',kind='renewal',amount=4990)
    assert client.post('/api/payments',json=body,headers=token()).status_code==403
    assert client.post('/api/payments',json=body,headers=token('SUBSCRIPTION_PAYMENT_TOKEN')).status_code==201
    assert client.post('/api/payments',json={**body,'course_id':str(uuid4())},headers=token('SUBSCRIPTION_PAYMENT_TOKEN')).status_code==422
