from pathlib import Path
import pdfplumber
from docx import Document

def is_probably_pdf(file_path: Path) -> bool:
    with open(file_path, "rb") as f:
        return f.read(4) == b"%PDF"

def parse_pdf(file_path: Path) -> str:
    text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)

def parse_docx(file_path: Path) -> str:
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def parse_cv(file_path: str) -> str:
    path = Path(file_path)

    if is_probably_pdf(path):
        return parse_pdf(path)

    if path.suffix.lower() == ".docx":
        return parse_docx(path)

    raise ValueError("Unsupported CV format")
