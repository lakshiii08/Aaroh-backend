import os
import sys
from pathlib import Path
from typing import Optional

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

    @classmethod
    def get_instance(cls) -> "AarohAIAdapter":
        if cls._instance is None:
            cls._instance = AarohAIAdapter()
        return cls._instance

ai_adapter = AarohAIAdapter.get_instance()
