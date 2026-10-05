import uuid
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.user_repository import UserRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.school_repository import SchoolRepository
from app.models.mongo_models import UserDocument, StudentDocument, TeacherDocument, SchoolDocument, SessionDocument
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token, create_refresh_token, decode_token, UserRole
from app.core.exceptions import UnauthorizedError, DuplicateResourceError, NotFoundError, ForbiddenError
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.core.logging import logger

class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.user_repo = UserRepository(db)
        self.student_repo = StudentRepository(db)
        self.school_repo = SchoolRepository(db)
        self.sessions_col = db["sessions"]
        self.teachers_col = db["teachers"]

    async def signup_teacher(self, signup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Registers a new verified Teacher account in MongoDB."""
        email = signup_data["email"].lower().strip()
        existing = await self.user_repo.find_by_email(email)
        if existing:
            raise DuplicateResourceError(message=f"An account with email '{email}' already exists.")

        user_id = f"teacher_{uuid.uuid4().hex[:12]}"
        hashed_pwd = hash_password(signup_data["password"])

        # Create user identity document
        user_doc = UserDocument(
            user_id=user_id,
            email=email,
            hashed_password=hashed_pwd,
            role=UserRole.TEACHER,
            school_id=signup_data["school_id"],
            district_id=signup_data.get("district_id", "CG_BASTAR_01"),
            name=signup_data["name"],
            is_active=True,
        )
        await self.user_repo.create_user(user_doc)

        # Create teacher profile document
        teacher_id = f"tprof_{uuid.uuid4().hex[:10]}"
        teacher_doc = TeacherDocument(
            teacher_id=teacher_id,
            user_id=user_id,
            school_id=signup_data["school_id"],
            district_id=signup_data.get("district_id", "CG_BASTAR_01"),
            employee_id=signup_data.get("employee_id"),
            assigned_grades=signup_data.get("assigned_grades", [3, 4, 5]),
            subjects=signup_data.get("subjects", ["Environmental Studies"]),
        )
        await self.teachers_col.insert_one(teacher_doc.model_dump())

        # Generate tokens
        access_token = create_access_token(
            user_id=user_id,
            role=UserRole.TEACHER,
            school_id=user_doc.school_id,
            district_id=user_doc.district_id,
            name=user_doc.name,
        )
        refresh_token = create_refresh_token(user_id=user_id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user_id,
            "role": UserRole.TEACHER,
            "name": user_doc.name,
            "school_id": user_doc.school_id,
            "district_id": user_doc.district_id,
            "must_change_password": False,
        }

    async def login(self, login_id: str, password: str, school_code: Optional[str] = None) -> Dict[str, Any]:
        """Authenticates either:
        1. Teacher / Admin / Parent using Email
        2. Student using Roll Number (Login ID) + School Code + Auto-generated password
        """
        login_id_clean = login_id.strip()
        await self._provision_demo_login_if_requested(login_id_clean, password, school_code)

        # Check if login_id looks like an email or username identifier
        if "@" in login_id_clean:
            user = await self.user_repo.find_by_email(login_id_clean)

            if not user:
                raise UnauthorizedError(message="Invalid credentials", code="INVALID_CREDENTIALS")

            if not verify_password(password, user["hashed_password"]):
                raise UnauthorizedError(message="Invalid credentials", code="INVALID_CREDENTIALS")

            await self.user_repo.update_last_login(user["user_id"])

            access_token = create_access_token(
                user_id=user["user_id"],
                role=user["role"],
                school_id=user.get("school_id"),
                district_id=user.get("district_id"),
                name=user.get("name"),
            )
            refresh_token = create_refresh_token(user_id=user["user_id"])

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user_id": user["user_id"],
                "role": user["role"],
                "name": user["name"],
                "school_id": user.get("school_id"),
                "district_id": user.get("district_id"),
                "roll_number": None,
                "must_change_password": user.get("must_change_password", False),
            }

        # Otherwise, authenticate as Student using Roll Number
        roll_number = login_id_clean

        # Resolve school
        school_id = None
        if school_code:
            school = await self.school_repo.find_by_school_code(school_code)
            if not school:
                # Try finding by school_id directly
                school = await self.school_repo.find_by_school_id(school_code)
            if school:
                school_id = school["school_id"]
            else:
                school_id = school_code

        # Search for student record matching roll number and resolved school
        query: Dict[str, Any] = {"roll_number": roll_number}
        if school_id:
            query["school_id"] = school_id

        student = await self.db["students"].find_one(query)
        user = None

        if not student:
            raise UnauthorizedError(
                message="Student account not found for this roll number and school context.",
                code="STUDENT_NOT_FOUND",
            )

        if not user:
            user = await self.user_repo.find_by_user_id(student["user_id"])
        if not user:
            raise UnauthorizedError(message="Student authentication credentials not found.", code="USER_NOT_FOUND")

        if not verify_password(password, user["hashed_password"]):
            raise UnauthorizedError(message="Invalid student roll number or password", code="INVALID_CREDENTIALS")

        await self.user_repo.update_last_login(user["user_id"])

        access_token = create_access_token(
            user_id=user["user_id"],
            role=UserRole.STUDENT,
            school_id=student["school_id"],
            district_id=student.get("district_id"),
            name=user["name"],
            extra_claims={"roll_number": roll_number, "grade_level": student.get("grade_level", 3)},
        )
        refresh_token = create_refresh_token(user_id=user["user_id"])

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user["user_id"],
            "role": UserRole.STUDENT,
            "name": user["name"],
            "school_id": student["school_id"],
            "district_id": student.get("district_id"),
            "roll_number": roll_number,
            "must_change_password": user.get("must_change_password", False),
        }

    async def _provision_demo_login_if_requested(
        self,
        login_id: str,
        password: str,
        school_code: Optional[str],
    ) -> None:
        if not settings.ENABLE_DEMO_LOGINS:
            return

        is_demo_teacher = (
            login_id.lower() == settings.DEMO_TEACHER_LOGIN.lower()
            and password == settings.DEMO_TEACHER_PASSWORD
        )
        is_demo_student = (
            login_id == settings.DEMO_STUDENT_ROLL_NUMBER
            and password == settings.DEMO_STUDENT_PASSWORD
            and (not school_code or school_code.upper().strip() in {
                settings.DEMO_SCHOOL_CODE.upper(),
                settings.DEMO_SCHOOL_ID.upper(),
            })
        )

        if not is_demo_teacher and not is_demo_student:
            return

        await self._ensure_demo_school()
        if is_demo_teacher:
            await self._ensure_demo_teacher()
        if is_demo_student:
            await self._ensure_demo_student()

    async def _ensure_demo_school(self) -> None:
        existing = await self.school_repo.find_by_school_id(settings.DEMO_SCHOOL_ID)
        if existing:
            return

        school = SchoolDocument(
            school_id=settings.DEMO_SCHOOL_ID,
            school_name="AAROH Demo Primary School",
            school_code=settings.DEMO_SCHOOL_CODE,
            district_id=settings.DEMO_DISTRICT_ID,
            village="Demo Village",
            state="Chhattisgarh",
            total_students=1,
        )
        await self.school_repo.create_school(school)

    async def _ensure_demo_teacher(self) -> None:
        existing = await self.user_repo.find_by_email(settings.DEMO_TEACHER_LOGIN)
        user_id = "demo_teacher_account"
        if existing:
            user_id = existing["user_id"]
            await self.db["users"].update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "hashed_password": hash_password(settings.DEMO_TEACHER_PASSWORD),
                        "role": UserRole.TEACHER,
                        "school_id": settings.DEMO_SCHOOL_ID,
                        "district_id": settings.DEMO_DISTRICT_ID,
                        "name": existing.get("name") or "Demo Teacher",
                        "is_active": True,
                        "is_demo": True,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
        else:
            user_doc = UserDocument(
                user_id=user_id,
                email=settings.DEMO_TEACHER_LOGIN,
                hashed_password=hash_password(settings.DEMO_TEACHER_PASSWORD),
                role=UserRole.TEACHER,
                school_id=settings.DEMO_SCHOOL_ID,
                district_id=settings.DEMO_DISTRICT_ID,
                name="Demo Teacher",
                is_active=True,
                is_demo=True,
            )
            await self.user_repo.create_user(user_doc)

        teacher_exists = await self.teachers_col.find_one({"user_id": user_id})
        if not teacher_exists:
            await self.teachers_col.insert_one(
                TeacherDocument(
                    teacher_id="demo_teacher_profile",
                    user_id=user_id,
                    school_id=settings.DEMO_SCHOOL_ID,
                    district_id=settings.DEMO_DISTRICT_ID,
                    employee_id="DEMO-TEACHER",
                    assigned_grades=[3, 4, 5],
                    subjects=["Environmental Studies", "Science", "Mathematics"],
                ).model_dump()
            )

    async def _ensure_demo_student(self) -> None:
        existing_student = await self.db["students"].find_one(
            {
                "school_id": settings.DEMO_SCHOOL_ID,
                "roll_number": settings.DEMO_STUDENT_ROLL_NUMBER,
            }
        )
        user_id = existing_student["user_id"] if existing_student else "demo_student_account"
        existing_user = await self.user_repo.find_by_user_id(user_id)
        if existing_user:
            await self.db["users"].update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "hashed_password": hash_password(settings.DEMO_STUDENT_PASSWORD),
                        "role": UserRole.STUDENT,
                        "school_id": settings.DEMO_SCHOOL_ID,
                        "district_id": settings.DEMO_DISTRICT_ID,
                        "name": existing_user.get("name") or "Demo Student",
                        "is_active": True,
                        "is_demo": True,
                        "must_change_password": False,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
        else:
            await self.user_repo.create_user(
                UserDocument(
                    user_id=user_id,
                    email=None,
                    hashed_password=hash_password(settings.DEMO_STUDENT_PASSWORD),
                    role=UserRole.STUDENT,
                    school_id=settings.DEMO_SCHOOL_ID,
                    district_id=settings.DEMO_DISTRICT_ID,
                    name="Demo Student",
                    is_active=True,
                    is_demo=True,
                    must_change_password=False,
                )
            )

        if existing_student:
            return

        await self.db["students"].insert_one(
            StudentDocument(
                student_id="demo_student_profile",
                user_id=user_id,
                roll_number=settings.DEMO_STUDENT_ROLL_NUMBER,
                school_id=settings.DEMO_SCHOOL_ID,
                district_id=settings.DEMO_DISTRICT_ID,
                grade_level=4,
                section="A",
                village="Demo Village",
                created_by_teacher_id="demo_teacher_account",
            ).model_dump()
        )

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refreshes an access token using a valid refresh token."""
        payload = decode_token(refresh_token)
        if payload.get("token_type") != "refresh":
            raise UnauthorizedError(message="Invalid token type for refresh", code="INVALID_TOKEN_TYPE")

        user_id = payload.get("sub") or payload.get("user_id")
        user = await self.user_repo.find_by_user_id(user_id)
        if not user or not user.get("is_active", True):
            raise UnauthorizedError(message="User account no longer active", code="USER_INACTIVE")

        # Check if student
        roll_number = None
        if user["role"] == UserRole.STUDENT:
            student = await self.student_repo.find_by_user_id(user_id)
            if student:
                roll_number = student.get("roll_number")

        access_token = create_access_token(
            user_id=user["user_id"],
            role=user["role"],
            school_id=user.get("school_id"),
            district_id=user.get("district_id"),
            name=user["name"],
            extra_claims={"roll_number": roll_number} if roll_number else None,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user["user_id"],
            "role": user["role"],
        }

    async def logout(self, user_id: str, token_jti: Optional[str] = None):
        """Invalidates user session / blacklists token."""
        if token_jti:
            session_doc = SessionDocument(
                session_id=str(uuid.uuid4()),
                token_jti=token_jti,
                user_id=user_id,
                is_revoked=True,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            )
            await self.sessions_col.insert_one(session_doc.model_dump())
        return {"status": "success", "message": "Successfully logged out"}
