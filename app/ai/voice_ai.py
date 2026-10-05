from typing import Optional, List, Dict, Any
from app.ai.aaroh_ai_adapter import ai_adapter
from app.core.exceptions import AIProcessingError
from app.core.logging import logger

class VoiceAI:
    def __init__(self):
        self.pipeline = ai_adapter.voice_pipeline

    def synthesize_text(
        self,
        text: str,
        section_name: str = "custom",
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
    ):
        try:
            return self.pipeline.synthesize_custom_text(
                text=text,
                section_name=section_name,
                target_language=target_language,
                target_dialect=target_dialect,
            )
        except Exception as e:
            logger.error(f"Voice synthesis failed: {e}")
            raise AIProcessingError(message=f"Voice synthesis error: {str(e)}")

    def generate_voice_lesson(
        self,
        concept_code: str,
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
        grade_level: int = 3,
    ):
        try:
            return self.pipeline.generate_voice_lesson(
                concept_code=concept_code,
                target_language=target_language,
                target_dialect=target_dialect,
                grade_level=grade_level,
            )
        except Exception as e:
            logger.error(f"Voice lesson generation failed: {e}")
            raise AIProcessingError(message=f"Voice lesson generation error: {str(e)}")

    def process_oral_quiz_answer(
        self,
        quiz_id: str,
        question_id: str,
        student_id: str,
        audio_file_path: str,
        expected_answer: str,
        target_language: str = "hi",
    ):
        try:
            return self.pipeline.process_oral_quiz_answer(
                quiz_id=quiz_id,
                question_id=question_id,
                student_id=student_id,
                audio_file_path=audio_file_path,
                expected_answer=expected_answer,
                target_language=target_language,
            )
        except Exception as e:
            logger.error(f"Oral quiz assessment failed: {e}")
            raise AIProcessingError(message=f"Oral quiz assessment error: {str(e)}")

    def transcribe_audio(
        self,
        audio_file_path: str,
        language_code: str = "hi",
    ):
        try:
            return self.pipeline.stt.transcribe_audio(
                audio_file_path=audio_file_path,
                hint_language=language_code,
            )
        except Exception as e:
            logger.error(f"Speech transcription failed: {e}")
            raise AIProcessingError(message=f"Speech transcription error: {str(e)}")

voice_ai = VoiceAI()
