import requests
import json
import re
from app.config import settings


GROQ_URL = f"{settings.GROQ_BASE_URL}/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
    "Content-Type": "application/json",
}

SALES_KEYWORDS = [
    "sales", "business development", "bdm", "lead generation",
    "lead gen", "outreach", "cold calling", "client acquisition",
    "inside sales", "sdr", "bdr", "relationship", "account executive",
    "growth", "pre-sales"
]

def normalize_sales(profile: dict) -> dict:
    text = " ".join([
        str(profile.get("current_role", "")),
        " ".join(profile.get("key_skills") or []),
        " ".join(profile.get("domains") or [])
    ]).lower()

    profile["is_sales_profile"] = any(k in text for k in SALES_KEYWORDS)
    return profile


def parse_resume_with_ai(resume_text: str) -> dict:
    resume_text = resume_text[:6000]

    prompt = f"""
Return ONLY valid JSON.

Fields:
- total_experience_years
- current_role
- sales_type
- domains
- key_skills
- tools
- crm_tools
- strengths
- red_flags

Resume:
\"\"\"{resume_text}\"\"\"
"""

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Return strict JSON only"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "max_tokens": 800
    }

    response = requests.post(GROQ_URL, headers=HEADERS, json=payload, timeout=60)

    if response.status_code != 200:
        raise Exception(response.text)

    content = response.json()["choices"][0]["message"]["content"]

    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise ValueError("Invalid LLM output")

    profile = json.loads(match.group())
    return normalize_sales(profile)
