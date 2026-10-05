# Re-export all PostgreSQL SQLAlchemy models from Aaroh-AI core
from src.aaroh.database.models import (
    Base,
    DocumentModel,
    ConceptModel,
    ContentChunkModel,
    QuizModel,
    QuizSubmissionModel,
    AssessmentResultModel,
    VoiceLessonModel,
    OralQuizAttemptModel,
    LessonPlanModel,
    OfflinePackageModel,
    EdgeSyncLogModel,
    StudentProfileModel,
    StudentBadgeModel,
    LearningQuestModel,
    VisualFlashcardModel,
    InterventionPathwayModel,
    ParentVoiceAdvisoryModel,
    DistrictSchoolModel,
)

from sqlalchemy import Column, String, Integer, Float, Text, JSON, DateTime, ForeignKey
from datetime import datetime, timezone

class AssignmentModel(Base):
    __tablename__ = "assignments"

    id = Column(String(64), primary_key=True)
    title = Column(String(255), nullable=False)
    document_id = Column(String(64), nullable=True)
    concept_code = Column(String(64), nullable=True)
    subject = Column(String(100), default="Science")
    grade = Column(Integer, default=4)
    language = Column(String(10), default="sat")
    dialect = Column(String(20), nullable=True)
    difficulty = Column(String(20), default="medium")
    total_questions = Column(Integer, default=5)
    total_marks = Column(Integer, default=20)
    items_json = Column(JSON, default=list)
    pdf_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AssignmentSubmissionModel(Base):
    __tablename__ = "assignment_submissions"

    id = Column(String(64), primary_key=True)
    assignment_id = Column(String(64), ForeignKey("assignments.id"), nullable=False)
    student_id = Column(String(64), nullable=False)
    student_name = Column(String(150), nullable=True)
    answers_json = Column(JSON, default=dict)
    score = Column(Float, default=0.0)
    score_percentage = Column(Float, default=0.0)
    grade = Column(String(10), default="B")
    feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

__all__ = [
    "Base",
    "DocumentModel",
    "ConceptModel",
    "ContentChunkModel",
    "QuizModel",
    "QuizSubmissionModel",
    "AssessmentResultModel",
    "VoiceLessonModel",
    "OralQuizAttemptModel",
    "LessonPlanModel",
    "OfflinePackageModel",
    "EdgeSyncLogModel",
    "StudentProfileModel",
    "StudentBadgeModel",
    "LearningQuestModel",
    "VisualFlashcardModel",
    "InterventionPathwayModel",
    "ParentVoiceAdvisoryModel",
    "DistrictSchoolModel",
    "AssignmentModel",
    "AssignmentSubmissionModel",
]
