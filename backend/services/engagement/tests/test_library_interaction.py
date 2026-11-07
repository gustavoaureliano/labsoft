"""Tests for StudyLibraryService and LessonInteractionService (F21-F26)."""

from tests.conftest import BackendTestCase


def _run_f21(test_context):
    client, _, _ = test_context
    headers = {"X-Demo-User": "aluno-demo"}

    r1 = client.post("/api/library/history/leis-newton", headers=headers)
    assert r1.status_code == 200
    assert r1.json()["lesson_id"] == "leis-newton"

    r2 = client.post("/api/library/history/trabalho-energia", headers=headers)
    assert r2.status_code == 200

    r3 = client.post("/api/library/history/leis-newton", headers=headers)
    assert r3.status_code == 200

    history = client.get("/api/library/history", headers=headers)
    assert history.status_code == 200
    items = history.json()
    assert [item["lesson_id"] for item in items] == [
        "leis-newton",
        "trabalho-energia",
    ]


def _run_f22(test_context):
    client, _, _ = test_context
    headers = {"X-Demo-User": "aluno-demo"}

    add1 = client.post("/api/library/favorites/leis-newton", headers=headers)
    assert add1.status_code == 201
    add2 = client.post("/api/library/favorites/leis-newton", headers=headers)
    assert add2.status_code == 201

    favs = client.get("/api/library/favorites", headers=headers)
    assert favs.status_code == 200
    assert len(favs.json()) == 1
    assert favs.json()[0]["lesson_id"] == "leis-newton"

    rem = client.delete("/api/library/favorites/leis-newton", headers=headers)
    assert rem.status_code == 204
    assert client.get("/api/library/favorites", headers=headers).json() == []


def _run_f23(test_context):
    client, _, _ = test_context
    headers = {"X-Demo-User": "aluno-demo"}

    created = client.post(
        "/api/library/playlists",
        json={"name": "Revisão Mecânica"},
        headers=headers,
    )
    assert created.status_code == 201
    playlist_id = created.json()["id"]

    dup = client.post(
        "/api/library/playlists",
        json={"name": "Revisão Mecânica"},
        headers=headers,
    )
    assert dup.status_code == 409

    renamed = client.patch(
        f"/api/library/playlists/{playlist_id}",
        json={"name": "Revisão Final ENEM"},
        headers=headers,
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Revisão Final ENEM"

    organized = client.put(
        f"/api/library/playlists/{playlist_id}/lessons",
        json={
            "lesson_ids": [
                "trabalho-energia",
                "leis-newton",
                "impulso-momento",
            ]
        },
        headers=headers,
    )
    assert organized.status_code == 200
    assert organized.json()["lesson_ids"] == [
        "trabalho-energia",
        "leis-newton",
        "impulso-momento",
    ]

    context_resp = client.get(
        f"/api/library/playlists/{playlist_id}/playback/leis-newton",
        headers=headers,
    )
    assert context_resp.status_code == 200
    ctx = context_resp.json()
    assert ctx["playlist_name"] == "Revisão Final ENEM"
    assert ctx["previous_lesson_id"] == "trabalho-energia"
    assert ctx["next_lesson_id"] == "impulso-momento"

    deleted = client.delete(
        f"/api/library/playlists/{playlist_id}", headers=headers
    )
    assert deleted.status_code == 204


def _run_f24(test_context):
    client, _, _ = test_context
    student1 = {"X-Demo-User": "aluno-demo"}
    student2 = {"X-Demo-User": "aluno-demo-2"}

    saved = client.put(
        "/api/interactions/lessons/leis-newton/note",
        json={"content": "Anotação secreta do Bob sobre a 2ª Lei de Newton"},
        headers=student1,
    )
    assert saved.status_code == 200
    assert "2ª Lei" in saved.json()["content"]

    fetched1 = client.get(
        "/api/interactions/lessons/leis-newton/note", headers=student1
    )
    assert fetched1.status_code == 200
    assert (
        fetched1.json()["content"]
        == "Anotação secreta do Bob sobre a 2ª Lei de Newton"
    )

    fetched2 = client.get(
        "/api/interactions/lessons/leis-newton/note", headers=student2
    )
    assert fetched2.status_code == 200
    assert fetched2.json()["content"] == ""


def _run_f25(test_context):
    client, _, _ = test_context
    student1 = {"X-Demo-User": "aluno-demo"}
    student2 = {"X-Demo-User": "aluno-demo-2"}

    c1 = client.post(
        "/api/interactions/lessons/leis-newton/comments",
        json={"content": "Ótima aula sobre blocos acoplados!"},
        headers=student1,
    )
    assert c1.status_code == 201
    assert c1.json()["moderation_status"] == "approved"
    parent_id = c1.json()["id"]

    c2 = client.post(
        "/api/interactions/lessons/leis-newton/comments",
        json={"content": "Concordo, ajudou muito!", "parent_id": parent_id},
        headers=student2,
    )
    assert c2.status_code == 201

    notices = client.get("/api/notifications", headers=student1).json()
    assert any(n["kind"] == "comment_reply" for n in notices)

    c3 = client.post(
        "/api/interactions/lessons/leis-newton/comments",
        json={"content": "Este comentário tem conteúdo ofensivo e spam"},
        headers=student2,
    )
    assert c3.status_code == 201
    assert c3.json()["moderation_status"] == "held"

    public_comments = client.get(
        "/api/interactions/lessons/leis-newton/comments", headers=student1
    ).json()
    assert len(public_comments) == 2


def _run_f26(test_context):
    client, _, _ = test_context
    student1 = {"X-Demo-User": "aluno-demo"}
    student2 = {"X-Demo-User": "aluno-demo-2"}

    r1 = client.put(
        "/api/interactions/ratings/leis-newton",
        json={"target_type": "lesson", "stars": 4},
        headers=student1,
    )
    assert r1.status_code == 200
    assert r1.json()["average_rating"] == 4.0
    assert r1.json()["total_ratings"] == 1

    r2 = client.put(
        "/api/interactions/ratings/leis-newton",
        json={"target_type": "lesson", "stars": 5},
        headers=student1,
    )
    assert r2.status_code == 200
    assert r2.json()["average_rating"] == 5.0
    assert r2.json()["total_ratings"] == 1

    r3 = client.put(
        "/api/interactions/ratings/leis-newton",
        json={"target_type": "lesson", "stars": 3},
        headers=student2,
    )
    assert r3.status_code == 200
    assert r3.json()["average_rating"] == 4.0
    assert r3.json()["total_ratings"] == 2


def test_f21_history_records_and_orders_recent_views(test_context):
    _run_f21(test_context)


def test_f22_favorites_prevents_duplicates_and_removes(test_context):
    _run_f22(test_context)


def test_f23_playlists_crud_reorder_and_contextual_playback(test_context):
    _run_f23(test_context)


def test_f24_private_notes_isolated_by_student(test_context):
    _run_f24(test_context)


def test_f25_comments_reply_notification_and_auto_moderation(test_context):
    _run_f25(test_context)


def test_f26_ratings_unique_per_student_and_recalculates_average(test_context):
    _run_f26(test_context)


class TestLibraryInteraction(BackendTestCase):
    def test_f21(self):
        _run_f21(self.test_context)

    def test_f22(self):
        _run_f22(self.test_context)

    def test_f23(self):
        _run_f23(self.test_context)

    def test_f24(self):
        _run_f24(self.test_context)

    def test_f25(self):
        _run_f25(self.test_context)

    def test_f26(self):
        _run_f26(self.test_context)
