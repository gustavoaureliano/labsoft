"""Tests for ReportService, ContentModerationService, TeacherAnalyticsService, and AdminDashboardService (F28, F41, F43, F45)."""

from tests.conftest import BackendTestCase


def _run_f28_and_f45(test_context):
    client, _, integrations = test_context
    student_headers = {"X-Demo-User": "aluno-demo"}
    admin_headers = {"X-Demo-User": "admin-demo"}

    rep1 = client.post(
        "/api/moderation/reports",
        json={
            "item_id": "leis-newton",
            "item_type": "lesson",
            "reason": "Informação imprecisa no minuto 05:10",
        },
        headers=student_headers,
    )
    assert rep1.status_code == 201
    assert rep1.json()["status"] == "pending"

    rep_dup = client.post(
        "/api/moderation/reports",
        json={
            "item_id": "leis-newton",
            "item_type": "lesson",
            "reason": "Outro motivo repetido",
        },
        headers=student_headers,
    )
    assert rep_dup.status_code == 409

    queue = client.get("/api/moderation/queue", headers=admin_headers)
    assert queue.status_code == 200
    items = queue.json()
    assert len(items) == 1
    assert items[0]["item_id"] == "leis-newton"
    assert items[0]["reports_count"] == 1

    decision = client.post(
        "/api/moderation/queue/leis-newton/decision",
        json={
            "item_type": "lesson",
            "decision": "keep",
            "justification": "Conteúdo revisado e validado pela equipe pedagógica.",
        },
        headers=admin_headers,
    )
    assert decision.status_code == 200
    body = decision.json()
    assert body["status"] == "kept"
    assert body["audit_recorded"] is True
    assert len(integrations.audit_log) == 1
    assert integrations.audit_log[0].item_id == "leis-newton"

    assert client.get("/api/moderation/queue", headers=admin_headers).json() == []


def _run_f41(test_context):
    client, _, _ = test_context
    student_headers = {"X-Demo-User": "aluno-demo"}
    teacher_headers = {"X-Demo-User": "professor-demo"}

    client.put(
        "/api/interactions/ratings/leis-newton",
        json={"target_type": "lesson", "stars": 5},
        headers=student_headers,
    )
    q_resp = client.post(
        "/api/questions",
        json={
            "course_id": "fisica-enem-mecanica",
            "lesson_id": "leis-newton",
            "prompt": "Dúvida para métrica do professor",
        },
        headers=student_headers,
    )
    client.patch(
        f"/api/questions/{q_resp.json()['id']}/answer",
        json={"answer": "Respondida rapidamente!"},
        headers=teacher_headers,
    )

    analytics = client.get(
        "/api/analytics/teacher?period=30d&course_id=fisica-enem-mecanica",
        headers=teacher_headers,
    )
    assert analytics.status_code == 200
    data = analytics.json()
    assert data["course_id"] == "fisica-enem-mecanica"
    assert data["average_rating"]["value"] == 5.0
    assert "ContentRating" in data["average_rating"]["source"]
    assert data["question_response_rate"]["value"] == 100.0
    assert "Question" in data["question_response_rate"]["source"]
    assert data["enrollments"]["value"] == 600

    forbidden = client.get(
        "/api/analytics/teacher?period=30d&course_id=biologia-celular",
        headers=teacher_headers,
    )
    assert forbidden.status_code == 403


def _run_f43(test_context):
    client, _, _ = test_context
    admin_headers = {"X-Demo-User": "admin-demo"}

    monthly = client.get(
        "/api/analytics/admin-dashboard?period=monthly", headers=admin_headers
    )
    assert monthly.status_code == 200
    m_data = monthly.json()
    assert m_data["period"] == "monthly"
    assert len(m_data["access_series"]) == 4
    assert m_data["total_users"] == 2516

    annual = client.get(
        "/api/analytics/admin-dashboard?period=annual", headers=admin_headers
    )
    assert annual.status_code == 200
    a_data = annual.json()
    assert a_data["period"] == "annual"
    assert len(a_data["access_series"]) == 12


def test_f28_and_f45_report_deduplication_and_moderation_decision_with_audit(
    test_context,
):
    _run_f28_and_f45(test_context)


def test_f41_teacher_analytics_filters_and_identifies_indicator_sources(
    test_context,
):
    _run_f41(test_context)


def test_f43_admin_dashboard_switches_periods(test_context):
    _run_f43(test_context)


class TestAnalyticsAndModeration(BackendTestCase):
    def test_f28_and_f45(self):
        _run_f28_and_f45(self.test_context)

    def test_f41(self):
        _run_f41(self.test_context)

    def test_f43(self):
        _run_f43(self.test_context)
