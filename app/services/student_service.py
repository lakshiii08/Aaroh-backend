import uuid
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.repositories.student_repository import StudentRepository
from app.models.mongo_models import UserDocument, StudentDocument
from app.models.pg_models import StudentProfileModel
from app.core.security import generate_secure_password, hash_password
from app.core.jwt import UserRole
from app.core.exceptions import DuplicateResourceError, NotFoundError, ForbiddenError
from app.core.logging import logger

class StudentService:
    def __init__(self, db: AsyncIOMotorDatabase, pg_session: Session):
        self.db = db
        self.pg_session = pg_session
        self.user_repo = UserRepository(db)
        self.student_repo = StudentRepository(db)

    async def create_student_by_teacher(
        self,
        teacher_user_id: str,
        teacher_school_id: str,
        student_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Creates a student account initiated by a teacher.
        
        1. Validates roll number uniqueness within (school_id, grade_level)
        2. Generates cryptographically secure random password
        3. Hashes password with bcrypt (never plaintext in DB)
        4. Inserts into MongoDB 'users' and 'students'
        5. Creates student learning profile in PostgreSQL 'student_profiles'
        6. Returns credentials ONCE in response.
        """
        school_id = student_data.get("school_id") or teacher_school_id
        roll_number = str(student_data["roll_number"]).strip()
        grade_level = int(student_data["class_grade"])
        name = student_data["name"].strip()
        village = student_data.get("village", "Bhamragad")
        section = student_data.get("section", "A")

        # Check roll number uniqueness in this school and grade
        existing_student = await self.student_repo.find_by_roll_and_school(
            school_id=school_id,
            grade_level=grade_level,
            roll_number=roll_number,
        )
        if existing_student:
            raise DuplicateResourceError(
                message=f"Roll number '{roll_number}' is already assigned to a student in Grade {grade_level} of this school."
            )

        # Generate secure random password (never predictable)
        temporary_password = generate_secure_password(8)
        hashed_pwd = hash_password(temporary_password)

        student_id = f"stu_{uuid.uuid4().hex[:12]}"
        user_id = f"u_{student_id}"

        # 1. MongoDB User Document (Authentication)
        user_doc = UserDocument(
            user_id=user_id,
            email=None,
            hashed_password=hashed_pwd,
            role=UserRole.STUDENT,
            school_id=school_id,
            district_id=student_data.get("district_id", "CG_BASTAR_01"),
            name=name,
            is_active=True,
            must_change_password=True,
        )
        await self.user_repo.create_user(user_doc)

        # 2. MongoDB Student Document (Identity & School Context)
        student_doc = StudentDocument(
            student_id=student_id,
            user_id=user_id,
            roll_number=roll_number,
            school_id=school_id,
            district_id=student_data.get("district_id", "CG_BASTAR_01"),
            grade_level=grade_level,
            section=section,
            village=village,
            created_by_teacher_id=teacher_user_id,
        )
        await self.student_repo.create_student(student_doc)

        # 3. PostgreSQL Learning Profile (Curriculum, XP, Mastery, Analytics)
        try:
            pg_profile = StudentProfileModel(
                student_id=student_id,
                student_name=name,
                school_id=school_id,
                grade_level=grade_level,
                total_xp=0,
                level=1,
                current_streak_days=1,
                completed_quests_count=0,
                concepts_mastered=[],
            )
            self.pg_session.add(pg_profile)
            self.pg_session.commit()
            logger.info(f"Created student PostgreSQL learning profile for student_id: {student_id}")
        except Exception as pg_err:
            self.pg_session.rollback()
            logger.error(f"Failed to create student learning profile in PostgreSQL: {pg_err}")

        # Return generated credentials once
        return {
            "student_id": student_id,
            "name": name,
            "roll_number": roll_number,
            "login_id": roll_number,
            "temporary_password": temporary_password,
            "school_id": school_id,
            "grade_level": grade_level,
            "message": "Student created successfully. Secure temporary password displayed once.",
        }

    async def reset_student_password(
        self,
        teacher_school_id: str,
        student_id: str,
    ) -> Dict[str, Any]:
        """Teacher resets a student's password and generates a fresh temporary password."""
        student = await self.student_repo.find_by_student_id(student_id)
        if not student:
            raise NotFoundError(message="Student not found", code="STUDENT_NOT_FOUND")

        if student["school_id"] != teacher_school_id:
            raise ForbiddenError(message="Cannot reset password of a student from another school.")

        new_password = generate_secure_password(8)
        hashed_pwd = hash_password(new_password)

        await self.user_repo.update_password(student["user_id"], hashed_pwd)

        return {
            "student_id": student_id,
            "roll_number": student["roll_number"],
            "login_id": student["roll_number"],
            "temporary_password": new_password,
            "message": "Password reset successfully. New temporary password displayed once.",
        }

    async def list_students(
        self,
        school_id: str,
        grade_level: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Lists students for a teacher's school, enriched with gamification stats from PostgreSQL."""
        students_mongo = await self.student_repo.list_students_by_school(school_id, grade_level)
        result = []
        for s in students_mongo:
            # Query PostgreSQL profile for XP and Streak
            pg_prof = self.pg_session.query(StudentProfileModel).filter_by(student_id=s["student_id"]).first()
            user = await self.user_repo.find_by_user_id(s["user_id"])
            result.append({
                "student_id": s["student_id"],
                "name": user["name"] if user else "Student",
                "roll_number": s["roll_number"],
                "grade_level": s["grade_level"],
                "section": s.get("section"),
                "village": s.get("village"),
                "school_id": s["school_id"],
                "total_xp": pg_prof.total_xp if pg_prof else 0,
                "level": pg_prof.level if pg_prof else 1,
                "current_streak_days": pg_prof.current_streak_days if pg_prof else 1,
                "created_at": s["created_at"].isoformat() if s.get("created_at") else "",
            })
        return result

    async def get_student_details(
        self,
        student_id: str,
        current_user_school_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> Dict[str, Any]:
        """Retrieves single student profile with complete isolation checks."""
        student = await self.student_repo.find_by_student_id(student_id)
        if not student:
            raise NotFoundError(message="Student not found", code="STUDENT_NOT_FOUND")

        if not is_admin and current_user_school_id and student["school_id"] != current_user_school_id:
            raise ForbiddenError(message="Access denied to student from another school.")

        user = await self.user_repo.find_by_user_id(student["user_id"])
        pg_prof = self.pg_session.query(StudentProfileModel).filter_by(student_id=student_id).first()

        return {
            "student_id": student["student_id"],
            "user_id": student["user_id"],
            "name": user["name"] if user else "Student",
            "roll_number": student["roll_number"],
            "grade_level": student["grade_level"],
            "section": student.get("section"),
            "village": student.get("village"),
            "school_id": student["school_id"],
            "total_xp": pg_prof.total_xp if pg_prof else 0,
            "level": pg_prof.level if pg_prof else 1,
            "current_streak_days": pg_prof.current_streak_days if pg_prof else 1,
            "concepts_mastered": pg_prof.concepts_mastered if pg_prof else [],
            "badges_count": 0,
            "created_at": student["created_at"].isoformat() if student.get("created_at") else "",
        }
