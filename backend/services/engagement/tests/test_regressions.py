"""Regression tests for bugs found in the engagement audit (F23-F26, F28, F31, F41, F45)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app.library_interaction.models import ContentRating
from tests.test_remote_library import headers, integrated  # noqa: F401 (fixture)

STUDENT = {"X-Demo-User": "aluno-demo"}
STUDENT_2 = {"X-Demo-User": "aluno-demo-2"}
TEACHER = {"X-Demo-User": "professor-demo"}
ADMIN = {"X-Demo-User": "admin-demo"}


def _variants(uuid: str) -> list[str]:
    return [uuid.upper(), uuid.replace("-", ""), "{" + uuid + "}"]


# --- UUID spellings must not bypass unique keys (real adapter) ---


def test_uuid_spellings_do_not_duplicate_ratings_favorites_or_reports(integrated):  # noqa: F811
    client, ids, course, lesson, state = integrated
    for target in [lesson, *_variants(lesson)]:
        rated = client.put(f"/api/interactions/ratings/{target}", headers=headers(),
                           json={"target_type": "lesson", "stars": 1})
        assert rated.status_code == 200, rated.text
        assert rated.json()["target_id"] == lesson
        assert rated.json()["total_ratings"] == 1

    for target in [lesson, *_variants(lesson)]:
        assert client.post(f"/api/library/favorites/{target}", headers=headers()).status_code == 201
    favorites = client.get("/api/library/favorites", headers=headers(method="GET")).json()
    assert [item["lesson_id"] for item in favorites] == [lesson]
    assert client.delete(f"/api/library/favorites/{lesson.upper()}", headers=headers()).status_code == 204
    assert client.get("/api/library/favorites", headers=headers(method="GET")).json() == []

    first = client.post("/api/moderation/reports", headers=headers(),
                        json={"item_type": "lesson", "item_id": lesson, "reason": "Problema"})
    assert first.status_code == 201
    again = client.post("/api/moderation/reports", headers=headers(),
                        json={"item_type": "lesson", "item_id": lesson.upper(), "reason": "Problema"})
    assert again.status_code == 409
    queue = client.get("/api/moderation/queue", headers=headers(3, "GET")).json()
    assert len(queue) == 1


def test_playlist_rejects_same_lesson_spelled_twice(integrated):  # noqa: F811
    client, ids, course, lesson, state = integrated
    playlist = client.post("/api/library/playlists", headers=headers(), json={"name": "P"}).json()
    saved = client.put(f"/api/library/playlists/{playlist['id']}/lessons", headers=headers(),
                       json={"lesson_ids": [lesson, lesson.upper()]})
    assert saved.status_code == 409


def test_teacher_analytics_works_with_real_login(integrated):  # noqa: F811
    client, ids, course, lesson, state = integrated
    assert client.post(f"/api/library/history/{lesson}", headers=headers()).status_code == 200
    assert client.put(f"/api/interactions/ratings/{lesson}", headers=headers(),
                      json={"target_type": "lesson", "stars": 4}).status_code == 200
    result = client.get("/api/analytics/teacher?period=30d", headers=headers(2, "GET"))
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["enrollments"]["value"] is None and "não integrado" in data["enrollments"]["source"]
    assert data["completion_rate"]["value"] is None
    assert data["active_students"]["value"] == 1
    assert data["average_rating"]["value"] == 4.0
    assert data["question_response_rate"]["value"] is None
    assert [item["course_id"] for item in data["courses"]] == [course]


# --- F24 / F25 (demo adapter) ---


def test_empty_note_clears_it(test_context):
    client, _, _ = test_context
    url = "/api/interactions/lessons/leis-newton/note"
    assert client.put(url, json={"content": "texto"}, headers=STUDENT).status_code == 200
    cleared = client.put(url, json={"content": "   "}, headers=STUDENT)
    assert cleared.status_code == 200 and cleared.json()["content"] == ""
    assert client.get(url, headers=STUDENT).json()["content"] == ""


def test_replies_respect_parent_moderation(test_context):
    client, _, _ = test_context
    url = "/api/interactions/lessons/leis-newton/comments"
    parent = client.post(url, json={"content": "Pergunta legítima"}, headers=STUDENT).json()
    reply = client.post(url, json={"content": "Resposta", "parent_id": parent["id"]}, headers=STUDENT_2)
    assert reply.status_code == 201

    hidden = client.post(f"/api/moderation/queue/{parent['id']}/decision", headers=ADMIN,
                         json={"item_type": "comment", "decision": "hide", "justification": "x"})
    assert hidden.status_code == 404  # not in the queue until reported
    assert client.post("/api/moderation/reports", headers=STUDENT_2, json={
        "item_type": "comment", "item_id": parent["id"], "reason": "Ofende"}).status_code == 201
    hidden = client.post(f"/api/moderation/queue/{parent['id']}/decision", headers=ADMIN,
                         json={"item_type": "comment", "decision": "hide", "justification": "x"})
    assert hidden.status_code == 200

    listed = [item["id"] for item in client.get(url, headers=STUDENT).json()]
    assert parent["id"] not in listed and reply.json()["id"] not in listed
    late = client.post(url, json={"content": "Oi", "parent_id": parent["id"]}, headers=STUDENT_2)
    assert late.status_code == 404
    # A moderated comment can't be reported again to reopen the case.
    assert client.post("/api/moderation/reports", headers=STUDENT, json={
        "item_type": "comment", "item_id": parent["id"], "reason": "De novo"}).status_code == 404


def test_accented_blocked_terms_are_held(test_context):
    client, _, _ = test_context
    created = client.post("/api/interactions/lessons/leis-newton/comments",
                          json={"content": "Isso é IMPRÓPRIO"}, headers=STUDENT)
    assert created.status_code == 201 and created.json()["moderation_status"] == "held"


def test_approving_held_reply_notifies_parent_author(test_context):
    client, _, _ = test_context
    url = "/api/interactions/lessons/leis-newton/comments"
    parent = client.post(url, json={"content": "Dúvida"}, headers=STUDENT).json()
    reply = client.post(url, json={"content": "isso é spam?", "parent_id": parent["id"]},
                        headers=STUDENT_2).json()
    assert reply["moderation_status"] == "held"
    assert [n for n in client.get("/api/notifications", headers=STUDENT).json()
            if n["kind"] == "comment_reply"] == []
    kept = client.post(f"/api/moderation/queue/{reply['id']}/decision", headers=ADMIN,
                       json={"item_type": "comment", "decision": "keep", "justification": "Ok"})
    assert kept.status_code == 200
    replies = [n for n in client.get("/api/notifications", headers=STUDENT).json()
               if n["kind"] == "comment_reply"]
    assert len(replies) == 1


# --- F45 ---


def test_moderation_delete_is_final_and_repeat_is_idempotent(test_context):
    client, _, integrations = test_context
    comment = client.post("/api/interactions/lessons/leis-newton/comments",
                          json={"content": "Comentário"}, headers=STUDENT).json()
    assert client.post("/api/moderation/reports", headers=STUDENT_2, json={
        "item_type": "comment", "item_id": comment["id"], "reason": "x"}).status_code == 201
    url = f"/api/moderation/queue/{comment['id']}/decision"
    body = {"item_type": "comment", "decision": "delete", "justification": "Viola regras"}
    assert client.post(url, headers=ADMIN, json=body).status_code == 200
    assert client.post(url, headers=ADMIN, json=body).status_code == 200
    assert len(integrations.audit_log) == 1
    restore = client.post(url, headers=ADMIN, json={**body, "decision": "keep"})
    assert restore.status_code == 409
    assert client.get("/api/moderation/queue", headers=ADMIN).json() == []


# --- F31 ---


def test_question_cannot_be_answered_twice(test_context):
    client, _, _ = test_context
    question = client.post("/api/questions", headers=STUDENT, json={
        "course_id": "fisica-enem-mecanica", "lesson_id": None, "prompt": "Como?"}).json()
    url = f"/api/questions/{question['id']}/answer"
    assert client.patch(url, headers=TEACHER, json={"answer": "Assim."}).status_code == 200
    again = client.patch(url, headers=TEACHER, json={"answer": "Outra."})
    assert again.status_code == 409
    answered = [n for n in client.get("/api/notifications", headers=STUDENT).json()
                if n["kind"] == "question_answered"]
    assert len(answered) == 1


# --- F41 ---


def test_teacher_metrics_respect_period(test_context):
    client, sessions, _ = test_context
    assert client.put("/api/interactions/ratings/leis-newton", headers=STUDENT,
                      json={"target_type": "lesson", "stars": 1}).status_code == 200
    with sessions() as session:
        session.execute(update(ContentRating).values(
            updated_at=datetime.now(timezone.utc) - timedelta(days=60)))
        session.commit()
    assert client.put("/api/interactions/ratings/leis-newton", headers=STUDENT_2,
                      json={"target_type": "lesson", "stars": 5}).status_code == 200

    def metrics(period):
        return client.get(f"/api/analytics/teacher?period={period}&course_id=fisica-enem-mecanica",
                          headers=TEACHER).json()

    recent = metrics("30d")
    assert recent["total_ratings"]["value"] == 1 and recent["average_rating"]["value"] == 5.0
    assert recent["question_response_rate"]["value"] is None
    older = metrics("90d")
    assert older["total_ratings"]["value"] == 2 and older["average_rating"]["value"] == 3.0
