from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.mongo_models import SchoolDocument

class SchoolRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["schools"]

    async def find_by_school_id(self, school_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"school_id": school_id})

    async def find_by_school_code(self, school_code: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"school_code": school_code.upper().strip()})

    async def create_school(self, school: SchoolDocument) -> Dict[str, Any]:
        doc = school.model_dump()
        doc["school_code"] = doc["school_code"].upper().strip()
        await self.collection.insert_one(doc)
        return doc

    async def list_schools_by_district(self, district_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"district_id": district_id})
        return await cursor.to_list(length=500)
