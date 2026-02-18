from pathlib import Path
from app.cv_parser import extract_cv_text
from app.resume_ai import parse_resume_with_ai

# Pick ANY file that actually exists
cv_path = Path("data/cvs/Yogesh_Sharma.docx")

text = extract_cv_text(cv_path)
profile = parse_resume_with_ai(text)

print(profile)
