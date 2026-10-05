from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session
from app.core.mongodb import get_mongo_db
from app.core.postgres import get_db
from app.api.deps import require_roles, get_current_user
from app.core.jwt import UserRole
from app.services.student_service import StudentService
from app.schemas.common_schemas import success_response
from app.core.exceptions import ForbiddenError

router = APIRouter(prefix="/students", tags=["Student Profile"])

@router.get(
    "/{student_id}",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN]))],
)
async def get_student_profile(
    student_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    pg_session: Session = Depends(get_db),
):
    """Retrieves student profile.
    Students can access ONLY their own profile data.
    """
    user_id = current_user["user_id"]
    role = current_user["role"]

    if role == UserRole.STUDENT and student_id != user_id and not user_id.endswith(student_id):
        raise ForbiddenError(message="Students may access only their own profile.", code="FORBIDDEN_PROFILE_ACCESS")

    service = StudentService(db, pg_session)
    student = await service.get_student_details(
        student_id=student_id,
        current_user_school_id=current_user.get("school_id"),
        is_admin=role in [UserRole.ADMIN, UserRole.DISTRICT_ADMIN],
    )
    return success_response(student)
