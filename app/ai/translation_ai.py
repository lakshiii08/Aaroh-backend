from typing import Optional, List, Dict, Any
from app.ai.aaroh_ai_adapter import ai_adapter
from src.aaroh.entity.artifact_entity import GlossaryEntryEntity
from app.core.exceptions import AIProcessingError
from app.core.logging import logger

class TranslationAI:
    def __init__(self):
        self.component = ai_adapter.translation_component
        self.glossary_db = ai_adapter.glossary_db
        self.config = ai_adapter.translation_config

    def translate_single(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "hi",
        target_dialect: Optional[str] = None,
        apply_glossary: bool = True,
    ):
        try:
            return self.component.translate_text(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                target_dialect=target_dialect,
                apply_glossary=apply_glossary,
            )
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise AIProcessingError(message=f"Translation error: {str(e)}")

    def translate_batch(
        self,
        texts: List[str],
        source_lang: str = "en",
        target_lang: str = "hi",
        target_dialect: Optional[str] = None,
    ):
        try:
            return self.component.translate_batch(
                texts=texts,
                source_lang=source_lang,
                target_lang=target_lang,
                target_dialect=target_dialect,
            )
        except Exception as e:
            logger.error(f"Batch translation failed: {e}")
            raise AIProcessingError(message=f"Batch translation error: {str(e)}")

    def get_supported_languages(self) -> Dict[str, Any]:
        return {
            "supported_languages": self.config.supported_languages,
            "default_source": self.config.default_source_lang,
            "default_target": self.config.default_target_lang,
        }

    def lookup_glossary_term(self, term: str, source_lang: str = "en", target_lang: str = "hi"):
        return self.glossary_db.get_term(term, source_lang=source_lang, target_lang=target_lang)

    def add_glossary_term(self, entry_dict: Dict[str, Any]):
        entry = GlossaryEntryEntity(
            source_term=entry_dict["source_term"],
            translated_term=entry_dict["translated_term"],
            source_lang=entry_dict.get("source_lang", "en"),
            target_lang=entry_dict.get("target_lang", "hi"),
            domain=entry_dict.get("domain", "general"),
            dialects=entry_dict.get("dialects", {}),
            phonetic_hint=entry_dict.get("phonetic_hint"),
            notes=entry_dict.get("notes"),
        )
        self.glossary_db.put_term(entry)
        return entry

translation_ai = TranslationAI()
