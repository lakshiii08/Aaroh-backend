from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class GenerateLessonPlanRequest(BaseModel):
    concept_code: str = Field(..., description="Concept code, e.g. 'EVS-G3-WAT-01'")
    grade_level: int = Field(3, ge=1, le=5, description="Primary class grade level")
    target_language: str = Field("hi", description="Instruction language")
    target_dialect: Optional[str] = Field(None, description="Optional dialect: 'gon', 'sat'")
    duration_mins: int = Field(45, description="Class duration in minutes")

class LessonPlanResponse(BaseModel):
    plan_id: str
    title: str
    grade_level: int
    target_language: str
    time_allocation_mins: Dict[str, int]
    multigrade_strategies: Dict[str, str]
    blackboard_activity: str
    teaching_aids: List[str]
    hands_on_experiments: List[str]
    homework_village_inquiry: str

class RemedialAidRequest(BaseModel):
    concept_code: str = Field(..., description="Concept code")
    weak_bloom_level: str = Field("Understand", description="Bloom's level where gap was detected")
    target_language: str = Field("hi", description="Instruction language")

class RemedialAidResponse(BaseModel):
    aid_id: str
    concept_code: str
    concept_name: str
    identified_gap_summary: str
    simplified_activity: str
    story_analogy: str
    check_questions: List[str]
    printable_guide: str

class ExportOfflineBundleRequest(BaseModel):
    grade_level: int = Field(3, ge=1, le=5, description="Grade level to export")
    subject: str = Field("Environmental Studies", description="Subject name")
    target_language: str = Field("hi", description="Target language")
    target_dialect: Optional[str] = Field(None, description="Target dialect")

class ExportOfflineBundleResponse(BaseModel):
    package_id: str
    package_name: str
    grade_level: int
    subject: str
    target_language: str
    total_lessons: int
    total_quizzes: int
    total_audio_files: int
    package_size_bytes: int
    download_url: str

class EdgeSyncBatchRequest(BaseModel):
    batch_id: str = Field(..., description="Unique client sync batch ID for idempotency")
    device_id: str = Field(..., description="Hardware kiosk/tablet ID")
    school_id: str = Field(..., description="School code")
    submissions: List[Dict[str, Any]] = Field(..., description="Offline completed student quiz attempts")

class EdgeSyncBatchResponse(BaseModel):
    batch_id: str
    device_id: str
    school_id: str
    total_synced_submissions: int
    synced_at: str

class MasteryHeatmapResponse(BaseModel):
    total_concepts: int
    mastery_heatmap: List[Dict[str, Any]]
