import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.jwt import create_access_token, UserRole

client = TestClient(app)

def test_unauthenticated_request_rejected():
    """Unauthenticated requests to protected endpoints return 401 Unauthorized."""
    resp = client.post("/api/v1/teachers/students", json={
        "name": "Test",
        "class_grade": 3,
        "roll_number": "1",
    })
    assert resp.status_code == 401
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "NO_AUTH_HEADER"

def test_student_cannot_call_teacher_endpoint():
    """Role escalation: Student token calling Teacher endpoint returns 403 Forbidden."""
    student_token = create_access_token(user_id="student_hacker_01", role=UserRole.STUDENT)
    headers = {"Authorization": f"Bearer {student_token}"}

    resp = client.post("/api/v1/teachers/students", json={
        "name": "Unauthorized Add",
        "class_grade": 3,
        "roll_number": "99",
    }, headers=headers)
    assert resp.status_code == 403
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

def test_student_cannot_access_other_student_data():
    """Data isolation: Student cannot access private profile or history of another student."""
    student1_token = create_access_token(user_id="student_alice", role=UserRole.STUDENT)
    headers = {"Authorization": f"Bearer {student1_token}"}

    # Student Alice tries to view Student Bob's profile
    resp = client.get("/api/v1/students/student_bob", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "FORBIDDEN_PROFILE_ACCESS"

    # Student Alice tries to view Student Bob's quiz history
    hist_resp = client.get("/api/v1/assessment/students/student_bob/history", headers=headers)
    assert hist_resp.status_code == 403
    assert hist_resp.json()["success"] is False
    assert "strictly isolated" in hist_resp.json()["error"]["message"]
