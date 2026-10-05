from typing import Optional, List, Dict, Any
from app.ai.aaroh_ai_adapter import ai_adapter
from app.core.logging import logger

class DistrictService:
    def __init__(self):
        self.pipeline = ai_adapter.district_pipeline

    def generate_remedial_pathway(
        self,
        student_id: str,
        student_name: str,
        concept_code: str,
        weak_bloom_level: str = "Understand",
        target_language: str = "hi",
    ) -> Dict[str, Any]:
        pathway = self.pipeline.generate_remedial_pathway(
            student_id=student_id,
            student_name=student_name,
            concept_code=concept_code,
            weak_bloom_level=weak_bloom_level,
            target_language=target_language,
        )
        return {
            "pathway_id": pathway.pathway_id,
            "student_id": pathway.student_id,
            "student_name": pathway.student_name,
            "concept_code": pathway.concept_code,
            "concept_name": pathway.concept_name,
            "weak_bloom_level": pathway.weak_bloom_level,
            "status_code": pathway.status,
            "steps": [
                {
                    "step_number": s.step_number,
                    "step_type": s.step_type,
                    "title": s.title,
                    "instruction": s.instruction,
                    "resource_url": s.resource_url,
                    "is_completed": s.is_completed,
                }
                for s in pathway.steps
            ],
        }

    def dispatch_parent_voice_note(
        self,
        student_id: str,
        student_name: str,
        parent_phone: str,
        concept_code: str,
        target_language: str = "hi",
        target_dialect: Optional[str] = "gon",
    ) -> Dict[str, Any]:
        advisory = self.pipeline.send_parent_voice_advisory(
            student_id=student_id,
            student_name=student_name,
            parent_phone=parent_phone,
            concept_code=concept_code,
            target_language=target_language,
            target_dialect=target_dialect,
        )
        return {
            "advisory_id": advisory.advisory_id,
            "student_id": advisory.student_id,
            "parent_phone": advisory.parent_phone,
            "target_language": advisory.target_language,
            "speech_script": advisory.speech_script,
            "audio_stream_url": advisory.stream_url,
            "dispatch_status": advisory.dispatch_status,
        }

    def get_pending_interventions(self) -> List[Dict[str, Any]]:
        return self.pipeline.get_pending_interventions()

    def get_district_overview(self) -> Dict[str, Any]:
        return self.pipeline.get_district_overview()
