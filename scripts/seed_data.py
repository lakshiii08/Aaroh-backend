import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.mongodb import MongoManager
from app.core.postgres import postgres_manager
from app.core.security import hash_password, generate_secure_password
from app.core.jwt import UserRole
from app.models.mongo_models import UserDocument, TeacherDocument, SchoolDocument, StudentDocument
from app.models.pg_models import StudentProfileModel, DistrictSchoolModel
from app.core.logging import logger

async def seed():
    logger.info("Initializing database seed process for AAROH...")
    db = await MongoManager.connect()
    pg_session = postgres_manager.get_session()

    # 1. Seed Demonstration School
    school_id = "SCH_BASTAR_01"
    school_code = "BASTAR01"
    existing_school = await db["schools"].find_one({"school_id": school_id})
    if not existing_school:
        school_doc = SchoolDocument(
            school_id=school_id,
            school_name="Government Tribal Primary Ashram School, Bhamragad",
            school_code=school_code,
            district_id="CG_BASTAR_01",
            village="Bhamragad",
            state="Chhattisgarh",
            total_students=45,
        )
        await db["schools"].insert_one(school_doc.model_dump())
        logger.info(f"Seeded school: {school_doc.school_name} (Code: {school_code})")

    # Sync school in PostgreSQL district_schools
    pg_school = pg_session.query(DistrictSchoolModel).filter_by(school_id=school_id).first()
    if not pg_school:
        pg_school = DistrictSchoolModel(
            school_id=school_id,
            school_name="Government Tribal Primary Ashram School, Bhamragad",
            district_code="CG_BASTAR_01",
            state_name="Chhattisgarh",
            block_name="Bastar Central",
            total_enrolled=45,
        )
        pg_session.add(pg_school)
        pg_session.commit()

    # 2. Seed Demonstration Teacher
    teacher_email = "teacher.bastar@aaroh.org"
    existing_teacher = await db["users"].find_one({"email": teacher_email})
    if not existing_teacher:
        teacher_pwd = "TeacherPassword2026!"
        teacher_user_id = "teacher_bhamragad_01"
        user_doc = UserDocument(
            user_id=teacher_user_id,
            email=teacher_email,
            hashed_password=hash_password(teacher_pwd),
            role=UserRole.TEACHER,
            school_id=school_id,
            district_id="CG_BASTAR_01",
            name="Smt. Savitri Mandavi",
            is_active=True,
        )
        await db["users"].insert_one(user_doc.model_dump())

        t_prof = TeacherDocument(
            teacher_id="tprof_001",
            user_id=teacher_user_id,
            school_id=school_id,
            district_id="CG_BASTAR_01",
            employee_id="CG-EDU-88421",
            assigned_grades=[3, 4, 5],
            subjects=["Environmental Studies", "Mathematics"],
        )
        await db["teachers"].insert_one(t_prof.model_dump())
        logger.info(f"Seeded Teacher: {teacher_email} (Password: {teacher_pwd})")

    # 3. Seed Demonstration District Admin
    admin_email = "admin.bastar@aaroh.org"
    existing_admin = await db["users"].find_one({"email": admin_email})
    if not existing_admin:
        admin_pwd = "DistrictAdmin2026!"
        admin_user_id = "admin_bastar_01"
        admin_doc = UserDocument(
            user_id=admin_user_id,
            email=admin_email,
            hashed_password=hash_password(admin_pwd),
            role=UserRole.DISTRICT_ADMIN,
            school_id=school_id,
            district_id="CG_BASTAR_01",
            name="Shri Alok Kashyap, IAS (District Collector)",
            is_active=True,
        )
        await db["users"].insert_one(admin_doc.model_dump())
        logger.info(f"Seeded District Admin: {admin_email} (Password: {admin_pwd})")

    # 4. Seed Demonstration Student with Teacher-Generated Password
    student_roll = "27"
    existing_student = await db["students"].find_one({"school_id": school_id, "roll_number": student_roll})
    if not existing_student:
        student_pwd = generate_secure_password(8)
        student_id = "student_rahul_murmu_01"
        user_id = f"u_{student_id}"

        stu_user = UserDocument(
            user_id=user_id,
            email=None,
            hashed_password=hash_password(student_pwd),
            role=UserRole.STUDENT,
            school_id=school_id,
            district_id="CG_BASTAR_01",
            name="Rahul Murmu",
            is_active=True,
            must_change_password=True,
        )
        await db["users"].insert_one(stu_user.model_dump())

        stu_doc = StudentDocument(
            student_id=student_id,
            user_id=user_id,
            roll_number=student_roll,
            school_id=school_id,
            district_id="CG_BASTAR_01",
            grade_level=3,
            section="A",
            village="Bhamragad",
            created_by_teacher_id="teacher_bhamragad_01",
        )
        await db["students"].insert_one(stu_doc.model_dump())

        # Sync PostgreSQL Learning Profile
        pg_prof = pg_session.query(StudentProfileModel).filter_by(student_id=student_id).first()
        if not pg_prof:
            pg_prof = StudentProfileModel(
                student_id=student_id,
                student_name="Rahul Murmu",
                school_id=school_id,
                grade_level=3,
                total_xp=250,
                level=2,
                current_streak_days=3,
                completed_quests_count=2,
                concepts_mastered=["EVS-G3-WAT-01"],
            )
            pg_session.add(pg_prof)
            pg_session.commit()

        logger.info("======================================================")
        logger.info("DEMO STUDENT CREDENTIALS (Teacher Created):")
        logger.info(f"Student Name: Rahul Murmu")
        logger.info(f"School Code:  {school_code}")
        logger.info(f"Roll Number (Login ID): {student_roll}")
        logger.info(f"Generated Password:     {student_pwd}")
        logger.info("======================================================")

    pg_session.close()
    await MongoManager.disconnect()
    logger.info("Seed process completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed())
