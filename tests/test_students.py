import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.jwt import create_access_token, UserRole

client = TestClient(app)

def test_teacher_creates_student_and_student_logs_in():
    """Full end-to-end test of Section 3, 4, 5:
    1. Teacher creates student account with roll number
    2. Backend auto-generates secure random password
    3. Password returned ONCE in teacher's response
    4. Student logs in using Roll Number as Login ID + generated password
    5. Duplicate roll number in same class/school is rejected
    """
    teacher_token = create_access_token(
        user_id="teacher_unit_01",
        role=UserRole.TEACHER,
        school_id="SCH_UNIT_01",
        district_id="DIST_UNIT_01",
        name="Teacher Unit",
    )
    headers = {"Authorization": f"Bearer {teacher_token}"}

    student_payload = {
        "name": "Manglu Netam",
        "class_grade": 3,
        "roll_number": "42",
        "village": "Chhindgarh",
        "section": "A",
    }

    # 1. Teacher creates student
    create_resp = client.post("/api/v1/teachers/students", json=student_payload, headers=headers)
    assert create_resp.status_code == 201
    create_data = create_resp.json()
    assert create_data["success"] is True

    data = create_data["data"]
    assert data["name"] == "Manglu Netam"
    assert data["roll_number"] == "42"
    assert data["login_id"] == "42"
    assert "temporary_password" in data
    temp_password = data["temporary_password"]
    assert len(temp_password) >= 8
    student_id = data["student_id"]

    # 2. Duplicate roll number in same school and class must be rejected
    dup_resp = client.post("/api/v1/teachers/students", json=student_payload, headers=headers)
    assert dup_resp.status_code == 409
    dup_data = dup_resp.json()
    assert dup_data["success"] is False
    assert dup_data["error"]["code"] == "RESOURCE_ALREADY_EXISTS"

    # 3. Student logs in using Roll Number (Login ID) + Temporary Password + School Code
    student_login_resp = client.post("/api/v1/auth/login", json={
        "login_id": "42",
        "password": temp_password,
        "school_code": "SCH_UNIT_01",
    })
    assert student_login_resp.status_code == 200
    login_data = student_login_resp.json()
    assert login_data["success"] is True
    assert login_data["data"]["role"] == "STUDENT"
    assert login_data["data"]["roll_number"] == "42"
    assert "access_token" in login_data["data"]

    student_token = login_data["data"]["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 4. Student can view their own profile (which never contains the password)
    prof_resp = client.get(f"/api/v1/students/{student_id}", headers=student_headers)
    assert prof_resp.status_code == 200
    prof_data = prof_resp.json()
    assert prof_data["success"] is True
    assert prof_data["data"]["name"] == "Manglu Netam"
    assert "password" not in prof_data["data"]
    assert "temporary_password" not in prof_data["data"]
    assert "hashed_password" not in prof_data["data"]

    # 5. Teacher lists students for their school
    list_resp = client.get("/api/v1/teachers/students", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["success"] is True
    assert any(s["roll_number"] == "42" for s in list_data["data"])
