import os
import sys
import asyncio
import secrets
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.mongodb import MongoManager
from app.core.postgres import postgres_manager
from app.core.security import hash_password
from app.models.mongo_models import UserDocument, TeacherDocument, SchoolDocument
from app.core.jwt import UserRole
from app.core.logging import logger

async def seed_demo_teacher():
    """Seeds ONLY an explicitly configured development demo teacher account.
    
    Creates NO fake students, NO fake quizzes, NO fake analytics, NO fake assignments.
    """
    logger.info("Initializing demo teacher seed script for AAROH...")
    await MongoManager.connect()
    db = MongoManager.get_database()

    users_col = db["users"]
    teachers_col = db["teachers"]
    schools_col = db["schools"]

    demo_school_id = os.getenv("AAROH_DEMO_SCHOOL_ID", "SCH_LOCAL_DEMO")
    demo_school_code = os.getenv("AAROH_DEMO_SCHOOL_CODE", "LOCAL-DEMO")
    demo_district_id = os.getenv("AAROH_DEMO_DISTRICT_ID", "DIST_LOCAL_DEMO")
    demo_identifier = os.getenv("AAROH_DEMO_TEACHER_EMAIL", "demo.teacher.local@aaroh.local")
    demo_password = os.getenv("AAROH_DEMO_TEACHER_PASSWORD") or secrets.token_urlsafe(12)

    # 1. Ensure school exists for the configured demo teacher
    existing_school = await schools_col.find_one({"school_id": demo_school_id})
    if not existing_school:
        school = SchoolDocument(
            school_id=demo_school_id,
            school_code=demo_school_code,
            school_name=os.getenv("AAROH_DEMO_SCHOOL_NAME", "Local Demo School"),
            district_id=demo_district_id,
            village=os.getenv("AAROH_DEMO_VILLAGE", "Local Demo Village"),
            state="Chhattisgarh",
            total_students=0,
        )
        await schools_col.insert_one(school.model_dump())
        logger.info(f"Created demo school context: {school.school_name} (Code: {school.school_code})")

    existing_user = await users_col.find_one({"email": demo_identifier})
    if existing_user:
        logger.info(f"Demo teacher account '{demo_identifier}' already exists. Updating credentials...")
        await users_col.update_one(
            {"email": demo_identifier},
            {"$set": {
                "hashed_password": hash_password(demo_password),
                "is_active": True,
                "role": UserRole.TEACHER,
                "school_id": demo_school_id,
                "district_id": demo_district_id,
                "name": os.getenv("AAROH_DEMO_TEACHER_NAME", "Local Demo Teacher"),
                "is_demo": True,
            }}
        )
    else:
        user_id = "teacher_demo_123"
        user_doc = UserDocument(
            user_id=user_id,
            email=demo_identifier,
            hashed_password=hash_password(demo_password),
            role=UserRole.TEACHER,
            school_id=demo_school_id,
            district_id=demo_district_id,
            name=os.getenv("AAROH_DEMO_TEACHER_NAME", "Local Demo Teacher"),
            is_active=True,
            is_demo=True,
        )
        await users_col.insert_one(user_doc.model_dump())

        teacher_doc = TeacherDocument(
            teacher_id="tprof_demo_123",
            user_id=user_id,
            school_id=demo_school_id,
            district_id=demo_district_id,
            employee_id="DEMO_TCH_01",
            assigned_grades=[1, 2, 3, 4, 5],
            subjects=["Science", "Mathematics", "Environmental Studies", "Language"],
        )
        await teachers_col.insert_one(teacher_doc.model_dump())
        logger.info(f"Created demo teacher account '{demo_identifier}' successfully.")

    logger.info("=" * 60)
    logger.info("DEMO TEACHER CREDENTIALS READY:")
    logger.info(f"  Identifier / Email: {demo_identifier}")
    logger.info(f"  Password:           {demo_password}")
    logger.info(f"  Role:               {UserRole.TEACHER}")
    logger.info("  Demo Flag:          True")
    logger.info("=" * 60)
    logger.info("Zero fake students, zero fake quizzes, and zero fake analytics seeded.")

    await MongoManager.disconnect()
    logger.info("Seed demo process complete.")

if __name__ == "__main__":
    asyncio.run(seed_demo_teacher())
