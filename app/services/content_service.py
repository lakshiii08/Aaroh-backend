import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.ai.content_ai import content_ai
from app.models.pg_models import DocumentModel, ConceptModel
from app.core.exceptions import ValidationError, NotFoundError
from app.core.logging import logger

class ContentService:
    def __init__(self, pg_session: Session):
        self.pg_session = pg_session

    async def upload_and_process_lesson(
        self,
        file: UploadFile,
        grade_hint: str = "Grade 3",
        subject_hint: str = "Environmental Studies",
    ) -> Dict[str, Any]:
        """Saves uploaded curriculum file and runs Aaroh-AI document ingestion pipeline."""
        filename = file.filename
        ext = Path(filename).suffix.lower()
        if ext not in [".pdf", ".txt", ".md", ".pptx"]:
            raise ValidationError(
                message=f"Unsupported file format '{ext}'. Allowed formats: .pdf, .pptx, .txt, .md",
                code="UNSUPPORTED_FILE_TYPE",
            )

        uploads_dir = Path("data/uploads")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        saved_file_path = uploads_dir / filename

        with open(saved_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run real Aaroh-AI ingestion pipeline
        result = content_ai.process_and_ingest_lesson(
            file_path=saved_file_path,
            grade_hint=grade_hint,
            subject_hint=subject_hint,
        )

        return {
            "document_id": result.document_id,
            "filename": result.filename,
            "status": result.status,
            "total_pages": result.total_pages,
            "total_chunks": result.total_chunks,
            "total_concepts": result.total_concepts,
        }

    def list_documents(self) -> List[Dict[str, Any]]:
        """Retrieves ingested curriculum documents from PostgreSQL."""
        docs = self.pg_session.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "title": d.title,
                "subject": d.subject,
                "grade_level": d.grade_level,
                "language": d.language,
                "summary": d.summary,
                "total_pages": d.total_pages,
                "status": d.status,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ]

    def get_document_by_id(self, document_id: str) -> Dict[str, Any]:
        """Retrieves single document by id."""
        d = self.pg_session.query(DocumentModel).filter_by(id=document_id).first()
        if not d:
            raise NotFoundError(message=f"Document '{document_id}' not found.", code="DOCUMENT_NOT_FOUND")
        return {
            "id": d.id,
            "filename": d.filename,
            "title": d.title,
            "subject": d.subject,
            "grade_level": d.grade_level,
            "language": d.language,
            "summary": d.summary,
            "total_pages": d.total_pages,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }

    def get_document_concepts(self, document_id: str) -> Dict[str, Any]:
        """Retrieves atomic concepts, Bloom's levels, and rural context anchors for a document."""
        doc = self.pg_session.query(DocumentModel).filter_by(id=document_id).first()
        if not doc:
            raise NotFoundError(message=f"Document with ID '{document_id}' not found.", code="DOCUMENT_NOT_FOUND")

        concepts = self.pg_session.query(ConceptModel).filter_by(document_id=document_id).all()
        return {
            "document_id": doc.id,
            "title": doc.title,
            "total_concepts": len(concepts),
            "concepts": [
                {
                    "id": c.id,
                    "concept_code": c.concept_code,
                    "name": c.name,
                    "definition": c.definition,
                    "blooms_level": c.blooms_level,
                    "difficulty_level": c.difficulty_level,
                    "prerequisite_concepts": c.prerequisite_concepts or [],
                    "rural_tribal_anchors": c.rural_tribal_anchors or [],
                    "key_vocabulary": c.key_vocabulary or [],
                }
                for c in concepts
            ],
        }

    def search_curriculum(
        self,
        query: str,
        top_k: int = 5,
        grade_level: Optional[int] = None,
        subject: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs vector semantic search over curriculum chunks."""
        results = content_ai.vector_search(
            query=query,
            top_k=top_k,
            grade_level=grade_level,
            subject=subject,
        )
        return {
            "query": query,
            "total_results": len(results),
            "results": [
                {
                    "chunk_id": r["id"],
                    "content": r["content"],
                    "page_number": r["page_number"],
                    "chunk_index": r["chunk_index"],
                    "concept_code": r.get("concept_code"),
                    "similarity_score": round(float(r.get("similarity", 0.0)), 4),
                    "doc_title": r.get("doc_title"),
                    "grade_level": r.get("grade_level"),
                    "subject": r.get("subject"),
                }
                for r in results
            ],
        }
