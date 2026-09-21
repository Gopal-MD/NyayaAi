"""Voice router: POST /voice/transcribe (Groq Whisper STT)"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.core.auth import CurrentUser
from app.core.config import settings
from app.models.schemas import TranscriptResponse

router = APIRouter()

ALLOWED_AUDIO = {".webm", ".mp3", ".wav", ".m4a", ".ogg"}
MAX_AUDIO_MB = 5


@router.post("/transcribe", response_model=TranscriptResponse)
async def transcribe_audio(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    language: str = "ta",
):
    import os
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_AUDIO:
        raise HTTPException(status_code=400, detail=f"Unsupported audio format '{ext}'.")

    content = await file.read(MAX_AUDIO_MB * 1024 * 1024 + 1)
    if len(content) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Audio exceeds {MAX_AUDIO_MB} MB limit.")

    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="Groq API key not configured.")

    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        import io
        audio_file = io.BytesIO(content)
        audio_file.name = file.filename or f"audio{ext}"

        transcription = client.audio.transcriptions.create(
            model=settings.GROQ_MODEL_WHISPER,
            file=audio_file,
            language=language if language != "ta" else None,  # Whisper auto-detects Tamil
            response_format="json",
        )
        return TranscriptResponse(
            transcript=transcription.text,
            language=language,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}")
