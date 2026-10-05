from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class GenerateQuizRequest(BaseModel):
    concept_code: str = Field(..., description="Concept code, e.g. 'EVS-G3-WAT-01'")
    target_language: str = Field("hi", description="Target mother tongue, e.g. 'hi', 'bn', 'or'")
    target_dialect: Optional[str] = Field(None, description="Optional tribal dialect: 'gon', 'sat'")
    grade_level: int = Field(3, ge=1, le=5, description="Grade level (1-5)")

class QuizQuestionItem(BaseModel):
    question_id: str
    question_type: str
    question_text: str
    options: List[str] = []
    blooms_level: str
    difficulty_level: int
    cultural_anchor: Optional[str] = None

class GenerateQuizResponse(BaseModel):
    quiz_id: str
    concept_code: str
    concept_name: Optional[str] = None
    grade_level: int
    target_language: str
    target_dialect: Optional[str] = None
    total_questions: int
    questions: List[QuizQuestionItem]

class SubmitQuizRequest(BaseModel):
    student_id: Optional[str] = Field(None, description="Student identifier (defaults to authenticated user if student)")
    answers: Dict[str, str] = Field(..., description="Map of question_id to selected answer option, e.g. {'Q1': 'A', 'Q2': 'C'}")

class SubmitQuizResponse(BaseModel):
    submission_id: str
    quiz_id: str
    student_id: str
    concept_code: str
    score_pct: float
    total_questions: int
    correct_count: int
    answers_evaluation: List[Dict[str, Any]]
    needs_remedial: bool
    gaps: List[Dict[str, Any]] = []
    remedial_concepts: List[str] = []
    teacher_insight: Optional[str] = None

class StudentAssessmentHistoryResponse(BaseModel):
    student_id: str
    total_submissions: int
    history: List[Dict[str, Any]]

class TeacherConceptReportResponse(BaseModel):
    report: Dict[str, Any]
