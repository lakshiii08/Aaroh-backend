from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class GenerateQuestRequest(BaseModel):
    concept_code: str = Field(..., description="Concept code, e.g. 'EVS-G3-WAT-01'")
    target_language: str = Field("hi", description="Instruction language")
    target_dialect: Optional[str] = Field(None, description="Tribal dialect, e.g. 'gon'")

class QuestResponse(BaseModel):
    quest_id: str
    concept_code: str
    title: str
    story_mission: str
    action_prompt: str
    reward_xp: int
    badge_unlock: Optional[str] = None

class RecordActivityRequest(BaseModel):
    student_name: str = Field("Student", description="Student full name")
    school_id: str = Field("rural_primary_01", description="School code")
    grade_level: int = Field(3, description="Grade level (1-5)")
    activity_type: str = Field("lesson", description="'lesson' | 'quiz_pass' | 'quest'")
    concept_code: Optional[str] = Field(None, description="Concept code completed")

class StudentPortfolioResponse(BaseModel):
    portfolio: Dict[str, Any]

class GenerateFlashcardsRequest(BaseModel):
    concept_code: str = Field(..., description="Concept code")
    target_language: str = Field("hi", description="Instruction language")
    target_dialect: Optional[str] = Field("gon", description="Mother-tongue dialect")

class FlashcardDeckResponse(BaseModel):
    concept_code: str
    concept_name: str
    total_cards: int
    printable_deck_url: str
    cards: List[Dict[str, Any]]

class SchoolLeaderboardResponse(BaseModel):
    school_id: str
    total_students: int
    leaderboard: List[Dict[str, Any]]
