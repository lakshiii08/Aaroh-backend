from typing import Optional, List, Dict, Any
from app.ai.aaroh_ai_adapter import ai_adapter
from app.core.exceptions import AIProcessingError
from app.core.logging import logger

class SimplificationAI:
    def __init__(self):
        self.pipeline = ai_adapter.simplification_pipeline

    def localize_concept(
        self,
        concept_code: str,
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
        grade_level: int = 3,
        force_regenerate: bool = False,
    ):
        try:
            return self.pipeline.run_for_concept(
                concept_code=concept_code,
                target_language=target_language,
                target_dialect=target_dialect,
                grade_level=grade_level,
                force_regenerate=force_regenerate,
            )
        except Exception as e:
            logger.error(f"Concept localization failed: {e}")
            raise AIProcessingError(message=f"Concept localization error: {str(e)}")

    def localize_document(
        self,
        document_id: str,
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
    ):
        try:
            return self.pipeline.run_for_document(
                document_id=document_id,
                target_language=target_language,
                target_dialect=target_dialect,
            )
        except Exception as e:
            logger.error(f"Document localization failed: {e}")
            raise AIProcessingError(message=f"Document localization error: {str(e)}")

    def run_langgraph_for_concept(
        self,
        concept_code: str,
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
        grade_level: int = 3,
        force_regenerate: bool = False,
    ):
        try:
            return self.pipeline.run_langgraph_for_concept(
                concept_code=concept_code,
                target_language=target_language,
                target_dialect=target_dialect,
                grade_level=grade_level,
                force_regenerate=force_regenerate,
            )
        except Exception as e:
            logger.error(f"LangGraph execution failed: {e}")
            raise AIProcessingError(message=f"LangGraph execution error: {str(e)}")

    def get_cache_status(self) -> Dict[str, Any]:
        cache = self.pipeline.cache
        entries = [
            {
                "cache_key": k,
                "concept_code": v.get("concept_code"),
                "target_language": v.get("target_language"),
                "target_dialect": v.get("target_dialect"),
            }
            for k, v in cache.memory_cache.items()
        ]
        return {
            "total_cached_lessons": len(entries),
            "entries": entries,
        }

simplification_ai = SimplificationAI()
