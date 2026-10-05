from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from app.services.gamification_service import GamificationService
from app.schemas.gamification_schemas import (
    GenerateQuestRequest,
    RecordActivityRequest,
    GenerateFlashcardsRequest,
)
from app.schemas.common_schemas import success_response
from app.api.deps import require_roles, get_current_user, get_optional_current_user
from app.core.jwt import UserRole

router = APIRouter(prefix="/gamification", tags=["Gamified Learning & Visual Flashcards"])

service = GamificationService()

@router.post("/quests/generate", response_model=dict)
def generate_nature_quest(
    request: GenerateQuestRequest,
    current_user: dict = Depends(get_optional_current_user),
):
    """Generates a 2-minute daily village observation micro-challenge for a concept."""
    result = service.generate_nature_quest(
        concept_code=request.concept_code,
        target_language=request.target_language,
        target_dialect=request.target_dialect,
    )
    return success_response(result)

@router.post("/students/{student_id}/activity", response_model=dict)
def record_student_learning_activity(
    student_id: str,
    request: RecordActivityRequest,
    current_user: dict = Depends(get_optional_current_user),
):
    """Records completion of a lesson, quiz, or nature quest, awards XP, and unlocks badges."""
    progress = service.record_activity(
        student_id=student_id,
        student_name=request.student_name,
        school_id=request.school_id,
        grade_level=request.grade_level,
        activity_type=request.activity_type,
        concept_code=request.concept_code,
    )
    return success_response(progress)

@router.get("/students/{student_id}/portfolio", response_model=dict)
def get_student_portfolio(
    student_id: str,
    current_user: dict = Depends(get_optional_current_user),
):
    """Retrieves student's complete gamification profile, level, streak, and unlocked badges."""
    portfolio_data = service.get_student_portfolio(student_id=student_id)
    return success_response(portfolio_data)

@router.post("/flashcards/generate", response_model=dict)
def generate_bilingual_flashcards(
    request: GenerateFlashcardsRequest,
    current_user: dict = Depends(get_optional_current_user),
):
    """Generates a multilingual visual flashcard deck with village iconography and printable HTML sheet."""
    deck = service.generate_flashcards(
        concept_code=request.concept_code,
        target_language=request.target_language,
        target_dialect=request.target_dialect,
    )
    return success_response(deck)

@router.get("/flashcards/deck/{filename}")
def view_printable_deck_html(filename: str):
    """Serves the printable HTML flashcard sheet."""
    html_content = service.resolve_flashcard_html(filename)
    return HTMLResponse(content=html_content)

@router.get("/leaderboards/{school_id}", response_model=dict)
def get_school_leaderboard(
    school_id: str,
    current_user: dict = Depends(get_optional_current_user),
):
    """Returns the cooperative learning leaderboard for a rural school."""
    leaderboard = service.get_school_leaderboard(school_id=school_id)
    return success_response({
        "school_id": school_id,
        "total_students": len(leaderboard),
        "leaderboard": leaderboard,
    })
