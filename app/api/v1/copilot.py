from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from app.services.copilot_service import CopilotService
from app.schemas.copilot_schemas import (
    GenerateLessonPlanRequest,
    RemedialAidRequest,
    ExportOfflineBundleRequest,
    EdgeSyncBatchRequest,
)
from app.schemas.common_schemas import success_response
from app.api.deps import require_roles, get_current_user, get_optional_current_user
from app.core.jwt import UserRole

router = APIRouter(prefix="/copilot", tags=["Teacher Copilot & Offline Edge Sync"])

service = CopilotService()

@router.post(
    "/lesson-plans/generate",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.TEACHER, UserRole.ADMIN, UserRole.DISTRICT_ADMIN]))],
)
def generate_multigrade_lesson_plan(
    request: GenerateLessonPlanRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generates a multigrade lesson plan tailored for single-teacher rural classrooms."""
    result = service.generate_lesson_plan(
        concept_code=request.concept_code,
        grade_level=request.grade_level,
        target_language=request.target_language,
        target_dialect=request.target_dialect,
        duration_mins=request.duration_mins,
    )
    return success_response(result)

@router.post(
    "/remedial-aid/generate",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.TEACHER, UserRole.ADMIN, UserRole.DISTRICT_ADMIN]))],
)
def generate_remedial_teaching_aid(
    request: RemedialAidRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generates a targeted 1-page remedial teaching guide based on student assessment gaps."""
    result = service.generate_remedial_aid(
        concept_code=request.concept_code,
        weak_bloom_level=request.weak_bloom_level,
        target_language=request.target_language,
    )
    return success_response(result)

@router.post(
    "/edge/packages/export",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.TEACHER, UserRole.ADMIN, UserRole.DISTRICT_ADMIN]))],
)
def export_offline_package(
    request: ExportOfflineBundleRequest,
    current_user: dict = Depends(get_current_user),
):
    """Exports an offline ZIP bundle for zero-connectivity rural classrooms."""
    result = service.export_offline_package(
        grade_level=request.grade_level,
        subject=request.subject,
        target_language=request.target_language,
        target_dialect=request.target_dialect,
    )
    return success_response(result)

@router.get("/edge/packages/download/{filename}")
def download_offline_package(filename: str):
    """Downloads the exported offline ZIP package."""
    zip_path = service.resolve_package_path(filename)
    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=filename,
    )

@router.post("/edge/sync", response_model=dict)
@router.post("/edge/sync/import", response_model=dict)
def sync_offline_student_attempts(
    request: EdgeSyncBatchRequest,
    current_user: dict = Depends(get_optional_current_user),
):
    """Ingests offline student quiz attempts from school kiosks/tablets and merges into central database."""
    result = service.sync_offline_attempts(request.model_dump())
    return success_response(result)

@router.get(
    "/analytics/mastery-heatmap",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.TEACHER, UserRole.ADMIN, UserRole.DISTRICT_ADMIN]))],
)
def get_classroom_mastery_heatmap(
    current_user: dict = Depends(get_current_user),
):
    """Generates concept mastery rates and student progression metrics for teacher dashboard."""
    heatmap = service.get_classroom_mastery_heatmap()
    return success_response({
        "total_concepts": len(heatmap),
        "mastery_heatmap": heatmap,
    })
