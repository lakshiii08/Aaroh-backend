from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.ai.translation_ai import translation_ai
from app.models.pg_models import DocumentModel, ContentChunkModel
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import logger

class TranslationService:
    def __init__(self, pg_session: Session):
        self.pg_session = pg_session

    def translate_text(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "hi",
        target_dialect: Optional[str] = None,
        apply_glossary: bool = True,
    ) -> Dict[str, Any]:
        result = translation_ai.translate_single(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            target_dialect=target_dialect,
            apply_glossary=apply_glossary,
        )
        return {
            "original_text": result.original_text,
            "translated_text": result.translated_text,
            "source_lang": result.source_lang,
            "target_lang": result.target_lang,
            "applied_glossary_terms": result.applied_glossary_terms,
            "latency_ms": result.latency_ms,
            "backend_used": result.backend_used,
        }

    def translate_batch(
        self,
        texts: List[str],
        source_lang: str = "en",
        target_lang: str = "hi",
        target_dialect: Optional[str] = None,
    ) -> Dict[str, Any]:
        result = translation_ai.translate_batch(
            texts=texts,
            source_lang=source_lang,
            target_lang=target_lang,
            target_dialect=target_dialect,
        )
        return {
            "total_count": result.total_count,
            "total_time_ms": result.total_time_ms,
            "results": [
                {
                    "original_text": r.original_text,
                    "translated_text": r.translated_text,
                    "applied_glossary_terms": r.applied_glossary_terms,
                    "latency_ms": r.latency_ms,
                }
                for r in result.results
            ],
        }

    def get_supported_languages(self) -> Dict[str, Any]:
        return translation_ai.get_supported_languages()

    def lookup_glossary_term(self, term: str, source_lang: str = "en", target_lang: str = "hi") -> Dict[str, Any]:
        entry = translation_ai.lookup_glossary_term(term, source_lang=source_lang, target_lang=target_lang)
        if not entry:
            raise NotFoundError(message=f"Term '{term}' not found in educational glossary.", code="TERM_NOT_FOUND")
        return {"term": entry}

    def add_glossary_term(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        translation_ai.add_glossary_term(entry_data)
        return {"message": f"Term '{entry_data['source_term']}' registered in pedagogical glossary."}

    def translate_lesson_document(
        self,
        document_id: str,
        target_lang: str = "hi",
        target_dialect: Optional[str] = None,
    ) -> Dict[str, Any]:
        doc = self.pg_session.query(DocumentModel).filter_by(id=document_id).first()
        if not doc:
            raise NotFoundError(message="Document not found", code="DOCUMENT_NOT_FOUND")

        chunks = (
            self.pg_session.query(ContentChunkModel)
            .filter_by(document_id=document_id)
            .order_by(ContentChunkModel.chunk_index)
            .all()
        )
        if not chunks:
            raise ValidationError(message="No chunks found for this document to translate", code="NO_CHUNKS")

        texts = [chunk.content for chunk in chunks]
        batch_result = translation_ai.translate_batch(
            texts=texts,
            source_lang="en",
            target_lang=target_lang,
            target_dialect=target_dialect,
        )

        translated_chunks = []
        for idx, chunk in enumerate(chunks):
            tr = batch_result.results[idx]
            translated_chunks.append({
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "original_content": chunk.content,
                "translated_content": tr.translated_text,
                "applied_glossary_terms": tr.applied_glossary_terms,
            })

        return {
            "document_id": doc.id,
            "document_title": doc.title,
            "target_lang": target_lang,
            "target_dialect": target_dialect,
            "total_chunks": len(translated_chunks),
            "total_time_ms": batch_result.total_time_ms,
            "chunks": translated_chunks,
        }
