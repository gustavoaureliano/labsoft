from uuid import UUID, uuid4

from app.courses.models import Enrollment


TEACHER_ID = uuid4()
OTHER_TEACHER_ID = uuid4()
STUDENT_ID = uuid4()


def teacher_headers(teacher_id=TEACHER_ID):
    return {
        "X-Teacher-Id": str(teacher_id),
        "X-Teacher-Name": "Professora Ana",
    }


def course_payload(title="Física para o ENEM", access_type="free", price=None):
    return {
        "title": title,
        "subject": "Física",
        "area": "Ciências da Natureza",
        "summary": "Curso completo de física voltado para vestibulares.",
        "exams": ["ENEM", "FUVEST"],
        "access_type": access_type,
        "price": price,
    }


def create_course(client, **overrides):
    payload = course_payload()
    payload.update(overrides)
    response = client.post("/api/courses", json=payload, headers=teacher_headers())
    assert response.status_code == 201, response.text
    return response.json()


def add_lesson(client, course_id):
    response = client.post(
        f"/api/courses/{course_id}/lessons",
        json={
            "title": "Introdução",
            "summary": "Apresentação do curso",
            "duration_minutes": 20,
            "position": 0,
        },
        headers=teacher_headers(),
    )
    assert response.status_code == 201, response.text
    return response.json()


def publish(client, course_id):
    response = client.post(
        f"/api/courses/{course_id}/publication",
        json={"action": "publish"},
        headers=teacher_headers(),
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_f36_create_and_edit_draft(client):
    course = create_course(client)
    assert course["status"] == "draft"
    assert course["teacher_id"] == str(TEACHER_ID)

    response = client.patch(
        f"/api/courses/{course['id']}",
        json={"title": "Física Moderna para o ENEM"},
        headers=teacher_headers(),
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Física Moderna para o ENEM"
    assert response.json()["status"] == "draft"


def test_f36_validates_price_and_ownership(client):
    response = client.post(
        "/api/courses",
        json=course_payload(access_type="paid", price=None),
        headers=teacher_headers(),
    )
    assert response.status_code == 422

    course = create_course(client)
    response = client.patch(
        f"/api/courses/{course['id']}",
        json={"title": "Tentativa indevida"},
        headers=teacher_headers(OTHER_TEACHER_ID),
    )
    assert response.status_code == 403


def test_teacher_material_publication_and_public_catalog_flows(client):
    course = create_course(client)
    course_id = course["id"]

    dashboard = client.get("/api/teacher/courses", headers=teacher_headers())
    assert dashboard.status_code == 200
    assert dashboard.json()["draft_courses"] == 1

    preview = client.get(f"/api/courses/{course_id}/preview", headers=teacher_headers())
    assert "lessons" in preview.json()["publication_pending"]

    lesson = add_lesson(client, course_id)
    material = client.post(
        f"/api/courses/{course_id}/materials",
        json={
            "title": "Lista de exercícios",
            "description": "Questões comentadas",
            "kind": "link",
            "external_url": "https://example.com/exercicios",
            "lesson_id": lesson["id"],
            "access_level": "public",
            "position": 0,
        },
        headers=teacher_headers(),
    )
    assert material.status_code == 201, material.text

    publication = publish(client, course_id)
    assert publication["status"] == "published"

    landing = client.get("/api/landing")
    assert landing.status_code == 200
    assert landing.json()["sample_courses"][0]["id"] == course_id

    catalog = client.get("/api/courses", params={"exam": "ENEM"})
    assert catalog.status_code == 200
    assert catalog.json()["pagination"]["total"] == 1

    search = client.get("/api/search", params={"q": "fisica"})
    assert search.status_code == 200
    assert search.json()["total"] >= 1

    details = client.get(f"/api/courses/{course_id}")
    assert details.status_code == 200
    assert details.json()["access"]["allowed"] is True

    materials = client.get(f"/api/courses/{course_id}/materials")
    assert materials.status_code == 200
    assert materials.json()["items"][0]["authorized"] is True
    assert materials.json()["items"][0]["download_url"].startswith("https://")


def test_recommendations_exclude_courses_already_accessed(client, db_session):
    first = create_course(client, title="Física básica")
    add_lesson(client, first["id"])
    publish(client, first["id"])

    second = create_course(client, title="Física avançada")
    add_lesson(client, second["id"])
    publish(client, second["id"])

    db_session.add(
        Enrollment(course_id=UUID(first["id"]), student_id=STUDENT_ID, status="active")
    )
    db_session.commit()

    response = client.get(
        "/api/recommendations", headers={"X-Student-Id": str(STUDENT_ID)}
    )
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert first["id"] not in ids
    assert second["id"] in ids
