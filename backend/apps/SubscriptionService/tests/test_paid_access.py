import pytest
import httpx
from app import main
from sqlalchemy.orm import Session
from app.main import CompletePlan, Subscription


@pytest.fixture
def paid(api, monkeypatch):
    monkeypatch.setenv('PAYMENT_SUBSCRIPTION_TOKEN','payment-to-subscription-secret')
    client=api.client
    headers={'X-Service-Token':'payment-to-subscription-secret'}
    def event(payment_id, *, plan='monthly', status='paid', kind='initial', user=None):
        return {'payment_id':payment_id,'user_id':str(user or api.users['student-a']),
                'course_id':str(api.course_id) if plan=='one_time' else None,
                'amount':4990 if plan=='monthly' else 1250, 'method':'pix',
                'kind':kind,'plan':plan,'status':status}
    return api, client, headers, event


def test_plan_is_separate_from_individual_purchase_and_cancellation(paid):
    api, client, headers, event=paid
    assert client.post('/api/subscriptions/events/payment',json=event(1,plan='one_time'),headers=headers).json()['status']=='applied'
    assert client.post('/api/subscriptions/events/payment',json=event(2),headers=headers).json()['status']=='applied'
    assert client.post('/api/subscriptions/events/payment',json=event(2),headers=headers).json()['status']=='duplicate'
    before=client.get('/api/subscriptions/me').json()
    assert before['complete_plan']['status']=='active' and before['complete_plan']['price']==4990
    assert before['items'][0]['status']=='active' and before['items'][0]['price']==1250
    assert client.delete('/api/subscriptions/me/complete-plan').status_code==204
    assert client.get('/api/subscriptions/me').json()['complete_plan']['status']=='cancelled'
    assert client.get(f'/api/subscriptions/me/{api.course_id}').json()['active'] is True
    assert client.delete(f'/api/subscriptions/me/{api.course_id}').status_code==409
    with Session(api.engine) as db:
        assert db.get(Subscription,(api.users['student-a'],api.course_id)).status=='active'
        assert db.get(CompletePlan,api.users['student-a']).status=='cancelled'


def test_past_due_and_cancelled_plan_do_not_grant_plan_access(paid):
    api, client, headers, event=paid
    client.post('/api/subscriptions/events/payment',json=event(1),headers=headers).raise_for_status()
    failed=client.post('/api/subscriptions/events/payment',json=event(2,status='failed',kind='renewal'),headers=headers)
    assert failed.status_code==200
    assert client.get('/api/subscriptions/me').json()['complete_plan']['status']=='past_due'
    client.delete('/api/subscriptions/me/complete-plan').raise_for_status()
    assert client.post('/api/subscriptions/events/payment',json=event(3,kind='renewal'),headers=headers).status_code==409
    assert client.get('/api/subscriptions/me').json()['complete_plan']['status']=='cancelled'


def test_fake_price_and_missing_service_token_cannot_grant_plan(paid):
    api, client, headers, event=paid
    assert client.post('/api/subscriptions/events/payment',json=event(1)).status_code==403
    assert client.post('/api/subscriptions/events/payment',json={**event(1),'amount':1},headers=headers).status_code==422
    assert client.post('/api/subscriptions/events/payment',json={**event(1),'course_id':str(api.course_id)},headers=headers).status_code==422
    assert client.get('/api/subscriptions/me').json()['complete_plan'] is None


def test_due_plan_renews_with_internal_credential_and_stable_key(paid, monkeypatch):
    api, client, headers, event=paid
    monkeypatch.setenv('BILLING_JOB_TOKEN','scheduler-only-long-secret')
    monkeypatch.setenv('SUBSCRIPTION_PAYMENT_TOKEN','renewal-payment-long-secret')
    client.post('/api/subscriptions/events/payment',json=event(1),headers=headers).raise_for_status()
    submitted=[]
    def payment(url, **kwargs):
        submitted.append(kwargs)
        assert kwargs['headers']['X-Service-Token']=='renewal-payment-long-secret'
        assert kwargs['json']['course_id'] is None and kwargs['json']['amount']==4990
        return httpx.Response(201,json={'id':42,'status':'pending'},request=httpx.Request('POST',url))
    monkeypatch.setattr(main.httpx,'post',payment)
    plan=client.get('/api/subscriptions/me').json()['complete_plan']
    assert client.post('/api/billing/run',params={'as_of':plan['next_billing_at']}).status_code==403
    auth={'X-Service-Token':'scheduler-only-long-secret'}
    first=client.post('/api/billing/run',params={'as_of':plan['next_billing_at']},headers=auth)
    second=client.post('/api/billing/run',params={'as_of':plan['next_billing_at']},headers=auth)
    assert first.status_code==second.status_code==200
    assert first.json()['charged'][0]['payment_id']==42
    assert submitted[0]['headers']['Idempotency-Key']==submitted[1]['headers']['Idempotency-Key']
