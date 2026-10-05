from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.mongo_models import StudentDocument

class StudentRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["students"]

    async def find_by_student_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"student_id": student_id})

    async def find_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"user_id": user_id})

    async def find_by_roll_and_school(
        self, school_id: str, grade_level: int, roll_number: str
    ) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({
            "school_id": school_id,
            "grade_level": grade_level,
            "roll_number": str(roll_number).strip(),
        })

    async def find_by_roll_in_school(
        self, school_id: str, roll_number: str
    ) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({
            "school_id": school_id,
            "roll_number": str(roll_number).strip(),
        })

    async def create_student(self, student: StudentDocument) -> Dict[str, Any]:
        doc = student.model_dump()
        doc["roll_number"] = str(doc["roll_number"]).strip()
        await self.collection.insert_one(doc)
        return doc

    async def list_students_by_school(
        self, school_id: str, grade_level: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"school_id": school_id}
        if grade_level is not None:
            query["grade_level"] = grade_level
        cursor = self.collection.find(query).sort("roll_number", 1)
        return await cursor.to_list(length=1000)
