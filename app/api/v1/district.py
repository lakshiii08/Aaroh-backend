from fastapi import APIRouter, Depends
from app.services.district_service import DistrictService
from app.schemas.district_schemas import (
    GeneratePathwayRequest,
    SendParentAdvisoryRequest,
)
from app.schemas.common_schemas import success_response
from app.api.deps import require_roles, get_current_user
from app.core.jwt import UserRole

router = APIRouter(prefix="/district", tags=["District Administration & Parent Voice Advisory"])

service = DistrictService()

@router.post(
    "/interventions/generate-pathway",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.TEACHER, UserRole.DISTRICT_ADMIN, UserRole.ADMIN]))],
)
def generate_remedial_pathway(
    request: GeneratePathwayRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generates a personalized 4-step remedial learning pathway for a student with identified learning gaps."""
    result = service.generate_remedial_pathway(
        student_id=request.student_id,
        student_name=request.student_name,
        concept_code=request.concept_code,
        weak_bloom_level=request.weak_bloom_level,
        target_language=request.target_language,
    )
    return success_response(result)

@router.post(
    "/parent-advisory/send-voice-note",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.TEACHER, UserRole.DISTRICT_ADMIN, UserRole.ADMIN]))],
)
def dispatch_parent_voice_note(
    request: SendParentAdvisoryRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generates and dispatches a 45-second mother-tongue audio advisory note for non-literate parents."""
    result = service.dispatch_parent_voice_note(
        student_id=request.student_id,
        student_name=request.student_name,
        parent_phone=request.parent_phone,
        concept_code=request.concept_code,
        target_language=request.target_language,
        target_dialect=request.target_dialect,
    )
    return success_response(result)

@router.get(
    "/interventions/pending",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.DISTRICT_ADMIN, UserRole.ADMIN]))],
)
def list_pending_remedial_interventions(
    current_user: dict = Depends(get_current_user),
):
    """Returns active remedial intervention pathways queued across schools."""
    pending = service.get_pending_interventions()
    return success_response({
        "total_pending_interventions": len(pending),
        "interventions": pending,
    })

@router.get(
    "/analytics/overview",
    response_model=dict,
    dependencies=[Depends(require_roles([UserRole.DISTRICT_ADMIN, UserRole.ADMIN]))],
)
def get_district_admin_overview(
    current_user: dict = Depends(get_current_user),
):
    """Returns high-level administrative KPIs across all tribal schools in the district."""
    overview = service.get_district_overview()
    return success_response(overview)
