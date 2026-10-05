from pathlib import Path
from typing import Optional, List, Dict, Any
from app.ai.aaroh_ai_adapter import ai_adapter
from app.core.exceptions import NotFoundError
from app.core.logging import logger

class GamificationService:
    def __init__(self):
        self.pipeline = ai_adapter.gamification_pipeline

    def generate_nature_quest(
        self,
        concept_code: str,
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
    ) -> Dict[str, Any]:
        quest = self.pipeline.generate_concept_quest(
            concept_code=concept_code,
            target_language=target_language,
            target_dialect=target_dialect,
        )
        return {
            "quest_id": quest.quest_id,
            "concept_code": quest.concept_code,
            "title": quest.title,
            "story_mission": quest.story_mission,
            "action_prompt": quest.action_prompt,
            "reward_xp": quest.reward_xp,
            "badge_unlock": quest.badge_unlock,
        }

    def record_activity(
        self,
        student_id: str,
        student_name: str,
        school_id: str,
        grade_level: int,
        activity_type: str,
        concept_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.pipeline.record_student_activity(
            student_id=student_id,
            student_name=student_name,
            school_id=school_id,
            grade_level=grade_level,
            activity_type=activity_type,
            concept_code=concept_code,
        )

    def get_student_portfolio(self, student_id: str) -> Dict[str, Any]:
        portfolio = self.pipeline.get_student_portfolio(student_id=student_id)
        return {
            "student_id": portfolio.student_id,
            "student_name": portfolio.student_name,
            "school_id": portfolio.school_id,
            "grade_level": portfolio.grade_level,
            "total_xp": portfolio.total_xp,
            "level": portfolio.level,
            "current_streak_days": portfolio.current_streak_days,
            "completed_quests_count": portfolio.completed_quests_count,
            "concepts_mastered": portfolio.concepts_mastered,
            "badges_count": len(portfolio.badges),
            "badges": [
                {
                    "badge_id": b.badge_id,
                    "badge_name": b.badge_name,
                    "title_local": b.title_local,
                    "description": b.description,
                    "icon": b.icon_symbol,
                    "tier": b.tier,
                }
                for b in portfolio.badges
            ],
        }

    def generate_flashcards(
        self,
        concept_code: str,
        target_language: str = "hi",
        target_dialect: Optional[str] = "gon",
    ) -> Dict[str, Any]:
        deck = self.pipeline.generate_flashcard_deck(
            concept_code=concept_code,
            target_language=target_language,
            target_dialect=target_dialect,
        )
        filename = Path(deck["html_deck_path"]).name
        return {
            "concept_code": deck["concept_code"],
            "concept_name": deck["concept_name"],
            "total_cards": deck["total_cards"],
            "printable_deck_url": f"/api/v1/gamification/flashcards/deck/{filename}",
            "cards": deck["cards"],
        }

    def resolve_flashcard_html(self, filename: str) -> str:
        local_dir = Path("data/flashcards")
        candidate = local_dir / filename
        if candidate.exists():
            with open(candidate, "r", encoding="utf-8") as f:
                return f.read()

        from app.core.config import settings
        ai_candidate = Path(settings.AAROH_AI_PATH) / "data" / "flashcards" / filename
        if ai_candidate.exists():
            with open(ai_candidate, "r", encoding="utf-8") as f:
                return f.read()

        raise NotFoundError(message=f"Flashcard deck '{filename}' not found.", code="DECK_NOT_FOUND")

    def get_school_leaderboard(self, school_id: str) -> List[Dict[str, Any]]:
        return self.pipeline.get_school_leaderboard(school_id=school_id)
