import requests
from app.config import settings

RESEND_URL = "https://api.resend.com/emails"

HEADERS = {
    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
    "Content-Type": "application/json"
}

def send_email(to_email, subject, html):
    payload = {
        "from": settings.FROM_EMAIL,
        "to": [to_email],
        "reply_to": settings.REPLY_TO_EMAIL,
        "subject": subject,
        "html": html
    }

    response = requests.post(
        RESEND_URL,
        headers=HEADERS,
        json=payload,
        timeout=30
    )

    if response.status_code != 200:
        print("Email failed:", response.text)

    return response.status_code == 200
