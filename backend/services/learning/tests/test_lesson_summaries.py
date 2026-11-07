from dataclasses import replace
from uuid import uuid4
from app.integrations import Course, DemoIntegrations, User, get_integrations
from app.learning.models import Lesson
from app.learning.router import summary_user
from app.main import app


def test_public_summary_does_not_expose_description_or_private_media(upload_context):
    client, sessions, _ = upload_context
    cid, lid = str(uuid4()),str(uuid4())
    integrations=DemoIntegrations()
    integrations.catalog={cid:Course(cid,'Curso público','owner','','Professor')}
    app.dependency_overrides[get_integrations]=lambda:integrations
    with sessions() as db:
        db.add(Lesson(id=lid,course_id=cid,title='Título público',description='Descrição restrita',position=1))
        db.commit()
    url=f'/api/learning/courses/{cid}/lesson-summaries'
    public=client.get(url)
    assert public.headers['cache-control'] == 'private, no-store'
    assert public.status_code==200
    assert public.json()['items'][0]['title']=='Título público'
    assert 'Descrição restrita' not in public.text
    assert 'media_id' not in public.text and 'content_url' not in public.text
    integrations.catalog[cid]=replace(integrations.catalog[cid],published=False)
    assert client.get(url).status_code==404
    app.dependency_overrides[summary_user]=lambda:User('owner','teacher','Professor')
    try:
        assert client.get(url).json()['items'][0]['description']=='Descrição restrita'
        app.dependency_overrides[summary_user]=lambda:User('other','teacher','Outro')
        assert client.get(url).status_code==404
    finally:
        app.dependency_overrides.pop(summary_user,None)
