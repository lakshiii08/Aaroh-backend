from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.mongo_models import UserDocument
from datetime import datetime, timezone

class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"email": email.lower().strip()})

    async def find_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"user_id": user_id})

    async def create_user(self, user: UserDocument) -> Dict[str, Any]:
        doc = user.model_dump()
        if doc.get("email"):
            doc["email"] = doc["email"].lower().strip()
        await self.collection.insert_one(doc)
        return doc

    async def update_password(self, user_id: str, hashed_password: str) -> bool:
        result = await self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "must_change_password": False,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return result.modified_count > 0

    async def update_last_login(self, user_id: str):
        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_login": datetime.now(timezone.utc)}},
        )
