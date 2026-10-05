import os
import sys
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote, urlparse

from app.core.config import settings, AAROH_AI_DIR
from app.core.logging import logger

# Ensure Aaroh-AI is in sys.path
if str(AAROH_AI_DIR) not in sys.path:
    sys.path.insert(0, str(AAROH_AI_DIR))
if str(AAROH_AI_DIR / "src") not in sys.path:
    sys.path.insert(0, str(AAROH_AI_DIR / "src"))

from src.aaroh.configuration.configuration import ConfigurationManager
from src.aaroh.pipeline.content_ingestion_pipeline import ContentIngestionPipeline
from src.aaroh.components.translation import TranslationComponent
from src.aaroh.database.glossary_db import GlossaryDatabaseManager
from src.aaroh.pipeline.simplification_localization_pipeline import SimplificationLocalizationPipeline
from src.aaroh.pipeline.quiz_assessment_pipeline import QuizAssessmentPipeline
from src.aaroh.pipeline.voice_intelligence_pipeline import VoiceIntelligencePipeline
from src.aaroh.pipeline.copilot_edge_pipeline import CopilotEdgePipeline
from src.aaroh.pipeline.gamification_pipeline import GamificationPipeline
from src.aaroh.pipeline.district_admin_pipeline import DistrictAdminPipeline
from src.aaroh.database.session import DatabaseManager
from src.aaroh.database.models import DocumentModel, ConceptModel, ContentChunkModel


def _sync_backend_database_env_for_ai() -> None:
    """Keep embedded Aaroh-AI pipelines on the same DB as the FastAPI backend."""
    os.environ.setdefault("DB_USE_SQLITE_FALLBACK", str(settings.USE_SQLITE_FALLBACK).lower())
    os.environ.setdefault("SQLITE_DB_PATH", settings.SQLITE_DB_PATH)

    if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgres"):
        parsed = urlparse(settings.DATABASE_URL)
        os.environ.setdefault("DB_DIALECT", "postgresql")
        os.environ.setdefault("DB_HOST", parsed.hostname or settings.POSTGRES_HOST)
        os.environ.setdefault("DB_PORT", str(parsed.port or settings.POSTGRES_PORT))
        os.environ.setdefault("DB_NAME", (parsed.path or f"/{settings.POSTGRES_DB}").lstrip("/"))
        os.environ.setdefault("DB_USER", unquote(parsed.username or settings.POSTGRES_USER))
        if parsed.password:
            os.environ.setdefault("DB_PASSWORD", unquote(parsed.password))
        elif settings.POSTGRES_PASSWORD:
            os.environ.setdefault("DB_PASSWORD", settings.POSTGRES_PASSWORD)
        return

    os.environ.setdefault("DB_DIALECT", "postgresql")
    os.environ.setdefault("DB_HOST", settings.POSTGRES_HOST)
    os.environ.setdefault("DB_PORT", str(settings.POSTGRES_PORT))
    os.environ.setdefault("DB_NAME", settings.POSTGRES_DB)
    os.environ.setdefault("DB_USER", settings.POSTGRES_USER)
    if settings.POSTGRES_PASSWORD:
        os.environ.setdefault("DB_PASSWORD", settings.POSTGRES_PASSWORD)


def _json_value(value: Any, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback
    return value


def _datetime_value(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)

class AarohAIAdapter:
    """Central Adapter layer integrating the FastAPI backend directly with existing Aaroh-AI.
    
    Provides managed access to:
    - Content Ingestion & Concept Extraction Pipeline
    - Mother-Tongue Translation & Cultural Glossary Engine
    - Simplification & Localization Pipeline (RAG & LangGraph)
    - Quiz Generator & Bayesian Knowledge Tracing Assessment Engine
    - Voice & Speech Intelligence Pipeline (Polly/Indic TTS + Oral STT)
    - Teacher Copilot & Offline Edge Sync Pipeline
    - Gamification, Learning Quests & Bilingual Visual Storyboarding
    - District Administration & Community Voice Advisory Bridge
    """
    _instance: Optional["AarohAIAdapter"] = None

    def __init__(self):
        logger.info(f"Initializing AarohAIAdapter pointing to: {AAROH_AI_DIR}")
        _sync_backend_database_env_for_ai()

        # Ensure local data directory has database, glossary, and caches if running outside Aaroh-AI
        import shutil
        target_data_dir = Path("data")
        target_data_dir.mkdir(parents=True, exist_ok=True)
        source_data_dir = AAROH_AI_DIR / "data"
        if source_data_dir.exists():
            for item in ["aaroh_local.db", "glossary", "cache", "flashcards", "gamification", "audio", "packages"]:
                src_item = source_data_dir / item
                dst_item = target_data_dir / item
                if src_item.exists():
                    try:
                        if src_item.is_dir():
                            shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
                        elif not dst_item.exists() or dst_item.stat().st_size < 1000:
                            shutil.copy2(src_item, dst_item)
                    except Exception as copy_err:
                        logger.warning(f"Could not copy {item}: {copy_err}")


        self.config_manager = ConfigurationManager(
            config_filepath=settings.AAROH_AI_CONFIG_PATH,
            model_config_filepath=settings.AAROH_AI_MODEL_CONFIG_PATH,
            prompt_config_filepath=settings.AAROH_AI_PROMPT_CONFIG_PATH,
        )


        # 1. Content Pipeline
        self.content_pipeline = ContentIngestionPipeline(self.config_manager)
        self._seed_packaged_curriculum_if_missing()

        # 2. Translation & Glossary Component
        self.translation_config = self.config_manager.get_translation_config()
        self.dynamodb_config = self.config_manager.get_dynamodb_config()
        self.glossary_db = GlossaryDatabaseManager(self.dynamodb_config)
        self.translation_component = TranslationComponent(self.translation_config, self.glossary_db)

        # 3. Simplification & Localization Pipeline (RAG + LangGraph)
        self.simplification_pipeline = SimplificationLocalizationPipeline(self.config_manager)

        # 4. Assessment & Quiz Pipeline
        self.quiz_pipeline = QuizAssessmentPipeline(self.config_manager)

        # 5. Voice Intelligence Pipeline
        self.voice_pipeline = VoiceIntelligencePipeline(self.config_manager)

        # 6. Teacher Copilot & Offline Edge Pipeline
        self.copilot_pipeline = CopilotEdgePipeline(self.config_manager)

        # 7. Gamification & Visual Storytelling Pipeline
        self.gamification_pipeline = GamificationPipeline(self.config_manager)

        # 8. District Administration & Parent Bridge Pipeline
        self.district_pipeline = DistrictAdminPipeline(self.config_manager)

        logger.info("All 8 Aaroh-AI pipelines initialized successfully via adapter.")

    def _seed_packaged_curriculum_if_missing(self) -> None:
        """Copy packaged starter curriculum into the active DB when it is absent."""
        source_db = AAROH_AI_DIR / "data" / "aaroh_local.db"
        if not source_db.exists():
            logger.warning("Packaged curriculum DB not found at %s; skipping seed.", source_db)
            return

        target_session = self.content_pipeline.db_manager.get_session()
        try:
            existing = target_session.query(ConceptModel).filter_by(concept_code="EVS-G3-WAT-01").first()
            if existing:
                return

            with sqlite3.connect(source_db) as source_conn:
                source_conn.row_factory = sqlite3.Row
                source_doc = source_conn.execute(
                    """
                    SELECT d.*
                    FROM raw_documents d
                    JOIN concepts c ON c.document_id = d.id
                    WHERE c.concept_code = ?
                    ORDER BY CASE WHEN d.filename = 'sample_class3_evs_water.pdf' THEN 0 ELSE 1 END,
                             d.created_at ASC
                    LIMIT 1
                    """,
                    ("EVS-G3-WAT-01",),
                ).fetchone()
                if not source_doc:
                    logger.warning("Packaged curriculum concept EVS-G3-WAT-01 not found; skipping seed.")
                    return

                doc_id = source_doc["id"]
                concepts = source_conn.execute(
                    "SELECT * FROM concepts WHERE document_id = ? ORDER BY created_at ASC",
                    (doc_id,),
                ).fetchall()
                chunks = source_conn.execute(
                    "SELECT * FROM content_chunks WHERE document_id = ? ORDER BY page_number ASC, chunk_index ASC",
                    (doc_id,),
                ).fetchall()

            if not target_session.query(DocumentModel).filter_by(id=doc_id).first():
                target_session.add(
                    DocumentModel(
                        id=doc_id,
                        filename=source_doc["filename"],
                        file_hash=source_doc["file_hash"],
                        file_size_bytes=source_doc["file_size_bytes"],
                        s3_bucket=source_doc["s3_bucket"],
                        s3_key=source_doc["s3_key"],
                        status=source_doc["status"] or "INDEXED",
                        error_message=source_doc["error_message"],
                        title=source_doc["title"],
                        subject=source_doc["subject"],
                        grade_level=source_doc["grade_level"],
                        language=source_doc["language"],
                        summary=source_doc["summary"],
                        target_competencies=_json_value(source_doc["target_competencies"], []),
                        total_pages=source_doc["total_pages"] or 0,
                        created_at=_datetime_value(source_doc["created_at"]),
                        updated_at=_datetime_value(source_doc["updated_at"]),
                    )
                )

            for concept in concepts:
                if target_session.query(ConceptModel).filter_by(id=concept["id"]).first():
                    continue
                target_session.add(
                    ConceptModel(
                        id=concept["id"],
                        document_id=concept["document_id"],
                        concept_code=concept["concept_code"],
                        name=concept["name"],
                        definition=concept["definition"],
                        blooms_level=concept["blooms_level"],
                        difficulty_level=concept["difficulty_level"],
                        prerequisite_concepts=_json_value(concept["prerequisite_concepts"], []),
                        rural_tribal_anchors=_json_value(concept["rural_tribal_anchors"], []),
                        key_vocabulary=_json_value(concept["key_vocabulary"], []),
                        created_at=_datetime_value(concept["created_at"]),
                    )
                )

            for chunk in chunks:
                if target_session.query(ContentChunkModel).filter_by(id=chunk["id"]).first():
                    continue
                target_session.add(
                    ContentChunkModel(
                        id=chunk["id"],
                        document_id=chunk["document_id"],
                        concept_id=chunk["concept_id"],
                        concept_code=chunk["concept_code"],
                        chunk_index=chunk["chunk_index"],
                        page_number=chunk["page_number"],
                        content=chunk["content"],
                        token_count=chunk["token_count"],
                        embedding=_json_value(chunk["embedding"], None),
                        chunk_metadata=_json_value(chunk["chunk_metadata"], {}),
                        created_at=_datetime_value(chunk["created_at"]),
                    )
                )

            target_session.commit()
            logger.info(
                "Seeded packaged curriculum '%s' with %s concepts and %s chunks into the active DB.",
                source_doc["filename"],
                len(concepts),
                len(chunks),
            )
        except Exception as seed_err:
            target_session.rollback()
            logger.warning("Could not seed packaged curriculum: %s", seed_err)
        finally:
            target_session.close()

    @classmethod
    def get_instance(cls) -> "AarohAIAdapter":
        if cls._instance is None:
            cls._instance = AarohAIAdapter()
        return cls._instance

ai_adapter = AarohAIAdapter.get_instance()
