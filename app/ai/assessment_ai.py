from typing import Optional, Dict, Any, List
from app.ai.aaroh_ai_adapter import ai_adapter
from app.core.exceptions import AIProcessingError
from app.core.logging import logger

class AssessmentAI:
    def __init__(self):
        self.pipeline = ai_adapter.quiz_pipeline

    def generate_quiz(
        self,
        concept_code: str,
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
        grade_level: int = 3,
    ):
        try:
            return self.pipeline.generate_quiz_for_concept(
                concept_code=concept_code,
                target_language=target_language,
                target_dialect=target_dialect,
                grade_level=grade_level,
            )
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            raise AIProcessingError(message=f"Quiz generation failed: {str(e)}")

    def submit_and_assess_quiz(
        self,
        quiz_id: str,
        student_id: str,
        answers: Dict[str, str],
    ):
        try:
            return self.pipeline.submit_and_assess_quiz(
                quiz_id=quiz_id,
                student_id=student_id,
                answers=answers,
            )
        except Exception as e:
            logger.error(f"Assessment evaluation failed: {e}")
            raise AIProcessingError(message=f"Assessment evaluation failed: {str(e)}")

    def get_student_history(self, student_id: str) -> List[Dict[str, Any]]:
        try:
            return self.pipeline.get_student_history(student_id=student_id)
        except Exception as e:
            logger.error(f"Failed to fetch student history: {e}")
            raise AIProcessingError(message=f"Failed to fetch student history: {str(e)}")

    def get_class_report(self, concept_code: str) -> Dict[str, Any]:
        try:
            return self.pipeline.get_class_report(concept_code=concept_code)
        except Exception as e:
            logger.error(f"Failed to generate class report: {e}")
            raise AIProcessingError(message=f"Failed to generate class report: {str(e)}")

assessment_ai = AssessmentAI()
