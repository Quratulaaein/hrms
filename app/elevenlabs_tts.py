import os
import requests

def generate_speech(text: str) -> bytes:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVEN_VOICE_ID")

    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY missing")

    if not voice_id:
        raise RuntimeError("ELEVEN_VOICE_ID missing")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }

    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1"
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    print("ELEVEN KEY PRESENT:", bool(api_key))


    return response.content

