from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.postgres import get_db
from app.services.assignment_service import AssignmentService
from app.schemas.assignment_schemas import (
    AssignmentGenerateRequest,
    AssignmentSubmitRequest,
    AssignmentResponse,
    AssignmentSubmitResponse,
)
from app.schemas.common_schemas import success_response
from app.api.deps import require_roles, get_current_user, get_optional_current_user
from app.core.jwt import UserRole

router = APIRouter(prefix="/assignments", tags=["Worksheets & Assignments"])

@router.post("/generate", response_model=dict, status_code=status.HTTP_201_CREATED)
def generate_assignment(
    request: AssignmentGenerateRequest,
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(require_roles([UserRole.TEACHER, UserRole.ADMIN, UserRole.DISTRICT_ADMIN])),
):
    """Generates a real curriculum-anchored worksheet assignment with local examples and translation."""
    service = AssignmentService(pg_session)
    result = service.generate_assignment(
        document_id=request.document_id,
        concept_code=request.concept_code,
        grade=request.grade,
        subject=request.subject,
        target_language=request.target_language,
        target_dialect=request.target_dialect,
        number_of_questions=request.number_of_questions,
        difficulty=request.difficulty,
        title=request.title,
    )
    return success_response(result)

@router.get("", response_model=dict)
def list_assignments(
    subject: Optional[str] = Query(None),
    grade: Optional[int] = Query(None),
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_current_user),
):
    """Lists generated assignments."""
    service = AssignmentService(pg_session)
    assignments = service.list_assignments(subject=subject, grade=grade)
    return success_response(assignments)

@router.get("/{assignment_id}", response_model=dict)
def get_assignment(
    assignment_id: str,
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_current_user),
):
    """Retrieves full assignment details and questions."""
    service = AssignmentService(pg_session)
    asgn = service.get_assignment(assignment_id=assignment_id)
    return success_response(asgn)

@router.post("/{assignment_id}/submit", response_model=dict)
def submit_assignment(
    assignment_id: str,
    request: AssignmentSubmitRequest,
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_current_user),
):
    """Submits student answers to assignment and scores against concept rubric."""
    service = AssignmentService(pg_session)
    result = service.submit_assignment(
        assignment_id=assignment_id,
        student_id=request.student_id,
        answers=request.answers,
        student_name=request.student_name,
    )
    return success_response(result)

@router.get("/{assignment_id}/pdf")
def download_assignment_pdf(
    assignment_id: str,
    pg_session: Session = Depends(get_db),
):
    """Downloads printable assignment worksheet (HTML / PDF)."""
    service = AssignmentService(pg_session)
    file_path = service.get_assignment_pdf_path(assignment_id)
    media_type = "text/html" if file_path.suffix == ".html" else "application/pdf"
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=f"AAROH_Worksheet_{assignment_id}{file_path.suffix}",
    )
