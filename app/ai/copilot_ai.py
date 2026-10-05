from typing import Optional, List, Dict, Any
from app.ai.aaroh_ai_adapter import ai_adapter
from app.core.exceptions import AIProcessingError
from app.core.logging import logger

class CopilotAI:
    def __init__(self):
        self.pipeline = ai_adapter.copilot_pipeline

    def generate_lesson_plan(
        self,
        concept_code: str,
        grade_level: int = 3,
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
        duration_mins: int = 45,
    ):
        try:
            return self.pipeline.generate_lesson_plan(
                concept_code=concept_code,
                grade_level=grade_level,
                target_language=target_language,
                target_dialect=target_dialect,
                duration_mins=duration_mins,
            )
        except Exception as e:
            logger.error(f"Lesson plan generation failed: {e}")
            raise AIProcessingError(message=f"Lesson plan generation error: {str(e)}")

    def generate_remedial_aid(
        self,
        concept_code: str,
        weak_bloom_level: str = "Understand",
        target_language: str = "hi",
    ):
        try:
            return self.pipeline.generate_remedial_aid(
                concept_code=concept_code,
                weak_bloom_level=weak_bloom_level,
                target_language=target_language,
            )
        except Exception as e:
            logger.error(f"Remedial aid generation failed: {e}")
            raise AIProcessingError(message=f"Remedial aid generation error: {str(e)}")

    def export_offline_bundle(
        self,
        grade_level: int = 3,
        subject: str = "Environmental Studies",
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
    ):
        try:
            return self.pipeline.export_offline_bundle(
                grade_level=grade_level,
                subject=subject,
                target_language=target_language,
                target_dialect=target_dialect,
            )
        except Exception as e:
            logger.error(f"Offline bundle export failed: {e}")
            raise AIProcessingError(message=f"Offline bundle export error: {str(e)}")

    def sync_offline_attempts(self, batch_payload: Dict[str, Any]):
        try:
            return self.pipeline.sync_offline_attempts(batch_payload)
        except Exception as e:
            logger.error(f"Edge sync failed: {e}")
            raise AIProcessingError(message=f"Edge sync error: {str(e)}")

    def get_classroom_mastery_heatmap(self) -> List[Dict[str, Any]]:
        try:
            return self.pipeline.get_classroom_mastery_heatmap()
        except Exception as e:
            logger.error(f"Mastery heatmap failed: {e}")
            raise AIProcessingError(message=f"Mastery heatmap error: {str(e)}")

copilot_ai = CopilotAI()
