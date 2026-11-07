from uuid import uuid4
import httpx
import pytest
from fastapi.testclient import TestClient
from app import main


@pytest.fixture
def api(monkeypatch):
    uid, cid = str(uuid4()), str(uuid4())
    state = {'user_id':uid,'items':[{'course_id':cid,'status':'active'}]}
    calls = []
    original = httpx.AsyncClient
    def handle(request):
        calls.append(request)
        assert 'cookie' not in request.headers
        if request.headers['authorization'] != 'Bearer valid': return httpx.Response(401)
        if request.url.host == 'identity': return httpx.Response(200,json={'id':uid,'role':'student'})
        if state.get('http_status'): return httpx.Response(state['http_status'])
        return httpx.Response(200,json=state)
    monkeypatch.setenv('IDENTITY_URL','http://identity')
    monkeypatch.setenv('SUBSCRIPTION_URL','http://subscriptions')
    monkeypatch.setattr(main.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handle),**kw))
    with TestClient(main.app) as client:
        client.headers['Authorization']='Bearer valid'
        yield client, uid, cid, state, calls


def test_access_is_for_authenticated_user_and_canonical_course(api):
    client, uid, cid, _, calls = api
    r = client.get('/api/access',params={'course_id':cid})
    assert r.json() == {'user_id':uid,'course_id':cid,'allowed':True,'reason':'free_enrollment'}
    assert [c.url.path for c in calls] == ['/api/v1/auth/me','/api/subscriptions/me']


@pytest.mark.parametrize('status', ['cancelled','past_due'])
def test_inactive_enrollment_is_denied(api, status):
    client, _, cid, state, _ = api
    state['items'][0]['status']=status
    assert client.get('/api/access',params={'course_id':cid}).json()['allowed'] is False


def test_absent_course_grant_is_a_business_denial(api):
    client, _, _, _, _ = api
    r=client.get('/api/access',params={'course_id':str(uuid4())})
    assert r.status_code==200 and r.json()['allowed'] is False


def test_user_cannot_be_selected_in_query(api):
    client, _, cid, _, _=api
    assert client.get('/api/access',params={'course_id':cid,'user_id':str(uuid4())}).status_code==422
    assert client.get('/api/access',params={'course_id':'0'}).status_code==422


@pytest.mark.parametrize('status', [500,429,302])
def test_dependency_failure_is_not_access_false(api,status):
    client, _, cid, state, _=api
    state['http_status']=status
    assert client.get('/api/access',params={'course_id':cid}).status_code==503


def test_subscriptions_must_belong_to_authenticated_user(api):
    client, _, cid, state, _=api
    state['user_id']=str(uuid4())
    assert client.get('/api/access',params={'course_id':cid}).status_code==503


@pytest.mark.parametrize('value', ['Bearer invalid','Basic invalid',''])
def test_bad_header_does_not_fall_back_to_cookie(api,value):
    client, _, cid, _, _=api
    client.cookies.set('aprovaai_access','valid',path='/api')
    client.headers['Authorization']=value
    assert client.get('/api/access',params={'course_id':cid}).status_code==401
