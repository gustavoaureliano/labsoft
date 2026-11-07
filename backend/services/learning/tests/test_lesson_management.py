from app.integrations import DemoIntegrations, get_current_user
from app.main import app
from tests.test_lessons import create_lesson, upload


def test_edit_detach_delete_and_preserve_video(upload_context):
    client, _, root = upload_context
    lesson = create_lesson(client)
    media_id = upload(client)
    url = f"/api/learning/lessons/{lesson['id']}"
    assert client.patch(url + "/media", json={"media_id": media_id}).status_code == 200
    assert client.patch(url, json={"title": "Nova aula", "description": "Detalhes"}).json()["title"] == "Nova aula"
    assert client.patch(url + "/media", json={"media_id": None}).json()["media_id"] is None
    assert client.delete(url).status_code == 204
    assert client.get("/api/learning/courses/fisica-quantica/lessons").json() == []
    assert len(list(root.rglob("*.mp4"))) == 1


def test_reorder_and_invalid_request_preserve_order(upload_context):
    client, _, _ = upload_context
    first, second = create_lesson(client, 1), create_lesson(client, 2)
    url = "/api/learning/courses/fisica-quantica/lessons/order"
    expected = [second["id"], first["id"]]
    result = client.put(url, json={"lesson_ids": expected})
    assert result.status_code == 200
    assert [lesson["position"] for lesson in result.json()] == [1, 2]
    for ids in ([first["id"]], [first["id"], first["id"]], [first["id"], "foreign"]):
        assert client.put(url, json={"lesson_ids": ids}).status_code == 400
    assert [lesson["id"] for lesson in client.get(url.removesuffix("/order")).json()] == expected
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["professor-demo-2"]
    assert client.delete(f"/api/learning/lessons/{first['id']}").status_code == 403
    assert client.put(url, json={"lesson_ids": expected}).status_code == 403
