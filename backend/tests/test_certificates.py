from dataclasses import replace
from io import BytesIO
from pypdf import PdfReader

from app.integrations import DemoIntegrations, get_current_user, get_integrations
from app.main import app
from tests.test_lessons import create_lesson, upload


def test_certificate_eligibility_snapshot_ownership_and_pdf(upload_context):
    client, _, _ = upload_context
    lesson = create_lesson(client)
    media_id = upload(client)
    base = f"/api/learning/lessons/{lesson['id']}"
    client.patch(base + "/media", json={"media_id": media_id})
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["aluno-demo"]
    url = "/api/learning/courses/fisica-quantica/certificate"
    assert client.post(url).status_code == 409
    assert client.post("/api/learning/courses/fisica-enem-mecanica/certificate").status_code == 409
    client.patch(base + "/progress", json={"media_id": media_id, "position_seconds": 11})
    response = client.post(url)
    assert response.status_code == 200, response.text
    certificate = response.json()
    assert client.post(url).json()["id"] == certificate["id"]
    assert len(client.get("/api/learning/certificates").json()) == 1
    public = client.get(f"/api/learning/certificates/verify/{certificate['verification_code']}")
    assert public.status_code == 200
    assert "student_id" not in public.json()
    assert client.get("/api/learning/certificates/verify/missing").status_code == 404
    pdf = client.get(f"/api/learning/certificates/{certificate['id']}/download")
    assert pdf.content.startswith(b"%PDF-") and pdf.headers["content-type"] == "application/pdf"
    text = PdfReader(BytesIO(pdf.content)).pages[0].extract_text()
    assert certificate["student_name"] in text
    assert certificate["course_title"] in text
    assert certificate["verification_code"] in text
    class Changed(DemoIntegrations):
        def course(self, course_id):
            course = super().course(course_id)
            return replace(course, title="Changed") if course else None
        def has_access(self, student_id, course_id):
            return False
    app.dependency_overrides[get_integrations] = Changed
    assert client.get(f"/api/learning/certificates/{certificate['id']}").json()["course_title"] == certificate["course_title"]
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["aluno-demo-2"]
    assert client.get(f"/api/learning/certificates/{certificate['id']}/download").status_code == 403


def test_notification_failure_does_not_duplicate_certificate(upload_context):
    client, _, _ = upload_context
    lesson = create_lesson(client)
    media_id = upload(client)
    client.patch(f"/api/learning/lessons/{lesson['id']}/media", json={"media_id": media_id})
    app.dependency_overrides[get_current_user] = lambda: DemoIntegrations.users["aluno-demo"]
    client.patch(f"/api/learning/lessons/{lesson['id']}/progress", json={"media_id": media_id, "position_seconds": 11})
    class Failed(DemoIntegrations):
        def notify_certificate(self, user_id, certificate_id):
            raise RuntimeError("Notification unavailable")
    app.dependency_overrides[get_integrations] = Failed
    url = "/api/learning/courses/fisica-quantica/certificate"
    first = client.post(url)
    assert first.status_code == 200
    assert client.post(url).json()["id"] == first.json()["id"]
