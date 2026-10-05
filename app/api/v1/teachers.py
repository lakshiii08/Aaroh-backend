from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session
from app.core.mongodb import get_mongo_db
from app.core.postgres import get_db
from app.api.deps import require_roles, get_current_user
from app.core.jwt import UserRole
from app.services.student_service import StudentService
from app.schemas.student_schemas import CreateStudentRequest
from app.schemas.common_schemas import success_response

router = APIRouter(prefix="/teachers", tags=["Teacher Management"])

@router.post(
    "/students",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([UserRole.TEACHER, UserRole.ADMIN]))],
)
async def create_student(
    request: CreateStudentRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    pg_session: Session = Depends(get_db),
):
    """Teacher adds a new student to their classroom.
    
    1. Validates roll number uniqueness within the school and class.
    2. Auto-generates a secure, cryptographically random temporary password.
    3. Hashes password securely (never stored in plaintext).
    4. Stores identity in MongoDB & creates learning profile in PostgreSQL.
    5. Returns student login credentials ONCE to display to the teacher.
    """
    service = StudentService(db, pg_session)
    result = await service.create_student_by_teacher(
        teacher_user_id=current_user["user_id"],
        teacher_school_id=current_user.get("school_id", "SCH_001"),
        student_data=request.model_dump(),
    )
    return success_response(result)

@router.get(
    "/students",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.TEACHER, UserRole.ADMIN]))],
)
async def list_students(
    grade_level: Optional[int] = Query(None, description="Filter by grade level (1-5)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    pg_session: Session = Depends(get_db),
):
    """Lists all students belonging to the authenticated teacher's school."""
    service = StudentService(db, pg_session)
    students = await service.list_students(
        school_id=current_user.get("school_id", "SCH_001"),
        grade_level=grade_level,
    )
    return success_response(students)

@router.get(
    "/students/{student_id}",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.TEACHER, UserRole.ADMIN, UserRole.DISTRICT_ADMIN]))],
)
async def get_student_details(
    student_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    pg_session: Session = Depends(get_db),
):
    """Retrieves full details and learning progress of a student within teacher's school."""
    service = StudentService(db, pg_session)
    student = await service.get_student_details(
        student_id=student_id,
        current_user_school_id=current_user.get("school_id"),
        is_admin=current_user.get("role") in [UserRole.ADMIN, UserRole.DISTRICT_ADMIN],
    )
    return success_response(student)

@router.post(
    "/students/{student_id}/reset-password",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.TEACHER, UserRole.ADMIN]))],
)
async def reset_student_password(
    student_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    pg_session: Session = Depends(get_db),
):
    """Resets a student's password and returns the new temporary credentials once."""
    service = StudentService(db, pg_session)
    result = await service.reset_student_password(
        teacher_school_id=current_user.get("school_id", "SCH_001"),
        student_id=student_id,
    )
    return success_response(result)
