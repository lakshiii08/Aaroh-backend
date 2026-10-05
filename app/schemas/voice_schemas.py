from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class TextToSpeechRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize into mother-tongue speech")
    target_language: str = Field("hi", description="Language code: 'hi', 'bn', 'or', 'gon', 'sat'")
    target_dialect: Optional[str] = Field(None, description="Optional tribal dialect: 'gon', 'sat', 'hne'")
    section_name: str = Field("custom", description="Section identifier: 'story', 'activity', 'concept'")

class TextToSpeechResponse(BaseModel):
    segment_id: str
    section_name: str
    duration_seconds: float
    format: str
    voice_id: str
    audio_file_path: str
    stream_url: str

class VoiceLessonRequest(BaseModel):
    target_language: str = Field("hi", description="Target language code")
    target_dialect: Optional[str] = Field(None, description="Optional tribal dialect")
    grade_level: int = Field(3, ge=1, le=5, description="Grade level (1-5)")

class AudioSegmentItem(BaseModel):
    segment_id: str
    section_name: str
    duration_seconds: float
    audio_file_path: str
    stream_url: str

class VoiceLessonResponse(BaseModel):
    concept_code: str
    concept_name: Optional[str] = None
    target_language: str
    target_dialect: Optional[str] = None
    total_duration_seconds: float
    audio_segments: List[AudioSegmentItem]

class OralQuizAssessmentResponse(BaseModel):
    student_id: str
    question_id: str
    transcribed_speech: str
    expected_answer: str
    is_correct: bool
    confidence_score: float
    feedback_script: Optional[str] = None
    feedback_audio_url: Optional[str] = None
