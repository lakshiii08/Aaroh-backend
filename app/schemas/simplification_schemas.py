from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ConceptLocalizeRequest(BaseModel):
    target_language: str = Field("hi", description="Target language: 'hi', 'bn', 'or', 'mr'")
    target_dialect: Optional[str] = Field(None, description="Optional tribal dialect: 'gon', 'sat', 'hne', 'bhi'")
    grade_level: int = Field(3, ge=1, le=5, description="Grade level (1-5)")
    force_regenerate: bool = Field(False, description="Bypass cache and force fresh AI generation")

class LocalizedLessonContent(BaseModel):
    simplified_explanation: str
    local_analogies: List[str] = []
    story_narrative: str
    hands_on_activity: str
    reflection_questions: List[str] = []
    voice_script: str

class ConceptLocalizeResponse(BaseModel):
    cached: bool
    concept_code: str
    concept_name: str
    grade_level: int
    target_language: str
    target_dialect: Optional[str] = None
    lesson: LocalizedLessonContent
    cultural_anchors_used: List[str] = []
    source_chunks_preview: List[str] = []

class DocumentLocalizeRequest(BaseModel):
    target_language: str = Field("hi", description="Target language code")
    target_dialect: Optional[str] = Field(None, description="Optional tribal dialect")

class DocumentLocalizeResponse(BaseModel):
    document_id: str
    target_language: str
    target_dialect: Optional[str] = None
    total_lessons: int
    lessons: List[Dict[str, Any]]

class LangGraphAgentResponse(BaseModel):
    agent: str
    concept_code: str
    lesson: Dict[str, Any]

class CacheStatusResponse(BaseModel):
    total_cached_lessons: int
    entries: List[Dict[str, Any]]
