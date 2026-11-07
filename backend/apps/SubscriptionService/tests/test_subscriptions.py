from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.main import Subscription


def enroll(api, **extra):
    return api.client.post("/api/subscriptions", json={"course_id": str(api.course_id), **extra})


def test_enrollment_uses_identity_and_is_idempotent(api):
    first, second = enroll(api), enroll(api)
    assert (first.status_code,second.status_code) == (201,200)
    assert first.json() == {'user_id':str(api.users['student-a']),'course_id':str(api.course_id),'active':True}
    with Session(api.engine) as db:
        rows = list(db.scalars(select(Subscription)))
        assert len(rows) == 1 and rows[0].price == 0 and rows[0].user_id == api.users['student-a']
    assert api.calls[-1].headers['authorization'] == 'Bearer student-a'


@pytest.mark.parametrize('extra', [{'user_id':str(uuid4())},{'item_id':1},{'price':0},{'status':'active'}])
def test_enrollment_rejects_client_identity_price_or_state(api, extra):
    assert enroll(api, **extra).status_code == 422


@pytest.mark.parametrize('field,value', [('access_type','paid'),('price','12.50'),('status','draft'),('status','archived')])
def test_enrollment_requires_published_free_course(api, field, value):
    api.state[field] = value
    assert enroll(api).status_code == 409
    with Session(api.engine) as db: assert list(db.scalars(select(Subscription))) == []


@pytest.mark.parametrize('status,expected', [(404,404),(500,503),(302,503),(429,503)])
def test_catalog_failure_never_grants_access(api, status, expected):
    api.state['http_status'] = status
    assert enroll(api).status_code == expected
    with Session(api.engine) as db: assert list(db.scalars(select(Subscription))) == []


def test_course_response_must_match_requested_id(api):
    api.state['id'] = str(uuid4())
    assert enroll(api).status_code == 503


def test_cancelled_enrollment_is_not_silently_reactivated(api):
    assert enroll(api).status_code == 201
    api.client.delete(f'/api/subscriptions/me/{api.course_id}')
    assert enroll(api).status_code == 409
    assert api.client.get(f'/api/subscriptions/me/{api.course_id}').json()['status'] == 'cancelled'


@pytest.mark.parametrize('value,expected', [('invalid',401),('teacher',403)])
def test_invalid_or_nonstudent_identity_cannot_enroll(api, value, expected):
    api.client.headers['Authorization'] = f'Bearer {value}'
    api.client.cookies.set('aprovaai_access','student-a',path='/api')
    assert enroll(api).status_code == expected


@pytest.mark.parametrize('origin', [None,'null','https://untrusted.example'])
def test_cookie_write_requires_origin(api, origin):
    del api.client.headers['Authorization']
    api.client.cookies.set('aprovaai_access','student-a',path='/api')
    response = api.client.post('/api/subscriptions',json={'course_id':str(api.course_id)},headers={} if origin is None else {'Origin':origin})
    assert response.status_code == 403


def test_anonymous_demo_headers_do_not_authenticate(api):
    del api.client.headers['Authorization']
    api.client.headers['X-Demo-User'] = 'aluno-demo'
    assert enroll(api).status_code == 401
