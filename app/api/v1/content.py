from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.core.postgres import get_db
from app.services.content_service import ContentService
from app.schemas.content_schemas import ContentSearchRequest
from app.schemas.common_schemas import success_response
from app.api.deps import require_roles, get_optional_current_user
from app.core.jwt import UserRole

router = APIRouter(prefix="/content", tags=["Content Ingestion & Concept Extraction"])

@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_lesson(
    file: UploadFile = File(...),
    grade_hint: str = Form("Grade 3"),
    subject_hint: str = Form("Environmental Studies"),
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(require_roles([UserRole.TEACHER, UserRole.ADMIN, UserRole.DISTRICT_ADMIN])),
):
    """Uploads curriculum file and runs Aaroh-AI document ingestion pipeline."""
    service = ContentService(pg_session)
    result = await service.upload_and_process_lesson(
        file=file,
        grade_hint=grade_hint,
        subject_hint=subject_hint,
    )
    return success_response(result)

@router.get("/documents", response_model=dict)
def list_documents(
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_current_user),
):
    """Lists all ingested curriculum documents."""
    service = ContentService(pg_session)
    docs = service.list_documents()
    return success_response(docs)

@router.get("/documents/{document_id}", response_model=dict)
def get_document(
    document_id: str,
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_current_user),
):
    """Retrieves metadata of a specific ingested document."""
    service = ContentService(pg_session)
    doc = service.get_document_by_id(document_id=document_id)
    return success_response(doc)

@router.get("/documents/{document_id}/concepts", response_model=dict)
def get_document_concepts(
    document_id: str,
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_current_user),
):
    """Retrieves atomic concepts, Bloom's cognitive levels, and tribal/rural anchors."""
    service = ContentService(pg_session)
    concepts_data = service.get_document_concepts(document_id=document_id)
    return success_response(concepts_data)

@router.post("/search", response_model=dict)
def search_curriculum(
    request: ContentSearchRequest,
    pg_session: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_current_user),
):
    """Semantic vector similarity search across curriculum chunks using Titan embeddings & pgvector."""
    service = ContentService(pg_session)
    results = service.search_curriculum(
        query=request.query,
        top_k=request.top_k,
        grade_level=request.grade_level,
        subject=request.subject,
    )
    return success_response(results)
