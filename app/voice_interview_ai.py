import requests, json, re
from app.config import settings

def evaluate_voice_answer(transcript, role):
    prompt = f"""
Evaluate the answer for role {role}

Score from 1 to 10:
communication
clarity
confidence
role_fit

Return only JSON
"""

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Return strict JSON"},
            {"role": "user", "content": transcript}
        ],
        "temperature": 0
    }

    response = requests.post(
        f"{settings.GROQ_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload
    )

    content = response.json()["choices"][0]["message"]["content"]
    match = re.search(r"\{.*\}", content, re.DOTALL)

    return json.loads(match.group())
