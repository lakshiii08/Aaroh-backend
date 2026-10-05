from typing import Optional, Dict, Any, List
from app.ai.assessment_ai import assessment_ai
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.jwt import UserRole
from app.core.logging import logger

class AssessmentService:
    def generate_quiz(
        self,
        concept_code: str,
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
        grade_level: int = 3,
    ) -> Dict[str, Any]:
        quiz = assessment_ai.generate_quiz(
            concept_code=concept_code,
            target_language=target_language,
            target_dialect=target_dialect,
            grade_level=grade_level,
        )
        return {
            "quiz_id": quiz.quiz_id,
            "concept_code": quiz.concept_code,
            "concept_name": quiz.concept_name,
            "grade_level": quiz.grade_level,
            "target_language": quiz.target_language,
            "target_dialect": quiz.target_dialect,
            "total_questions": len(quiz.questions),
            "questions": [
                {
                    "question_id": q.question_id,
                    "question_type": q.question_type,
                    "question_text": q.question_text,
                    "options": q.options,
                    "blooms_level": q.blooms_level,
                    "difficulty_level": q.difficulty_level,
                    "cultural_anchor": q.cultural_anchor,
                }
                for q in quiz.questions
            ],
        }

    def submit_quiz_and_assess(
        self,
        quiz_id: str,
        student_id: str,
        answers: Dict[str, str],
        current_user: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Submits answers, scores against expected responses, runs Bayesian knowledge gap analysis,
        and logs to PostgreSQL.
        Enforces that student can only submit for themselves.
        """
        role = current_user.get("role")
        if role == UserRole.STUDENT:
            # Student can only submit for their own user_id or matching student_id
            user_id = current_user.get("user_id")
            if student_id != user_id and not user_id.endswith(student_id):
                student_id = user_id

        result = assessment_ai.submit_and_assess_quiz(
            quiz_id=quiz_id,
            student_id=student_id,
            answers=answers,
        )
        return result

    def get_student_history(
        self,
        student_id: str,
        current_user: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Retrieves past quiz submissions with strict student-level isolation."""
        role = current_user.get("role")
        user_id = current_user.get("user_id")

        if role == UserRole.STUDENT and student_id != user_id and not user_id.endswith(student_id):
            raise ForbiddenError(message="Students are strictly isolated and cannot view another student's history.")

        return assessment_ai.get_student_history(student_id=student_id)

    def get_teacher_concept_report(self, concept_code: str) -> Dict[str, Any]:
        """Aggregates concept understanding, error patterns, and remedial suggestions for teachers."""
        return assessment_ai.get_class_report(concept_code=concept_code)
