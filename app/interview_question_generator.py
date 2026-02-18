from google import genai
from app.config import settings
from app.jd_engine import get_jd_requirements

client = genai.Client(api_key=settings.GEMINI_API_KEY)

TOTAL_QUESTIONS = 5


def generate_questions(role: str):

    role_key = role.strip().lower()

    jd_dict = {
        k.lower(): v
        for k, v in get_jd_requirements().items()
    }

    jd_data = jd_dict.get(role_key)

    if not jd_data:
        print("JD not found for role:", role)
        return [f"General question {i}" for i in range(1, TOTAL_QUESTIONS + 1)]

    prompt = f"""
Generate exactly {TOTAL_QUESTIONS} interview questions for the role: {role}

Role requirements:
Skills: {jd_data['required_skills']}
Tools: {jd_data['tools']}
Minimum Experience: {jd_data['min_exp']} years

Rules:
- Mix technical and behavioral
- Practical and scenario based
- Output only plain list of questions
- No explanations
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        text = response.text.strip()

        lines = [l.strip() for l in text.split("\n") if l.strip()]

        questions = []

        for line in lines:
            clean = line.lstrip("0123456789). -•")
            if len(clean) > 10:
                questions.append(clean.strip())

        if len(questions) >= TOTAL_QUESTIONS:
            return questions[:TOTAL_QUESTIONS]

    except Exception as e:
        print("Gemini question generation failed:", e)

    return [f"General question {i}" for i in range(1, TOTAL_QUESTIONS + 1)]
