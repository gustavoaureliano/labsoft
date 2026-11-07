from uuid import uuid4
import pytest
from fastapi import HTTPException
from starlette.requests import Request
from app.catalog import CatalogIntegrations
from app.integrations import Course, User


@pytest.mark.parametrize('allowed', [True, False])
def test_access_response_is_used_without_inventing_status(allowed):
    uid, cid = str(uuid4()), str(uuid4())
    integrations = CatalogIntegrations(None)
    integrations.read = lambda *args, **kwargs: {'user_id':uid,'course_id':cid,'allowed':allowed,
        'reason':'free_enrollment' if allowed else 'no_active_enrollment'}
    assert integrations.has_access(uid,cid) is allowed
    assert integrations.access_status(uid,cid) == ('active' if allowed else 'none')


@pytest.mark.parametrize('field,value', [('user_id',str(uuid4())),('course_id',str(uuid4())),('allowed','true')])
def test_foreign_or_invalid_access_decision_fails_closed(field,value):
    uid,cid=str(uuid4()),str(uuid4())
    payload={'user_id':uid,'course_id':cid,'allowed':True,'reason':'free_enrollment',field:value}
    integrations=CatalogIntegrations(None)
    integrations.read=lambda *args,**kwargs:payload
    with pytest.raises(HTTPException) as exc:integrations.has_access(uid,cid)
    assert exc.value.status_code==503


def test_only_own_active_enrollments_are_composed():
    uid,active,cancelled=str(uuid4()),str(uuid4()),str(uuid4())
    request=Request({'type':'http','method':'GET','headers':[]})
    request.state.current_user=User(uid,'student','Aluno')
    integrations=CatalogIntegrations(request)
    payload={'user_id':uid,'items':[{'course_id':active,'status':'active'},{'course_id':cancelled,'status':'cancelled'}]}
    integrations.read=lambda *args,**kwargs:payload
    integrations.course=lambda cid:Course(cid,"Curso",uid,"","Professor")
    assert [course.id for course in integrations.courses()]==[active]
    payload['user_id']=str(uuid4())
    with pytest.raises(HTTPException) as exc:integrations.courses()
    assert exc.value.status_code==503


def test_complete_plan_composes_catalog_and_keeps_individual_grant():
    uid, first, second = str(uuid4()), str(uuid4()), str(uuid4())
    request=Request({'type':'http','method':'GET','headers':[]})
    request.state.current_user=User(uid,'student','Aluno')
    integrations=CatalogIntegrations(request)
    payload={'user_id':uid,'items':[{'course_id':first,'status':'active'}],
             'complete_plan':{'status':'active','price':4990}}
    def read(setting,path,**kwargs):
        if setting=='SUBSCRIPTION_URL': return payload
        return {'items':[{'id':second,'title':'Curso','teacher_id':uid,'teacher_name':'Professor','status':'published'}],
                'pagination':{'page':1,'pages':1}}
    integrations.read=read
    integrations.course=lambda cid:Course(cid,"Curso",uid,"","Professor")
    assert {row.id for row in integrations.courses()}=={first,second}
    payload['complete_plan']['status']='cancelled'
    assert [row.id for row in integrations.courses()]==[first]
