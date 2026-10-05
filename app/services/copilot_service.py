from pathlib import Path
from typing import Optional, List, Dict, Any
from app.ai.copilot_ai import copilot_ai
from app.core.exceptions import NotFoundError
from app.core.logging import logger

class CopilotService:
    def generate_lesson_plan(
        self,
        concept_code: str,
        grade_level: int = 3,
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
        duration_mins: int = 45,
    ) -> Dict[str, Any]:
        plan = copilot_ai.generate_lesson_plan(
            concept_code=concept_code,
            grade_level=grade_level,
            target_language=target_language,
            target_dialect=target_dialect,
            duration_mins=duration_mins,
        )
        return {
            "plan_id": plan.plan_id,
            "title": plan.title,
            "grade_level": plan.grade_level,
            "target_language": plan.target_language,
            "time_allocation_mins": plan.time_allocation_mins,
            "multigrade_strategies": plan.multigrade_strategies,
            "blackboard_activity": plan.blackboard_activity,
            "teaching_aids": plan.teaching_aids,
            "hands_on_experiments": plan.hands_on_experiments,
            "homework_village_inquiry": plan.homework_village_inquiry,
        }

    def generate_remedial_aid(
        self,
        concept_code: str,
        weak_bloom_level: str = "Understand",
        target_language: str = "hi",
    ) -> Dict[str, Any]:
        aid = copilot_ai.generate_remedial_aid(
            concept_code=concept_code,
            weak_bloom_level=weak_bloom_level,
            target_language=target_language,
        )
        return {
            "aid_id": aid.aid_id,
            "concept_code": aid.concept_code,
            "concept_name": aid.concept_name,
            "identified_gap_summary": aid.identified_gap_summary,
            "simplified_activity": aid.simplified_activity,
            "story_analogy": aid.story_analogy,
            "check_questions": aid.check_questions,
            "printable_guide": aid.printable_guide,
        }

    def export_offline_package(
        self,
        grade_level: int = 3,
        subject: str = "Environmental Studies",
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
    ) -> Dict[str, Any]:
        pkg = copilot_ai.export_offline_bundle(
            grade_level=grade_level,
            subject=subject,
            target_language=target_language,
            target_dialect=target_dialect,
        )
        zip_filename = Path(pkg.package_zip_path).name
        return {
            "package_id": pkg.package_id,
            "package_name": pkg.package_name,
            "grade_level": pkg.grade_level,
            "subject": pkg.subject,
            "target_language": pkg.target_language,
            "total_lessons": pkg.total_lessons,
            "total_quizzes": pkg.total_quizzes,
            "total_audio_files": pkg.total_audio_files,
            "package_size_bytes": pkg.package_size_bytes,
            "download_url": f"/api/v1/copilot/edge/packages/download/{zip_filename}",
        }

    def resolve_package_path(self, filename: str) -> Path:
        export_dir = Path("data/edge_packages")
        candidate = export_dir / filename
        if candidate.exists():
            return candidate

        from app.core.config import settings
        ai_candidate = Path(settings.AAROH_AI_PATH) / "data" / "edge_packages" / filename
        if ai_candidate.exists():
            return ai_candidate

        raise NotFoundError(message=f"Offline package '{filename}' not found.", code="PACKAGE_NOT_FOUND")

    def sync_offline_attempts(self, batch_payload: Dict[str, Any]) -> Dict[str, Any]:
        sync_result = copilot_ai.sync_offline_attempts(batch_payload)
        return {
            "batch_id": sync_result.batch_id,
            "device_id": sync_result.device_id,
            "school_id": sync_result.school_id,
            "total_synced_submissions": sync_result.total_submissions,
            "synced_at": sync_result.synced_at.isoformat(),
        }

    def get_classroom_mastery_heatmap(self) -> List[Dict[str, Any]]:
        return copilot_ai.get_classroom_mastery_heatmap()
