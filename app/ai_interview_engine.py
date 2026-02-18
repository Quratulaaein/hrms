from openai import OpenAI
from app.config import settings
import json

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def transcribe_audio(file_path: str):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text


def evaluate_full_interview(qa_pairs: list):
    """
    qa_pairs = [
        {"question": "...", "answer": "..."},
        ...
    ]
    """

    formatted = ""
    for i, qa in enumerate(qa_pairs, start=1):
        formatted += f"\nQ{i}: {qa['question']}\nA{i}: {qa['answer']}\n"

    prompt = f"""
You are an AI interviewer.

Evaluate the entire interview.

{formatted}

Return ONLY valid JSON:
{{
  "technical": number (0-10),
  "relevance": number (0-10),
  "communication": number (0-10),
  "confidence": number (0-10),
  "summary": "short feedback paragraph"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content
    return json.loads(content)
