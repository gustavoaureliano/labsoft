from app.integrations import DemoIntegrations, User, get_current_user
from app.learning.models import Lesson
from app.main import app


def test_admin_hide_keep_and_logical_delete_preserve_lesson(upload_context, monkeypatch):
    client, sessions, _ = upload_context
    monkeypatch.setenv('ENGAGEMENT_LEARNING_TOKEN','engagement-learning-secret')
    course_id='fisica-quantica'
    lesson_id='moderated-lesson'
    with sessions() as session:
        session.add(Lesson(id=lesson_id,course_id=course_id,title='Histórico',position=1))
        session.commit()
    url=f'/api/learning/lessons/{lesson_id}/moderation'
    assert client.put(url,json={'decision':'hide'}).status_code==403
    app.dependency_overrides[get_current_user]=lambda:User('admin-demo','admin','Admin')
    assert client.put(url,json={'decision':'hide'}).status_code==403
    client.headers['X-Service-Token']='engagement-learning-secret'
    assert client.put(url,json={'decision':'hide'}).json()['moderation_status']=='hidden'
    app.dependency_overrides[get_current_user]=lambda:DemoIntegrations.users['aluno-demo']
    assert client.get(f'/api/learning/lessons/{lesson_id}/summary').status_code==403
    assert client.get(f'/api/learning/lessons/{lesson_id}/playback').status_code==403
    assert all(row['id']!=lesson_id for row in client.get(f'/api/learning/courses/{course_id}').json()['lessons'])
    app.dependency_overrides[get_current_user]=lambda:User('admin-demo','admin','Admin')
    assert client.put(url,json={'decision':'keep'}).json()['moderation_status']=='visible'
    assert client.put(url,json={'decision':'delete'}).json()['moderation_status']=='deleted'
    assert client.put(url,json={'decision':'keep'}).status_code==409
    with sessions() as session:
        assert session.get(Lesson,lesson_id).title=='Histórico'
