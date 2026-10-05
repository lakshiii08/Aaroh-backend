from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from app.services.voice_service import VoiceService
from app.schemas.voice_schemas import (
    TextToSpeechRequest,
    VoiceLessonRequest,
)
from app.schemas.common_schemas import success_response
from app.api.deps import get_optional_current_user

router = APIRouter(prefix="/voice", tags=["Voice & Speech Intelligence"])

service = VoiceService()

@router.post("/synthesize", response_model=dict)
def synthesize_speech(
    request: TextToSpeechRequest,
    current_user: dict = Depends(get_optional_current_user),
):
    """Synthesizes text into a localized audio explanation (AWS Polly / local synth)."""
    result = service.synthesize_speech(
        text=request.text,
        section_name=request.section_name,
        target_language=request.target_language,
        target_dialect=request.target_dialect,
    )
    return success_response(result)

@router.post("/lessons/{concept_code}", response_model=dict)
def generate_voice_lesson(
    concept_code: str,
    request: VoiceLessonRequest,
    current_user: dict = Depends(get_optional_current_user),
):
    """Generates a complete voice lesson package (Explanation, Story, and Voice Script) for a concept."""
    result = service.generate_voice_lesson(
        concept_code=concept_code,
        target_language=request.target_language,
        target_dialect=request.target_dialect,
        grade_level=request.grade_level,
    )
    return success_response(result)

@router.post("/stt", response_model=dict)
@router.post("/transcribe", response_model=dict)
async def speech_to_text(
    audio_file: UploadFile = File(...),
    language_code: str = Form("hi"),
    current_user: dict = Depends(get_optional_current_user),
):
    """Transcribes oral student speech to Indic text using Whisper/Vosk."""
    result = await service.transcribe_speech(
        audio_file=audio_file,
        language_code=language_code,
    )
    return success_response(result)

@router.post("/oral-quiz/submit-audio", response_model=dict)
async def submit_oral_quiz_audio(
    quiz_id: str = Form(...),
    question_id: str = Form(...),
    student_id: str = Form(...),
    expected_answer: str = Form(...),
    target_language: str = Form("hi"),
    audio_file: UploadFile = File(...),
    current_user: dict = Depends(get_optional_current_user),
):
    """Submits student spoken audio file for oral quiz assessment.
    Runs Speech-to-Text → Grades against expected answer → Returns verbal feedback audio track.
    """
    result = await service.process_oral_quiz_audio(
        quiz_id=quiz_id,
        question_id=question_id,
        student_id=student_id,
        expected_answer=expected_answer,
        target_language=target_language,
        audio_file=audio_file,
    )
    return success_response(result)

@router.get("/stream/{filename}")
def stream_audio(filename: str):
    """Streams a generated audio file (.wav or .mp3) directly to client browser/device."""
    file_path = service.resolve_audio_file(filename)
    media_type = "audio/mpeg" if file_path.suffix == ".mp3" else "audio/wav"
    return FileResponse(path=file_path, media_type=media_type, filename=filename)
