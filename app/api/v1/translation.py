from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.postgres import get_db
from app.services.translation_service import TranslationService
from app.schemas.translation_schemas import (
    TranslateRequest,
    BatchTranslateRequest,
    GlossaryTermAddRequest,
    TranslateLessonRequest,
)
from app.schemas.common_schemas import success_response
from app.api.deps import get_optional_current_user

router = APIRouter(prefix="/translation", tags=["Mother-Tongue Translation Layer"])

@router.post("/translate", response_model=dict)
def translate_single(
    request: TranslateRequest,
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_current_user),
):
    """Translates text into mother tongue with glossary preservation and tribal dialect adaptation."""
    service = TranslationService(pg_session)
    result = service.translate_text(
        text=request.text,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
        target_dialect=request.target_dialect,
        apply_glossary=request.apply_glossary,
    )
    return success_response(result)

@router.post("/batch", response_model=dict)
def translate_batch(
    request: BatchTranslateRequest,
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_current_user),
):
    """Batch translates multiple texts (e.g. lesson paragraphs or quiz items)."""
    service = TranslationService(pg_session)
    result = service.translate_batch(
        texts=request.texts,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
        target_dialect=request.target_dialect,
    )
    return success_response(result)

@router.get("/languages", response_model=dict)
def get_supported_languages(
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_current_user),
):
    """Returns list of supported Indian languages and tribal dialects (Gondi, Santhali, Bhili, etc.)."""
    service = TranslationService(pg_session)
    langs = service.get_supported_languages()
    return success_response(langs)

@router.get("/glossary/lookup", response_model=dict)
def lookup_glossary_term(
    term: str = Query(..., description="Term to look up"),
    source_lang: str = Query("en"),
    target_lang: str = Query("hi"),
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_current_user),
):
    """Ultra-low latency (< 2ms) glossary term lookup in cached educational glossary."""
    service = TranslationService(pg_session)
    result = service.lookup_glossary_term(term=term, source_lang=source_lang, target_lang=target_lang)
    return success_response(result)

@router.post("/glossary/term", response_model=dict)
def add_glossary_term(
    request: GlossaryTermAddRequest,
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_current_user),
):
    """Adds or updates a pedagogical/tribal glossary term."""
    service = TranslationService(pg_session)
    result = service.add_glossary_term(request.model_dump())
    return success_response(result)

@router.post("/lessons/{document_id}", response_model=dict)
def translate_lesson_document(
    document_id: str,
    request: TranslateLessonRequest,
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_current_user),
):
    """Translates all content chunks of an ingested lesson into child's mother tongue."""
    service = TranslationService(pg_session)
    result = service.translate_lesson_document(
        document_id=document_id,
        target_lang=request.target_lang,
        target_dialect=request.target_dialect,
    )
    return success_response(result)
