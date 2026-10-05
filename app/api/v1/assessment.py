from fastapi import APIRouter, Depends
from app.services.assessment_service import AssessmentService
from app.schemas.assessment_schemas import (
    GenerateQuizRequest,
    SubmitQuizRequest,
)
from app.schemas.common_schemas import success_response
from app.api.deps import require_roles, get_current_user, get_optional_current_user
from app.core.jwt import UserRole

router = APIRouter(prefix="/assessment", tags=["Quiz Generation & Student Assessment"])

service = AssessmentService()

@router.post("/quizzes/generate", response_model=dict)
def generate_quiz(
    request: GenerateQuizRequest,
    current_user: dict = Depends(get_optional_current_user),
):
    """Generates a culturally-localized pedagogical quiz for a curriculum concept in the child's mother tongue.
    - 3 Multiple Choice Questions
    - 1 Fill-in-the-blank question
    - 1 True/False question
    """
    result = service.generate_quiz(
        concept_code=request.concept_code,
        target_language=request.target_language,
        target_dialect=request.target_dialect,
        grade_level=request.grade_level,
    )
    return success_response(result)

@router.post("/quizzes/{quiz_id}/submit", response_model=dict)
def submit_quiz_and_assess(
    quiz_id: str,
    request: SubmitQuizRequest,
    current_user: dict = Depends(get_current_user),
):
    """Submits student answers, calculates score, identifies concept-level gaps,
    and returns personalized remedial lessons + teacher insights.
    """
    student_id = request.student_id or current_user.get("user_id")
    result = service.submit_quiz_and_assess(
        quiz_id=quiz_id,
        student_id=student_id,
        answers=request.answers,
        current_user=current_user,
    )
    return success_response(result)

@router.get("/students/{student_id}/history", response_model=dict)
def get_student_assessment_history(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retrieves all past quiz submissions and learning progress for a specific student."""
    history = service.get_student_history(student_id=student_id, current_user=current_user)
    return success_response({
        "student_id": student_id,
        "total_submissions": len(history),
        "history": history,
    })

@router.get(
    "/teachers/reports/{concept_code}",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.TEACHER, UserRole.ADMIN, UserRole.DISTRICT_ADMIN]))],
)
def get_teacher_concept_report(
    concept_code: str,
    current_user: dict = Depends(get_current_user),
):
    """Generates an aggregated class report and actionable recommendations for teachers."""
    report = service.get_teacher_concept_report(concept_code=concept_code)
    return success_response(report)
