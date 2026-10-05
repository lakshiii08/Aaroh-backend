from pathlib import Path
from typing import Optional, Dict, Any, List
from app.ai.aaroh_ai_adapter import ai_adapter
from app.core.exceptions import AIProcessingError
from app.core.logging import logger

class ContentAI:
    def __init__(self):
        self.pipeline = ai_adapter.content_pipeline

    def process_and_ingest_lesson(
        self,
        file_path: Path,
        grade_hint: str = "Grade 3",
        subject_hint: str = "Environmental Studies",
    ):
        try:
            return self.pipeline.run_pipeline(
                file_path=file_path,
                grade_hint=grade_hint,
                subject_hint=subject_hint,
            )
        except Exception as e:
            logger.error(f"Content AI ingestion failed: {e}")
            raise AIProcessingError(message=f"Failed to ingest curriculum content: {str(e)}")

    def vector_search(
        self,
        query: str,
        top_k: int = 5,
        grade_level: Optional[int] = None,
        subject: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        try:
            matches = self.pipeline.rag_component.search_similar_content(
                query=query,
                top_k=top_k,
                grade_filter=grade_level,
                subject_filter=subject,
            )
            return matches
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise AIProcessingError(message=f"Semantic search failed: {str(e)}")


content_ai = ContentAI()
