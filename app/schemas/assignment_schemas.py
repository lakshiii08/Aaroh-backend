from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class AssignmentGenerateRequest(BaseModel):
    document_id: Optional[str] = Field(None, description="Ingested curriculum document ID")
    concept_code: Optional[str] = Field(None, description="Concept Code (e.g. EVS-G3-WAT-01)")
    grade: int = Field(default=4, ge=1, le=8, description="Class / Grade level")
    subject: str = Field(default="Science", description="Subject name")
    target_language: str = Field(default="sat", description="Language code: sat, hi, gon, hne, etc.")
    target_dialect: Optional[str] = Field(None, description="Tribal dialect code (e.g. gon, sat, hne)")
    number_of_questions: int = Field(default=5, ge=1, le=20, description="Total questions to generate")
    difficulty: str = Field(default="medium", description="Difficulty level: easy, medium, hard")
    title: Optional[str] = Field(None, description="Custom worksheet / assignment title")

class AssignmentItemSchema(BaseModel):
    id: str
    question_number: int
    item_type: Optional[str] = None
    prompt: Optional[str] = None
    question: str
    translated_question: Optional[str] = None
    translated_ol_chiki: Optional[str] = None
    concept_code: Optional[str] = None
    concept: str
    local_example: Optional[str] = None
    localized_context: Optional[str] = None
    source_document_id: Optional[str] = None
    source_document_title: Optional[str] = None
    source_excerpt: Optional[str] = None
    source_page: Optional[int] = None
    source_chunk_index: Optional[int] = None
    writing_space_lines: int = 4
    marks: int = 4
    correct_answer: Optional[str] = None
    suggested_answer: Optional[str] = None

class AssignmentResponse(BaseModel):
    id: str
    title: str
    subject: str
    grade: int
    language: str
    dialect: Optional[str] = None
    difficulty: str
    total_questions: int
    total_marks: int
    pdf_download_url: str
    created_at: str
    items: List[AssignmentItemSchema]

class AssignmentSubmitRequest(BaseModel):
    student_id: str
    answers: Dict[str, str] = Field(..., description="Mapping of question id to student written/spoken answer")
    student_name: Optional[str] = None

class AssignmentSubmitResponse(BaseModel):
    assignment_id: str
    student_id: str
    total_questions: int
    evaluated_score: float
    score_percentage: float
    grade: str
    mastery_status: str
    concept_gaps: List[str]
    feedback: str
