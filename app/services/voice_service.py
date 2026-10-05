import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import UploadFile
from app.ai.voice_ai import voice_ai
from app.core.exceptions import NotFoundError
from app.core.logging import logger

class VoiceService:
    def synthesize_speech(
        self,
        text: str,
        section_name: str = "custom",
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
    ) -> Dict[str, Any]:
        segment = voice_ai.synthesize_text(
            text=text,
            section_name=section_name,
            target_language=target_language,
            target_dialect=target_dialect,
        )
        audio_filename = Path(segment.audio_file_path).name
        return {
            "segment_id": segment.segment_id,
            "section_name": segment.section_name,
            "duration_seconds": segment.duration_seconds,
            "format": segment.format,
            "voice_id": segment.voice_id,
            "audio_file_path": segment.audio_file_path,
            "stream_url": f"/api/v1/voice/stream/{audio_filename}",
        }

    def generate_voice_lesson(
        self,
        concept_code: str,
        target_language: str = "hi",
        target_dialect: Optional[str] = None,
        grade_level: int = 3,
    ) -> Dict[str, Any]:
        pkg = voice_ai.generate_voice_lesson(
            concept_code=concept_code,
            target_language=target_language,
            target_dialect=target_dialect,
            grade_level=grade_level,
        )
        return {
            "concept_code": pkg.concept_code,
            "concept_name": pkg.concept_name,
            "target_language": pkg.target_language,
            "target_dialect": pkg.target_dialect,
            "total_duration_seconds": pkg.total_duration_seconds,
            "audio_segments": [
                {
                    "segment_id": s.segment_id,
                    "section_name": s.section_name,
                    "duration_seconds": s.duration_seconds,
                    "audio_file_path": s.audio_file_path,
                    "stream_url": f"/api/v1/voice/stream/{Path(s.audio_file_path).name}",
                }
                for s in pkg.segments
            ],
        }

    async def transcribe_speech(self, audio_file: UploadFile, language_code: str = "hi") -> Dict[str, Any]:
        temp_dir = Path("data/uploads/audio")
        temp_dir.mkdir(parents=True, exist_ok=True)
        local_audio_path = temp_dir / audio_file.filename

        with open(local_audio_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        transcription = voice_ai.transcribe_audio(
            audio_file_path=str(local_audio_path),
            language_code=language_code,
        )

        return {
            "transcribed_text": transcription.transcribed_text,
            "detected_language": transcription.detected_language,
            "confidence_score": transcription.confidence_score,
            "latency_ms": getattr(transcription, "latency_ms", 0.0),
            "audio_file_name": audio_file.filename,
        }

    async def process_oral_quiz_audio(
        self,
        quiz_id: str,
        question_id: str,
        student_id: str,
        expected_answer: str,
        target_language: str,
        audio_file: UploadFile,
    ) -> Dict[str, Any]:
        temp_dir = Path("data/uploads/audio")
        temp_dir.mkdir(parents=True, exist_ok=True)
        local_audio_path = temp_dir / audio_file.filename

        with open(local_audio_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        result = voice_ai.process_oral_quiz_answer(
            quiz_id=quiz_id,
            question_id=question_id,
            student_id=student_id,
            audio_file_path=str(local_audio_path),
            expected_answer=expected_answer,
            target_language=target_language,
        )

        feedback_filename = Path(result.feedback_audio_path).name if result.feedback_audio_path else None

        return {
            "student_id": result.student_id,
            "question_id": result.question_id,
            "transcribed_speech": result.transcribed_speech,
            "expected_answer": result.expected_answer,
            "is_correct": result.is_correct,
            "confidence_score": result.confidence_score,
            "feedback_script": result.feedback_audio_script,
            "feedback_audio_url": f"/api/v1/voice/stream/{feedback_filename}" if feedback_filename else None,
        }

    def resolve_audio_file(self, filename: str) -> Path:
        """Finds audio file across generated audio directory and uploads directory."""
        from app.core.config import settings
        audio_dir = Path("data/audio")
        candidate = audio_dir / filename
        if candidate.exists():
            return candidate

        # Check in Aaroh-AI's audio dir
        ai_audio = Path(settings.AAROH_AI_PATH) / "data" / "audio" / filename
        if ai_audio.exists():
            return ai_audio

        # Check uploads
        upload_path = Path("data/uploads/audio") / filename
        if upload_path.exists():
            return upload_path

        raise NotFoundError(message=f"Audio file '{filename}' not found.", code="AUDIO_NOT_FOUND")
