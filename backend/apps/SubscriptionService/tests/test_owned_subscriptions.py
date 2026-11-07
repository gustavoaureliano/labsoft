import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from app import db as database
from app.main import Subscription


def test_owned_listing_and_cancellation(api):
    with Session(api.engine) as db:
        db.add_all([Subscription(user_id=uid, item_id=api.course_id) for uid in [api.users['student-a'],api.users['student-b']]])
        db.commit()
    response = api.client.get('/api/subscriptions/me')
    assert response.headers['cache-control'] == 'private, no-store'
    assert response.headers['vary'] == 'Cookie, Authorization'
    result = response.json()
    assert result == {'user_id': str(api.users['student-a']),
                      'items':[{'course_id':str(api.course_id),'status':'active','price':0}],
                      'complete_plan':None}
    assert api.client.delete(f'/api/subscriptions/me/{api.course_id}').status_code == 204
    assert api.client.delete(f'/api/subscriptions/me/{api.course_id}').status_code == 204
    with Session(api.engine) as db:
        assert db.get(Subscription,(api.users['student-a'],api.course_id)).status == 'cancelled'
        assert db.get(Subscription,(api.users['student-b'],api.course_id)).status == 'active'
    assert api.client.get(f"/api/subscriptions/{api.users['student-b']}").status_code == 404


def test_payment_events_require_service_credential_and_billing_is_not_public(api):
    event={'payment_id':1,'user_id':str(api.users['student-a']),'course_id':str(api.course_id),
           'amount':1250,'method':'pix','kind':'initial','plan':'one_time','status':'paid'}
    assert api.client.post('/api/subscriptions/events/payment',json=event).status_code == 403
    assert api.client.post('/api/billing/run').status_code == 403


def test_runtime_does_not_create_tables(tmp_path, monkeypatch):
    engine = create_engine(f'sqlite:///{tmp_path}/empty.sqlite')
    monkeypatch.setattr(database, 'engine', engine)
    with pytest.raises(OperationalError): database.init_db()
    assert inspect(engine).get_table_names() == []
    engine.dispose()
