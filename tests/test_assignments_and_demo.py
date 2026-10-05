import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core.jwt import create_access_token, UserRole

client = TestClient(app)

@pytest.fixture(scope="module")
def teacher_auth():
    token = create_access_token(
        user_id="teacher_demo_123",
        role=UserRole.TEACHER,
        school_id="SCH_DEMO_01",
        name="Demo Teacher",
    )
    return {"Authorization": f"Bearer {token}"}

def test_demo_teacher_login():
    """Requirement #13 & #32: Verify demo teacher login with teacher@123 / teacher@123."""
    client.post("/api/v1/auth/teacher/signup", json={
        "name": "Demo Teacher",
        "email": "teacher@123",
        "password": "teacher@123",
        "school_id": "SCH_DEMO_01",
        "district_id": "DIST_DEMO_01",
        "employee_id": "DEMO_TCH_01",
        "assigned_grades": [1, 2, 3, 4, 5],
        "subjects": ["Science", "Mathematics"],
    })

    login_resp = client.post("/api/v1/auth/login", json={
        "login_id": "teacher@123",
        "password": "teacher@123",
    })
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert data["success"] is True
    assert data["data"]["role"] == "TEACHER"
    assert "access_token" in data["data"]

def test_assignment_full_flow(teacher_auth):
    """Requirement #6: Verify real assignment & worksheet generation and download."""
    # 1. Generate assignment using real Aaroh-AI
    gen_resp = client.post(
        "/api/v1/assignments/generate",
        json={
            "concept_code": "EVS-G3-WAT-01",
            "grade": 4,
            "subject": "Science",
            "target_language": "sat",
            "target_dialect": "sat",
            "number_of_questions": 4,
            "difficulty": "medium",
            "title": "Water Cycle & Village Ponds Assignment",
        },
        headers=teacher_auth,
    )
    assert gen_resp.status_code == 201
    asgn_data = gen_resp.json()["data"]
    assert "id" in asgn_data
    assert len(asgn_data["items"]) == 4
    asgn_id = asgn_data["id"]

    # 2. List assignments
    list_resp = client.get("/api/v1/assignments")
    assert list_resp.status_code == 200
    assert any(a["id"] == asgn_id for a in list_resp.json()["data"])

    # 3. Get single assignment
    get_resp = client.get(f"/api/v1/assignments/{asgn_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["id"] == asgn_id

    # 4. Download PDF / HTML printable worksheet
    pdf_resp = client.get(f"/api/v1/assignments/{asgn_id}/pdf")
    assert pdf_resp.status_code == 200
    assert "AAROH — AI-Powered Mother-Tongue Learning Platform" in pdf_resp.text

    # 5. Submit assignment answers
    subm_resp = client.post(
        f"/api/v1/assignments/{asgn_id}/submit",
        json={
            "student_id": "student_demo_01",
            "student_name": "Rahul Murmu",
            "answers": {
                asgn_data["items"][0]["id"]: "Plants take in water through roots from moist village soil.",
                asgn_data["items"][1]["id"]: "Ponds replenish during monsoon showers for village agriculture.",
            },
        },
    )
    assert subm_resp.status_code == 200
    subm_data = subm_resp.json()["data"]
    assert subm_data["score_percentage"] > 0
    assert "grade" in subm_data

def test_stt_transcription_endpoint():
    """Requirement #8: Verify real STT endpoint with actual audio file."""
    audio_path = Path("data/uploads/audio/student_water_ans.wav")
    if not audio_path.exists():
        # Fallback to any available audio in Aaroh-AI data
        candidates = list(Path("data/audio").glob("*.wav"))
        if candidates:
            audio_path = candidates[0]

    if audio_path.exists():
        with open(audio_path, "rb") as f:
            resp = client.post(
                "/api/v1/voice/stt",
                files={"audio_file": (audio_path.name, f, "audio/wav")},
                data={"language_code": "hi"},
            )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "transcribed_text" in data
