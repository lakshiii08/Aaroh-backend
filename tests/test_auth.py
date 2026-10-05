import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.jwt import create_access_token, decode_token, UserRole
from app.core.security import generate_secure_password, hash_password, verify_password

client = TestClient(app)

def test_secure_password_generator():
    """Verifies that generated student passwords are random, secure, and meet entropy standards."""
    pwd1 = generate_secure_password(8)
    pwd2 = generate_secure_password(8)
    assert len(pwd1) >= 8
    assert pwd1 != pwd2
    assert any(c.isupper() for c in pwd1)
    assert any(c.islower() for c in pwd1)
    assert any(c.isdigit() for c in pwd1)
    # Ensure no predictable passwords
    assert pwd1 not in ["123456", "student123", "password", "rollnumber123"]

def test_password_hashing():
    """Verifies password hashing using bcrypt."""
    raw = "MySecurePass123"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPass", hashed) is False

def test_jwt_token_creation_and_decoding():
    """Verifies JWT access token creation with standard RBAC claims."""
    token = create_access_token(
        user_id="user_test_01",
        role=UserRole.TEACHER,
        school_id="SCH_TEST_01",
        district_id="DIST_01",
        name="Test Teacher",
    )
    payload = decode_token(token)
    assert payload["sub"] == "user_test_01"
    assert payload["role"] == UserRole.TEACHER
    assert payload["school_id"] == "SCH_TEST_01"
    assert payload["token_type"] == "access"

def test_teacher_signup_and_login_flow():
    """Tests teacher registration and authentication."""
    teacher_email = "teacher.test.unique@aaroh.org"
    signup_payload = {
        "name": "Smt. Sunita Bai",
        "email": teacher_email,
        "password": "SecureTeacherPass2026!",
        "school_id": "SCH_TEST_01",
        "district_id": "DIST_TEST_01",
        "employee_id": "CG-9921",
        "assigned_grades": [3, 4],
        "subjects": ["Environmental Studies"],
    }

    # 1. Signup
    signup_resp = client.post("/api/v1/auth/teacher/signup", json=signup_payload)
    assert signup_resp.status_code == 201
    signup_data = signup_resp.json()
    assert signup_data["success"] is True
    assert signup_data["data"]["role"] == "TEACHER"
    assert "access_token" in signup_data["data"]

    # 2. Duplicate signup should be rejected
    dup_resp = client.post("/api/v1/auth/teacher/signup", json=signup_payload)
    assert dup_resp.status_code == 409
    dup_data = dup_resp.json()
    assert dup_data["success"] is False
    assert dup_data["error"]["code"] == "RESOURCE_ALREADY_EXISTS"

    # 3. Login with correct password
    login_resp = client.post("/api/v1/auth/login", json={
        "login_id": teacher_email,
        "password": "SecureTeacherPass2026!",
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert login_data["success"] is True
    assert "access_token" in login_data["data"]

    # 4. Login with invalid password
    bad_login_resp = client.post("/api/v1/auth/login", json={
        "login_id": teacher_email,
        "password": "WrongPassword!",
    })
    assert bad_login_resp.status_code == 401
    bad_data = bad_login_resp.json()
    assert bad_data["success"] is False
    assert bad_data["error"]["code"] == "INVALID_CREDENTIALS"

def test_root_and_health_endpoints():
    """Verifies system status and health check."""
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    root_data = root_resp.json()
    assert root_data["success"] is True
    assert root_data["data"]["status"] == "operational"

    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert health_data["success"] is True
    assert "mongodb" in health_data["data"]["components"]
    assert "postgresql" in health_data["data"]["components"]
    assert "aaroh_ai_core" in health_data["data"]["components"]
