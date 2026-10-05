from typing import Optional, List, Dict, Any
from app.ai.simplification_ai import simplification_ai
from app.core.logging import logger

class SimplificationService:
    def localize_concept(
        self,
        concept_code: str,
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
        grade_level: int = 3,
        force_regenerate: bool = False,
    ) -> Dict[str, Any]:
        result = simplification_ai.localize_concept(
            concept_code=concept_code,
            target_language=target_language,
            target_dialect=target_dialect,
            grade_level=grade_level,
            force_regenerate=force_regenerate,
        )
        return {
            "cached": result.cached,
            "concept_code": result.concept_code,
            "concept_name": result.concept_name,
            "grade_level": result.grade_level,
            "target_language": result.target_language,
            "target_dialect": result.target_dialect,
            "lesson": {
                "simplified_explanation": result.simplified_explanation,
                "local_analogies": result.local_analogies,
                "story_narrative": result.story_narrative,
                "hands_on_activity": result.hands_on_activity,
                "reflection_questions": result.reflection_questions,
                "voice_script": result.voice_script,
            },
            "cultural_anchors_used": result.cultural_anchors_used,
            "source_chunks_preview": result.source_chunks,
        }

    def localize_document(
        self,
        document_id: str,
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
    ) -> Dict[str, Any]:
        lessons = simplification_ai.localize_document(
            document_id=document_id,
            target_language=target_language,
            target_dialect=target_dialect,
        )
        return {
            "document_id": document_id,
            "target_language": target_language,
            "target_dialect": target_dialect,
            "total_lessons": len(lessons),
            "lessons": [
                {
                    "concept_code": l.concept_code,
                    "concept_name": l.concept_name,
                    "cached": l.cached,
                    "simplified_explanation": l.simplified_explanation,
                    "local_analogies": l.local_analogies,
                    "story_narrative": l.story_narrative,
                    "hands_on_activity": l.hands_on_activity,
                    "reflection_questions": l.reflection_questions,
                    "voice_script": l.voice_script,
                }
                for l in lessons
            ],
        }

    def run_langgraph_for_concept(
        self,
        concept_code: str,
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
        grade_level: int = 3,
        force_regenerate: bool = False,
    ) -> Dict[str, Any]:
        lesson_dict = simplification_ai.run_langgraph_for_concept(
            concept_code=concept_code,
            target_language=target_language,
            target_dialect=target_dialect,
            grade_level=grade_level,
            force_regenerate=force_regenerate,
        )
        return {
            "agent": "LangGraph — SimplificationLocalizationGraph",
            "concept_code": concept_code,
            "lesson": lesson_dict,
        }

    def get_cache_status(self) -> Dict[str, Any]:
        return simplification_ai.get_cache_status()
