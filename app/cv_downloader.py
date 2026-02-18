import re
import requests
from pathlib import Path

CV_DIR = Path("data/cvs")
CV_DIR.mkdir(parents=True, exist_ok=True)


def extract_drive_file_id(url: str) -> str | None:
    """
    Correctly extracts file ID from:
    https://drive.google.com/file/d/<ID>/view
    """
    if not url:
        return None

    import re

    match = re.search(r"/file/d/([^/]+)", url)
    if match:
        return match.group(1)

    match = re.search(r"[?&]id=([^&]+)", url)
    if match:
        return match.group(1)

    return None



def download_cv(cv_url: str, candidate_name: str) -> Path | None:
    print("📎 CV URL:", cv_url)

    file_id = extract_drive_file_id(cv_url)
    if not file_id:
        print("❌ Could not extract file ID")
        return None

    session = requests.Session()
    response = session.get(
        "https://drive.google.com/uc",
        params={"id": file_id, "export": "download"},
        stream=True,
        timeout=30,
    )

    # Handle Google Drive virus scan confirmation
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            response = session.get(
                "https://drive.google.com/uc",
                params={
                    "id": file_id,
                    "export": "download",
                    "confirm": value,
                },
                stream=True,
                timeout=30,
            )

    if response.status_code != 200:
        print("❌ Download failed, status:", response.status_code)
        return None

    content_type = response.headers.get("Content-Type", "").lower()
    ext = ".pdf" if "pdf" in content_type else ".docx"

    filename = candidate_name.replace(" ", "_") + ext
    filepath = CV_DIR / filename

    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)

    print("✅ CV saved to:", filepath)
    return filepath
