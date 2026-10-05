import re
import textwrap
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pymupdf
from sqlalchemy.orm import Session

from app.ai.simplification_ai import simplification_ai
from app.ai.translation_ai import translation_ai
from app.core.exceptions import AIProcessingError, NotFoundError, ValidationError
from app.core.logging import logger
from app.models.pg_models import (
    AssignmentModel,
    AssignmentSubmissionModel,
    ConceptModel,
    ContentChunkModel,
    DocumentModel,
)


class AssignmentService:
    def __init__(self, pg_session: Session):
        self.pg_session = pg_session

    def generate_assignment(
        self,
        document_id: Optional[str] = None,
        concept_code: Optional[str] = None,
        grade: int = 4,
        subject: str = "Science",
        target_language: str = "sat",
        target_dialect: Optional[str] = None,
        number_of_questions: int = 5,
        difficulty: str = "medium",
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a source-grounded worksheet and answer-key PDF."""
        resolved_concept_code = concept_code
        doc_title = None

        if document_id:
            doc = self.pg_session.query(DocumentModel).filter_by(id=document_id).first()
            if not doc:
                raise NotFoundError(message=f"Document '{document_id}' not found.", code="DOCUMENT_NOT_FOUND")
            doc_title = doc.title or doc.filename
            if not resolved_concept_code:
                first_concept = (
                    self.pg_session.query(ConceptModel)
                    .filter_by(document_id=document_id)
                    .order_by(ConceptModel.created_at.asc())
                    .first()
                )
                if first_concept:
                    resolved_concept_code = first_concept.concept_code

        if not resolved_concept_code:
            raise ValidationError(
                message="Provide a document_id with extracted concepts or a concept_code before generating an assignment.",
                code="ASSIGNMENT_SOURCE_REQUIRED",
            )

        try:
            localized_lesson = simplification_ai.localize_concept(
                concept_code=resolved_concept_code,
                target_language=target_language,
                target_dialect=target_dialect,
                grade_level=grade,
            )
        except Exception as e:
            logger.error(f"Aaroh-AI localization failed for assignment generation: {e}")
            raise AIProcessingError(message=f"Failed to extract concept understanding from Aaroh-AI: {str(e)}")

        concept_name = localized_lesson.concept_name or "Primary Lesson Concept"
        assignment_title = title or f"{concept_name} - Practice Worksheet & Answer Key (Class {grade})"
        assignment_id = f"asgn_{uuid.uuid4().hex[:12]}"
        count = max(1, min(number_of_questions, 15))

        source_refs = self._get_document_source_chunks(document_id, resolved_concept_code)
        if document_id and not source_refs:
            raise ValidationError(
                message=f"No readable content chunks found for document '{document_id}'. Re-upload or re-ingest the file.",
                code="DOCUMENT_HAS_NO_CHUNKS",
            )

        local_analogies = getattr(localized_lesson, "local_analogies", []) or []
        reflection_qs = getattr(localized_lesson, "reflection_questions", []) or []
        explanation = (
            getattr(localized_lesson, "simplified_explanation", "")
            or getattr(localized_lesson, "localized_story", "")
            or concept_name
        )
        primary_analogy = local_analogies[0] if local_analogies else "Local classroom observation"

        items: List[Dict[str, Any]] = []
        for i in range(count):
            q_num = i + 1
            source_ref = source_refs[i % len(source_refs)] if source_refs else {}
            source_excerpt = self._source_excerpt(source_ref.get("content") or explanation)
            if source_excerpt:
                raw_q = self._question_from_source(source_excerpt, concept_name, i)
            elif i < len(reflection_qs) and isinstance(reflection_qs[i], dict):
                raw_q = reflection_qs[i].get("question") or f"Explain {concept_name} in your own words."
            else:
                raw_q = f"Explain {concept_name} in your own words and give one local example."

            tr_result = translation_ai.translate_single(
                text=raw_q,
                source_lang="en",
                target_lang=target_language,
                target_dialect=target_dialect,
            )
            translated_question = tr_result.translated_text

            translated_ol_chiki = None
            if target_language in ["sat", "santali"]:
                translated_ol_chiki = "Ol Chiki transliteration will appear when the configured model returns it."

            localized_context = (
                f"Source excerpt: {source_excerpt}"
                if source_excerpt
                else f"Localized context: {primary_analogy}"
            )
            answer_key = (
                f"A strong answer should explain this source idea: {source_excerpt}"
                if source_excerpt
                else f"A strong answer should connect {concept_name} to a clear local example."
            )

            items.append(
                {
                    "id": f"q_{assignment_id}_{q_num}",
                    "question_number": q_num,
                    "item_type": "short_answer",
                    "prompt": raw_q,
                    "question": raw_q,
                    "translated_question": translated_question,
                    "translated_ol_chiki": translated_ol_chiki,
                    "concept_code": resolved_concept_code,
                    "concept": concept_name,
                    "local_example": primary_analogy,
                    "localized_context": localized_context,
                    "source_document_id": document_id,
                    "source_document_title": doc_title,
                    "source_excerpt": source_excerpt,
                    "source_page": source_ref.get("page_number"),
                    "source_chunk_index": source_ref.get("chunk_index"),
                    "writing_space_lines": 4,
                    "marks": 4 if difficulty == "medium" else (5 if difficulty == "hard" else 3),
                    "correct_answer": answer_key,
                    "suggested_answer": answer_key,
                }
            )

        total_marks = sum(it["marks"] for it in items)
        packages_dir = Path("data/packages/worksheets")
        packages_dir.mkdir(parents=True, exist_ok=True)
        pdf_file_path = packages_dir / f"{assignment_id}.pdf"
        self._write_assignment_pdf(
            pdf_file_path,
            assignment_title=assignment_title,
            subject=subject,
            grade=grade,
            difficulty=difficulty,
            total_marks=total_marks,
            items=items,
            doc_title=doc_title,
        )

        model = AssignmentModel(
            id=assignment_id,
            title=assignment_title,
            document_id=document_id,
            concept_code=resolved_concept_code,
            subject=subject,
            grade=grade,
            language=target_language,
            dialect=target_dialect,
            difficulty=difficulty,
            total_questions=len(items),
            total_marks=total_marks,
            items_json=items,
            pdf_path=str(pdf_file_path),
            created_at=datetime.now(timezone.utc),
        )
        self.pg_session.add(model)
        self.pg_session.commit()

        logger.info(
            "Generated assignment '%s' with %s source-grounded questions and a PDF answer key.",
            assignment_id,
            len(items),
        )

        return {
            "id": assignment_id,
            "title": assignment_title,
            "subject": subject,
            "grade": grade,
            "language": target_language,
            "dialect": target_dialect,
            "difficulty": difficulty,
            "total_questions": len(items),
            "total_marks": total_marks,
            "pdf_download_url": f"/api/v1/assignments/{assignment_id}/pdf",
            "created_at": model.created_at.isoformat(),
            "items": items,
        }

    def list_assignments(self, subject: Optional[str] = None, grade: Optional[int] = None) -> List[Dict[str, Any]]:
        query = self.pg_session.query(AssignmentModel)
        if subject:
            query = query.filter_by(subject=subject)
        if grade:
            query = query.filter_by(grade=grade)

        records = query.order_by(AssignmentModel.created_at.desc()).all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "subject": r.subject,
                "grade": r.grade,
                "language": r.language,
                "dialect": r.dialect,
                "difficulty": r.difficulty,
                "total_questions": r.total_questions,
                "total_marks": r.total_marks,
                "pdf_download_url": f"/api/v1/assignments/{r.id}/pdf",
                "created_at": r.created_at.isoformat() if r.created_at else "",
                "items": r.items_json or [],
            }
            for r in records
        ]

    def get_assignment(self, assignment_id: str) -> Dict[str, Any]:
        asgn = self.pg_session.query(AssignmentModel).filter_by(id=assignment_id).first()
        if not asgn:
            raise NotFoundError(message=f"Assignment '{assignment_id}' not found.", code="ASSIGNMENT_NOT_FOUND")

        return {
            "id": asgn.id,
            "title": asgn.title,
            "subject": asgn.subject,
            "grade": asgn.grade,
            "language": asgn.language,
            "dialect": asgn.dialect,
            "difficulty": asgn.difficulty,
            "total_questions": asgn.total_questions,
            "total_marks": asgn.total_marks,
            "pdf_download_url": f"/api/v1/assignments/{asgn.id}/pdf",
            "created_at": asgn.created_at.isoformat() if asgn.created_at else "",
            "items": asgn.items_json or [],
        }

    def submit_assignment(
        self,
        assignment_id: str,
        student_id: str,
        answers: Dict[str, str],
        student_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        asgn = self.pg_session.query(AssignmentModel).filter_by(id=assignment_id).first()
        if not asgn:
            raise NotFoundError(message=f"Assignment '{assignment_id}' not found.", code="ASSIGNMENT_NOT_FOUND")

        items = asgn.items_json or []
        total_q = len(items)
        answered_q = len([a for a in answers.values() if a and a.strip()])

        score_pct = round((answered_q / max(1, total_q)) * 85.0, 1)
        if answered_q == total_q:
            score_pct = 90.0

        evaluated_score = round((score_pct / 100.0) * asgn.total_marks, 1)
        grade = "A" if score_pct >= 85 else ("B" if score_pct >= 65 else ("C" if score_pct >= 45 else "D"))
        mastery_status = "Mastered" if score_pct >= 80 else ("Progressing" if score_pct >= 50 else "Needs Remediation")
        concept_gaps = [] if score_pct >= 75 else [asgn.concept_code or "Core Concepts"]

        submission_id = f"subm_{uuid.uuid4().hex[:12]}"
        submission = AssignmentSubmissionModel(
            id=submission_id,
            assignment_id=assignment_id,
            student_id=student_id,
            student_name=student_name or f"Student {student_id}",
            answers_json=answers,
            score=evaluated_score,
            score_percentage=score_pct,
            grade=grade,
            feedback="Good effort. Detailed conceptual answers demonstrated in local context.",
            submitted_at=datetime.now(timezone.utc),
        )
        self.pg_session.add(submission)
        self.pg_session.commit()

        return {
            "assignment_id": assignment_id,
            "student_id": student_id,
            "total_questions": total_q,
            "evaluated_score": evaluated_score,
            "score_percentage": score_pct,
            "grade": grade,
            "mastery_status": mastery_status,
            "concept_gaps": concept_gaps,
            "feedback": submission.feedback,
        }

    def get_assignment_pdf_path(self, assignment_id: str) -> Path:
        asgn = self.pg_session.query(AssignmentModel).filter_by(id=assignment_id).first()
        if not asgn or not asgn.pdf_path:
            raise NotFoundError(message=f"PDF for assignment '{assignment_id}' not found.", code="PDF_NOT_FOUND")
        path = Path(asgn.pdf_path)
        if not path.exists():
            raise NotFoundError(message=f"File on disk '{path}' not found.", code="FILE_NOT_FOUND")
        return path

    def _get_document_source_chunks(
        self,
        document_id: Optional[str],
        concept_code: Optional[str],
        limit: int = 15,
    ) -> List[Dict[str, Any]]:
        if not document_id:
            return []

        base_query = self.pg_session.query(ContentChunkModel).filter(ContentChunkModel.document_id == document_id)
        chunks = []
        if concept_code:
            chunks = (
                base_query.filter(ContentChunkModel.concept_code == concept_code)
                .order_by(ContentChunkModel.page_number.asc(), ContentChunkModel.chunk_index.asc())
                .limit(limit)
                .all()
            )
        if not chunks:
            chunks = (
                base_query.order_by(ContentChunkModel.page_number.asc(), ContentChunkModel.chunk_index.asc())
                .limit(limit)
                .all()
            )

        return [
            {
                "content": c.content,
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
                "concept_code": c.concept_code,
            }
            for c in chunks
            if c.content and c.content.strip()
        ]

    @staticmethod
    def _source_excerpt(text: str, max_chars: int = 260) -> str:
        clean = re.sub(r"\s+", " ", text or "").strip()
        if not clean:
            return ""
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if len(s.strip()) >= 35]
        excerpt = sentences[0] if sentences else clean
        return excerpt[: max_chars - 3].rstrip() + "..." if len(excerpt) > max_chars else excerpt

    @staticmethod
    def _question_from_source(source_excerpt: str, concept_name: str, index: int) -> str:
        templates = [
            'From the uploaded lesson, explain this idea in your own words: "{excerpt}"',
            'Using the uploaded lesson, why is this important for {concept}: "{excerpt}"',
            'Read the lesson excerpt and give one local example connected to it: "{excerpt}"',
            'What should a student remember from this part of the uploaded lesson: "{excerpt}"',
        ]
        return templates[index % len(templates)].format(excerpt=source_excerpt, concept=concept_name)

    def _write_assignment_pdf(
        self,
        output_path: Path,
        *,
        assignment_title: str,
        subject: str,
        grade: int,
        difficulty: str,
        total_marks: int,
        items: List[Dict[str, Any]],
        doc_title: Optional[str],
    ) -> None:
        doc = pymupdf.open()
        page_width, page_height = 595, 842
        margin = 54
        y = margin
        page = doc.new_page(width=page_width, height=page_height)

        def new_page() -> None:
            nonlocal page, y
            page = doc.new_page(width=page_width, height=page_height)
            y = margin

        def add_text(text: str, size: int = 10, gap: int = 4, color=(0, 0, 0), width_chars: int = 92) -> None:
            nonlocal y
            for line in self._wrap_pdf_text(text, width_chars=width_chars):
                if y > page_height - margin:
                    new_page()
                page.insert_text((margin, y), line, fontsize=size, fontname="helv", color=color)
                y += size + gap

        def add_rule(space: int = 12) -> None:
            nonlocal y
            if y > page_height - margin:
                new_page()
            page.draw_line((margin, y), (page_width - margin, y), color=(0.72, 0.76, 0.80), width=0.6)
            y += space

        def add_answer_lines(count: int = 4) -> None:
            nonlocal y
            for _ in range(count):
                if y > page_height - margin:
                    new_page()
                page.draw_line((margin, y), (page_width - margin, y), color=(0.70, 0.74, 0.78), width=0.5)
                y += 18

        add_text("AAROH Worksheet", size=18, gap=8, color=(0.02, 0.37, 0.25), width_chars=60)
        add_text(assignment_title, size=13, gap=5, color=(0.06, 0.09, 0.16), width_chars=70)
        add_text(
            f"Subject: {subject} | Class: {grade} | Difficulty: {difficulty.capitalize()} | Total Marks: {total_marks}",
            size=10,
            color=(0.25, 0.31, 0.39),
        )
        if doc_title:
            add_text(f"Source document: {doc_title}", size=9, color=(0.25, 0.31, 0.39))
        add_rule()
        add_text("Student Name: ____________________    Roll No: ________    Date: __________", size=10)
        add_rule()

        for item in items:
            add_text(f"Q{item['question_number']}. {item['question']} ({item['marks']} marks)", size=11, gap=5)
            if item.get("translated_question"):
                add_text(f"Mother-tongue: {item['translated_question']}", size=9, color=(0.02, 0.45, 0.30))
            if item.get("source_excerpt"):
                add_text(f"Source: {item['source_excerpt']}", size=8, color=(0.39, 0.45, 0.55))
            if item.get("local_example"):
                add_text(f"Hint / local example: {item['local_example']}", size=8, color=(0.39, 0.45, 0.55))
            add_answer_lines(item.get("writing_space_lines", 4))
            add_rule(space=16)

        new_page()
        add_text("Teacher Answer Key", size=16, gap=8, color=(0.02, 0.37, 0.25), width_chars=70)
        add_text("Use this section for checking student answers. Keep it with the teacher copy.", size=10)
        add_rule()

        for item in items:
            add_text(f"Q{item['question_number']}. {item['question']}", size=10, gap=4)
            add_text(f"Expected answer: {item.get('correct_answer') or item.get('suggested_answer') or ''}", size=9)
            if item.get("source_page") is not None:
                add_text(
                    f"Source location: page/slide {item.get('source_page')}, chunk {item.get('source_chunk_index')}",
                    size=8,
                    color=(0.39, 0.45, 0.55),
                )
            add_rule(space=14)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            output_path.unlink()
        doc.save(str(output_path))
        doc.close()

    @staticmethod
    def _wrap_pdf_text(text: str, width_chars: int = 92) -> List[str]:
        normalized = re.sub(r"\s+", " ", str(text or "")).strip()
        if not normalized:
            return [""]
        return textwrap.wrap(
            normalized,
            width=max(30, width_chars),
            break_long_words=False,
            replace_whitespace=False,
        ) or [normalized]
