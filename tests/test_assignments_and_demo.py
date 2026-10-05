import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.jwt import UserRole, create_access_token
from app.main import app

client = TestClient(app)


def _write_minimal_pptx(path: Path, slide_text: str) -> None:
    slide_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:sp>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
          <a:p><a:r><a:t>{slide_text}</a:t></a:r></a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
</p:sld>
"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("ppt/slides/slide1.xml", slide_xml)


@pytest.fixture(scope="module")
def teacher_auth():
    token = create_access_token(
        user_id="teacher_demo_123",
        role=UserRole.TEACHER,
        school_id="SCH_DEMO_01",
        name="Demo Teacher",
    )
    return {"Authorization": f"Bearer {token}"}


def test_registered_teacher_login():
    """Verify teacher login after explicit account registration."""
    teacher_email = "demo.teacher.assignments@aaroh.org"
    teacher_password = "DemoTeacherPass2026!"

    client.post(
        "/api/v1/auth/teacher/signup",
        json={
            "name": "Demo Teacher",
            "email": teacher_email,
            "password": teacher_password,
            "school_id": "SCH_DEMO_01",
            "district_id": "DIST_DEMO_01",
            "employee_id": "DEMO_TCH_01",
            "assigned_grades": [1, 2, 3, 4, 5],
            "subjects": ["Science", "Mathematics"],
        },
    )

    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "login_id": teacher_email,
            "password": teacher_password,
        },
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert data["success"] is True
    assert data["data"]["role"] == "TEACHER"
    assert "access_token" in data["data"]


def test_assignment_full_flow(teacher_auth):
    """Verify assignment generation, PDF download, and submission."""
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
    assert all(item.get("prompt") for item in asgn_data["items"])
    asgn_id = asgn_data["id"]

    list_resp = client.get("/api/v1/assignments")
    assert list_resp.status_code == 200
    assert any(a["id"] == asgn_id for a in list_resp.json()["data"])

    get_resp = client.get(f"/api/v1/assignments/{asgn_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["id"] == asgn_id

    pdf_resp = client.get(f"/api/v1/assignments/{asgn_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"].startswith("application/pdf")
    assert pdf_resp.content.startswith(b"%PDF")

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


def test_pptx_upload_generates_source_grounded_pdf(teacher_auth, tmp_path):
    """Teacher PPTX upload should produce questions grounded in scanned slide text."""
    pptx_path = tmp_path / "seed_germination_lesson.pptx"
    slide_text = (
        "Seed germination begins when a seed absorbs water and the tiny root comes out first. "
        "Students observe soaked gram seeds in a classroom bowl and compare them with dry seeds. "
        "Warmth, air, and moisture help the young plant grow from the seed."
    )
    _write_minimal_pptx(pptx_path, slide_text)

    with open(pptx_path, "rb") as file_obj:
        upload_resp = client.post(
            "/api/v1/content/upload",
            files={
                "file": (
                    pptx_path.name,
                    file_obj,
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                )
            },
            data={"grade_hint": "Grade 4", "subject_hint": "Science"},
            headers=teacher_auth,
        )

    assert upload_resp.status_code == 201
    document_id = upload_resp.json()["data"]["document_id"]

    gen_resp = client.post(
        "/api/v1/assignments/generate",
        json={
            "document_id": document_id,
            "grade": 4,
            "subject": "Science",
            "target_language": "en",
            "number_of_questions": 3,
            "difficulty": "medium",
        },
        headers=teacher_auth,
    )

    assert gen_resp.status_code == 201
    asgn_data = gen_resp.json()["data"]
    assert len(asgn_data["items"]) == 3
    assert all(item.get("prompt") for item in asgn_data["items"])
    assert any("germination" in item.get("source_excerpt", "").lower() for item in asgn_data["items"])
    assert any("uploaded lesson" in item.get("prompt", "").lower() for item in asgn_data["items"])

    pdf_resp = client.get(f"/api/v1/assignments/{asgn_data['id']}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"].startswith("application/pdf")
    assert pdf_resp.content.startswith(b"%PDF")


def test_stt_transcription_endpoint():
    """Verify STT endpoint when an audio fixture exists."""
    audio_path = Path("data/uploads/audio/student_water_ans.wav")
    if not audio_path.exists():
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
