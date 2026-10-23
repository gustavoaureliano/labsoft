"""Tests for QuestionService and NotificationService (F29-F32)."""

from tests.conftest import BackendTestCase


def _run_f29_to_f32(test_context):
    client, _, _ = test_context
    student_headers = {"X-Demo-User": "aluno-demo"}
    teacher_headers = {"X-Demo-User": "professor-demo"}

    created = client.post(
        "/api/questions",
        json={
            "course_id": "fisica-enem-mecanica",
            "lesson_id": "leis-newton",
            "prompt": "Como decompor o peso no plano inclinado sem atrito?",
        },
        headers=student_headers,
    )
    assert created.status_code == 201
    q = created.json()
    assert q["status"] == "pending"
    assert q["teacher_id"] == "professor-demo"
    question_id = q["id"]

    teacher_notices = client.get(
        "/api/notifications", headers=teacher_headers
    ).json()
    assert len(teacher_notices) == 1
    assert teacher_notices[0]["kind"] == "new_question"
    assert teacher_notices[0]["is_read"] is False

    student_questions = client.get(
        "/api/questions/me", headers=student_headers
    ).json()
    assert len(student_questions) == 1
    assert student_questions[0]["id"] == question_id
    assert student_questions[0]["status"] == "pending"

    pending_list = client.get(
        "/api/questions/teacher?status=pending", headers=teacher_headers
    ).json()
    assert len(pending_list) == 1

    answered = client.patch(
        f"/api/questions/{question_id}/answer",
        json={"answer": "Use Px = P * sen(theta) e Py = P * cos(theta)."},
        headers=teacher_headers,
    )
    assert answered.status_code == 200
    assert answered.json()["status"] == "answered"
    assert (
        answered.json()["answer"]
        == "Use Px = P * sen(theta) e Py = P * cos(theta)."
    )

    student_notices = client.get(
        "/api/notifications", headers=student_headers
    ).json()
    assert len(student_notices) == 1
    notice_id = student_notices[0]["id"]
    assert student_notices[0]["kind"] == "question_answered"

    read_resp = client.patch(
        f"/api/notifications/{notice_id}/read", headers=student_headers
    )
    assert read_resp.status_code == 200
    assert read_resp.json()["is_read"] is True
    assert f"/duvidas?duvida={question_id}" in read_resp.json()["destination_url"]


def test_f29_f30_f31_f32_questions_and_notifications_lifecycle(test_context):
    _run_f29_to_f32(test_context)


class TestCommunication(BackendTestCase):
    def test_questions_and_notifications(self):
        _run_f29_to_f32(self.test_context)
