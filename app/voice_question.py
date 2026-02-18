from elevenlabs.client import ElevenLabs
from pathlib import Path
from app.config import settings

client = ElevenLabs(
    api_key=settings.ELEVEN_LABS_API_KEY
)

AUDIO_DIR = Path("data/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

def speak_question(text, candidate_id, index):
    audio_stream = client.text_to_speech.convert(
        voice_id="21m00Tcm4TlvDq8ikWAM",
        model_id="eleven_multilingual_v2",
        text=text
    )

    path = AUDIO_DIR / f"{candidate_id}_q{index}.mp3"

    with open(path, "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)

    return str(path)
