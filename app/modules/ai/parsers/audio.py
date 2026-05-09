import tempfile
import os

def transcribe_audio(content: bytes, filename: str) -> str:
    import whisper
    from app.config import get_settings
    settings = get_settings()
    model = whisper.load_model(settings.whisper_model)
    suffix = os.path.splitext(filename)[1] or ".mp3"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(content)
        tmp_path = f.name
    try:
        result = model.transcribe(tmp_path)
        return result["text"]
    finally:
        os.unlink(tmp_path)
