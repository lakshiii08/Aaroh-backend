import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.jwt import create_access_token, UserRole

client = TestClient(app)

@pytest.fixture(scope="module")
def teacher_auth():
    token = create_access_token(
        user_id="teacher_ai_test_01",
        role=UserRole.TEACHER,
        school_id="SCH_TEST_01",
        name="Teacher AI Tester",
    )
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def district_admin_auth():
    token = create_access_token(
        user_id="admin_district_01",
        role=UserRole.DISTRICT_ADMIN,
        school_id="SCH_TEST_01",
        district_id="CG_BASTAR_01",
        name="District Admin",
    )
    return {"Authorization": f"Bearer {token}"}

# ── 1. Content & Search ───────────────────────────────────────────────────────
def test_content_documents_and_search():
    # Documents list
    doc_resp = client.get("/api/v1/content/documents")
    assert doc_resp.status_code == 200
    assert doc_resp.json()["success"] is True

    # Vector search
    search_resp = client.post("/api/v1/content/search", json={
        "query": "sources of water in village",
        "top_k": 3,
    })
    assert search_resp.status_code == 200
    data = search_resp.json()
    assert data["success"] is True
    assert "results" in data["data"]

# ── 2. Translation & Tribal Dialects ──────────────────────────────────────────
def test_translation_endpoints():
    # Supported languages
    lang_resp = client.get("/api/v1/translation/languages")
    assert lang_resp.status_code == 200
    assert "supported_languages" in lang_resp.json()["data"]

    # Single translation
    tr_resp = client.post("/api/v1/translation/translate", json={
        "text": "Water is very important for life.",
        "source_lang": "en",
        "target_lang": "hi",
        "target_dialect": "gon",
    })
    assert tr_resp.status_code == 200
    tr_data = tr_resp.json()
    assert tr_data["success"] is True
    assert "translated_text" in tr_data["data"]

    # Batch translation
    batch_resp = client.post("/api/v1/translation/batch", json={
        "texts": ["Plants need sunlight.", "Trees give us fruit."],
        "source_lang": "en",
        "target_lang": "hi",
    })
    assert batch_resp.status_code == 200
    assert batch_resp.json()["data"]["total_count"] == 2

    # Glossary lookup
    glossary_resp = client.get("/api/v1/translation/glossary/lookup?term=water&source_lang=en&target_lang=hi")
    assert glossary_resp.status_code == 200
    assert glossary_resp.json()["success"] is True

# ── 3. Simplification & LangGraph ─────────────────────────────────────────────
def test_simplification_and_langgraph():
    # Localize concept
    loc_resp = client.post("/api/v1/simplification/concepts/EVS-G3-WAT-01", json={
        "target_language": "hi",
        "target_dialect": "gon",
        "grade_level": 3,
    })
    assert loc_resp.status_code == 200
    loc_data = loc_resp.json()
    assert loc_data["success"] is True
    assert "lesson" in loc_data["data"]
    assert "simplified_explanation" in loc_data["data"]["lesson"]

    # LangGraph agent endpoint
    lg_resp = client.post("/api/v1/simplification/langgraph/concepts/EVS-G3-WAT-01", json={
        "target_language": "hi",
        "target_dialect": "gon",
        "grade_level": 3,
    })
    assert lg_resp.status_code == 200
    assert lg_resp.json()["data"]["agent"] == "LangGraph — SimplificationLocalizationGraph"

    # Cache status
    cache_resp = client.get("/api/v1/simplification/cache/status")
    assert cache_resp.status_code == 200
    assert cache_resp.json()["success"] is True

# ── 4. Assessment & Quiz Generation ───────────────────────────────────────────
def test_assessment_quiz_flow(teacher_auth):
    # Generate quiz
    gen_resp = client.post("/api/v1/assessment/quizzes/generate", json={
        "concept_code": "EVS-G3-WAT-01",
        "target_language": "hi",
        "target_dialect": "gon",
        "grade_level": 3,
    })
    assert gen_resp.status_code == 200
    quiz_data = gen_resp.json()["data"]
    assert "quiz_id" in quiz_data
    assert quiz_data["total_questions"] >= 3
    quiz_id = quiz_data["quiz_id"]

    # Submit quiz answers
    student_token = create_access_token(user_id="student_test_42", role=UserRole.STUDENT)
    sub_resp = client.post(
        f"/api/v1/assessment/quizzes/{quiz_id}/submit",
        json={"student_id": "student_test_42", "answers": {"Q1": "A", "Q2": "B", "Q3": "A"}},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()["data"]
    assert "score_pct" in sub_data

    # Student history
    hist_resp = client.get(
        "/api/v1/assessment/students/student_test_42/history",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert hist_resp.status_code == 200

    # Teacher concept report
    rep_resp = client.get("/api/v1/assessment/teachers/reports/EVS-G3-WAT-01", headers=teacher_auth)
    assert rep_resp.status_code == 200

# ── 5. Voice Intelligence ─────────────────────────────────────────────────────
def test_voice_intelligence():
    # Synthesize text
    synth_resp = client.post("/api/v1/voice/synthesize", json={
        "text": "नमस्ते बच्चों, आज हम जल चक्र के बारे में सीखेंगे।",
        "target_language": "hi",
        "section_name": "story",
    })
    assert synth_resp.status_code == 200
    assert "stream_url" in synth_resp.json()["data"]

    # Generate complete voice lesson
    vlesson_resp = client.post("/api/v1/voice/lessons/EVS-G3-WAT-01", json={
        "target_language": "hi",
        "grade_level": 3,
    })
    assert vlesson_resp.status_code == 200
    assert len(vlesson_resp.json()["data"]["audio_segments"]) >= 1

# ── 6. Teacher Copilot & Offline Edge Sync ────────────────────────────────────
def test_copilot_and_edge_sync(teacher_auth):
    # Generate multigrade lesson plan
    plan_resp = client.post(
        "/api/v1/copilot/lesson-plans/generate",
        json={"concept_code": "EVS-G3-WAT-01", "grade_level": 3, "target_language": "hi", "duration_mins": 45},
        headers=teacher_auth,
    )
    assert plan_resp.status_code == 200
    assert "multigrade_strategies" in plan_resp.json()["data"]

    # Generate remedial aid
    aid_resp = client.post(
        "/api/v1/copilot/remedial-aid/generate",
        json={"concept_code": "EVS-G3-WAT-01", "weak_bloom_level": "Understand", "target_language": "hi"},
        headers=teacher_auth,
    )
    assert aid_resp.status_code == 200
    assert "printable_guide" in aid_resp.json()["data"]

    # Export offline bundle
    exp_resp = client.post(
        "/api/v1/copilot/edge/packages/export",
        json={"grade_level": 3, "subject": "Environmental Studies", "target_language": "hi"},
        headers=teacher_auth,
    )
    assert exp_resp.status_code == 200
    assert "download_url" in exp_resp.json()["data"]

    # Mastery heatmap
    heat_resp = client.get("/api/v1/copilot/analytics/mastery-heatmap", headers=teacher_auth)
    assert heat_resp.status_code == 200

# ── 7. Gamification & Visual Storytelling ──────────────────────────────────────
def test_gamification_endpoints():
    # Generate quest
    quest_resp = client.post("/api/v1/gamification/quests/generate", json={
        "concept_code": "EVS-G3-WAT-01",
        "target_language": "hi",
        "target_dialect": "gon",
    })
    assert quest_resp.status_code == 200
    assert "reward_xp" in quest_resp.json()["data"]

    # Record activity
    act_resp = client.post("/api/v1/gamification/students/student_test_42/activity", json={
        "student_name": "Test Student",
        "school_id": "SCH_TEST_01",
        "grade_level": 3,
        "activity_type": "quest",
        "concept_code": "EVS-G3-WAT-01",
    })
    assert act_resp.status_code == 200

    # Portfolio
    port_resp = client.get("/api/v1/gamification/students/student_test_42/portfolio")
    assert port_resp.status_code == 200

    # Flashcards
    card_resp = client.post("/api/v1/gamification/flashcards/generate", json={
        "concept_code": "EVS-G3-WAT-01",
        "target_language": "hi",
        "target_dialect": "gon",
    })
    assert card_resp.status_code == 200
    assert card_resp.json()["data"]["total_cards"] >= 1

    # Leaderboard
    lb_resp = client.get("/api/v1/gamification/leaderboards/SCH_TEST_01")
    assert lb_resp.status_code == 200

# ── 8. District Administration ────────────────────────────────────────────────
def test_district_administration(district_admin_auth):
    # Remedial pathway
    path_resp = client.post(
        "/api/v1/district/interventions/generate-pathway",
        json={"student_id": "student_test_42", "student_name": "Test Student", "concept_code": "EVS-G3-WAT-01", "weak_bloom_level": "Understand", "target_language": "hi"},
        headers=district_admin_auth,
    )
    assert path_resp.status_code == 200
    assert len(path_resp.json()["data"]["steps"]) == 4

    # Parent voice note dispatch
    p_resp = client.post(
        "/api/v1/district/parent-advisory/send-voice-note",
        json={"student_id": "student_test_42", "student_name": "Test Student", "parent_phone": "+919876543210", "concept_code": "EVS-G3-WAT-01", "target_language": "hi", "target_dialect": "gon"},
        headers=district_admin_auth,
    )
    assert p_resp.status_code == 200
    assert "speech_script" in p_resp.json()["data"]

    # Pending interventions
    pend_resp = client.get("/api/v1/district/interventions/pending", headers=district_admin_auth)
    assert pend_resp.status_code == 200

    # District overview
    ov_resp = client.get("/api/v1/district/analytics/overview", headers=district_admin_auth)
    assert ov_resp.status_code == 200
