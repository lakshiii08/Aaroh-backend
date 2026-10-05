from fastapi import APIRouter, Depends
from app.services.simplification_service import SimplificationService
from app.schemas.simplification_schemas import (
    ConceptLocalizeRequest,
    DocumentLocalizeRequest,
)
from app.schemas.common_schemas import success_response
from app.api.deps import get_optional_current_user

router = APIRouter(prefix="/simplification", tags=["Simplification & Localization (RAG)"])

service = SimplificationService()

@router.post("/concepts/{concept_code}", response_model=dict)
def localize_concept(
    concept_code: str,
    request: ConceptLocalizeRequest,
    current_user: dict = Depends(get_optional_current_user),
):
    """Generates a simplified, culturally localized lesson for a curriculum concept.
    
    LangGraph pipeline: cache_lookup → RAG retrieval → Bedrock LLM → cache & emit.
    Returns: explanation, village analogies, micro-story, hands-on activity, voice script.
    """
    result = service.localize_concept(
        concept_code=concept_code,
        target_language=request.target_language,
        target_dialect=request.target_dialect,
        grade_level=request.grade_level,
        force_regenerate=request.force_regenerate,
    )
    return success_response(result)

@router.post("/documents/{document_id}", response_model=dict)
def localize_document(
    document_id: str,
    request: DocumentLocalizeRequest,
    current_user: dict = Depends(get_optional_current_user),
):
    """Localizes ALL concepts of an ingested document in one shot."""
    result = service.localize_document(
        document_id=document_id,
        target_language=request.target_language,
        target_dialect=request.target_dialect,
    )
    return success_response(result)

@router.post("/langgraph/concepts/{concept_code}", response_model=dict)
def run_langgraph_agent(
    concept_code: str,
    request: ConceptLocalizeRequest,
    current_user: dict = Depends(get_optional_current_user),
):
    """Executes the explicit LangGraph agent for a concept (cache → RAG → LLM)."""
    result = service.run_langgraph_for_concept(
        concept_code=concept_code,
        target_language=request.target_language,
        target_dialect=request.target_dialect,
        grade_level=request.grade_level,
        force_regenerate=request.force_regenerate,
    )
    return success_response(result)

@router.get("/cache/status", response_model=dict)
def get_cache_status(
    current_user: dict = Depends(get_optional_current_user),
):
    """Returns the current content cache state."""
    result = service.get_cache_status()
    return success_response(result)
