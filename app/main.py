from fastapi import FastAPI, UploadFile, File, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd
import uuid
import os
import re
import requests
import asyncio
from datetime import datetime

from app.database import SessionLocal
from app.models import Candidate, InterviewAnswer
from app.cv_parser import parse_cv
from app.resume_ai import parse_resume_with_ai
from app.matcher import score_candidate
from app.jd_engine import get_jd_requirements
from app.interview_question_generator import generate_questions
from app.config import settings

app = FastAPI()

# enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

CV_THRESHOLD = 50
BASIC_THRESHOLD = 20


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def download_cv_from_drive(url: str):
    match = re.search(r'/d/([^/]+)', url)
    if not match:
        return None

    file_id = match.group(1)
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(download_url)

    if response.status_code != 200:
        return None

    file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.pdf")
    with open(file_path, "wb") as f:
        f.write(response.content)

    return file_path


# safe ai call with retry
async def safe_ai_parse(resume_text):
    for attempt in range(5):
        try:
            return parse_resume_with_ai(resume_text[:3000])
        except Exception as e:
            if "rate_limit" in str(e):
                await asyncio.sleep(3 + attempt * 2)
            else:
                raise e
    return None


def upsert_ghl_contact(name, email, phone, interview_link, score, username, password):
    base_url = settings.GHL_API_BASE

    headers = {
        "Authorization": f"Bearer {settings.GHL_API_KEY}",
        "Version": "2021-07-28",
        "Content-Type": "application/json"
    }

    first = name.split()[0]
    last = " ".join(name.split()[1:]) if len(name.split()) > 1 else ""

    payload = {
        "firstName": first,
        "lastName": last,
        "email": email,
        "phone": phone,
        "locationId": settings.GHL_LOCATION_ID,
        "customFields": [
            {"id": settings.GHL_SCORE_FIELD_ID, "value": str(score)},
            {"id": settings.GHL_LINK_FIELD_ID, "value": interview_link},
            {"id": settings.GHL_USERNAME_FIELD_ID, "value": username},
            {"id": settings.GHL_PASSWORD_FIELD_ID, "value": password},
        ]
    }

    try:
        # Step 1: Try to find existing contact by email
        contact_id = None

        search = requests.get(
            f"{base_url}/contacts/",
            headers=headers,
            params={
                "locationId": settings.GHL_LOCATION_ID,
                "query": email
            },
            timeout=15
        )

        if search.status_code == 200:
            contacts = search.json().get("contacts", [])
            for c in contacts:
                if c.get("email", "").lower() == email.lower():
                    contact_id = c.get("id")
                    break

        # Step 2: Update if found, create if not
        if contact_id:
            response = requests.put(
                f"{base_url}/contacts/{contact_id}",
                headers=headers,
                json=payload,
                timeout=15
            )
            print(f"GHL UPDATE STATUS: {response.status_code}")
            print(f"GHL UPDATE RESPONSE: {response.text}")

        else:
            response = requests.post(
                f"{base_url}/contacts/",
                headers=headers,
                json=payload,
                timeout=15
            )
            print(f"GHL CREATE STATUS: {response.status_code}")
            print(f"GHL CREATE RESPONSE: {response.text}")

            # Step 3: If POST fails due to duplicate, extract contactId and update
            if response.status_code == 400:
                resp_data = response.json()
                fallback_id = resp_data.get("meta", {}).get("contactId")

                if fallback_id:
                    print(f"GHL duplicate detected, updating existing contact: {fallback_id}")
                    update_response = requests.put(
                        f"{base_url}/contacts/{fallback_id}",
                        headers=headers,
                        json=payload,
                        timeout=15
                    )
                    print(f"GHL FALLBACK UPDATE STATUS: {update_response.status_code}")
                    print(f"GHL FALLBACK UPDATE RESPONSE: {update_response.text}")

    except Exception as e:
        print("GHL ERROR:", str(e))
              
@app.get("/")
def root():
    return {"status": "HRMS ATS running"}


@app.post("/excel/upload")
async def upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):

    excel_data = pd.read_excel(file.file, sheet_name=None)

    SALES_ALIGNMENT = [
        "sales", "b2b", "lead generation",
        "cold calling", "client acquisition",
        "outreach", "prospecting"
    ]

    for sheet_name, df in excel_data.items():

        if sheet_name.strip().lower() == "jd":
            continue

        df.columns = df.columns.str.strip().str.lower()

        for _, row in df.iterrows():
            try:
                name = row.get("applicant name") or row.get("name")
                email = row.get("email")
                phone = row.get("mobile") or ""
                cv_url = row.get("cv url") or row.get("cv")
                role = sheet_name.strip()

                if not name or not email or not cv_url:
                    continue

                local_cv = download_cv_from_drive(cv_url)
                if not local_cv:
                    continue

                resume_text = parse_cv(local_cv)
                resume_lower = resume_text.lower()

                

                score = 0

                matched_keywords = []

                # If basic sales word present → base 50
                if any(k in resume_lower for k in SALES_ALIGNMENT):
                    score = 50

                # Add +5 per matched keyword
                for k in SALES_ALIGNMENT:
                    if k in resume_lower:
                        matched_keywords.append(k)
                        score += 5

                # Experience bonus
                exp_match = re.search(r'(\d+)\s+years', resume_lower)
                if exp_match:
                    years = int(exp_match.group(1))
                    if years >= 2:
                        score += 5

                # Cap score at 75
                score = min(score, 75)


                if score < 45:
                    status = "rejected"
                elif 45 <= score < 50:
                    status = "alternate"
                elif 50 <= score < 60:
                    status = "shortlisted"
                else:
                    status = "shortlisted"

                username = email
                password = str(uuid.uuid4())[:8]

                candidate = Candidate(
                    id=str(uuid.uuid4()),
                    name=name,
                    email=email,
                    phone=phone,
                    role=role,
                    username=username,
                    password=password,
                    cv_score=score,
                    status=status,
                    created_at=datetime.utcnow()
                )

                db.add(candidate)
                db.commit()

                # Send to GHL only if shortlisted
                if status == "shortlisted":
                    link = f"{settings.HR_INTERVIEW_CALENDAR}/login"
                    upsert_ghl_contact(
                        name=name,
                        email=email,
                        phone=phone,
                        interview_link=link,
                        score=score,
                        username=username,
                        password=password
                    )

            except Exception as e:
                print("Row failed:", e)
                continue

    return {"message": "Excel processed successfully"}

@app.get("/login", response_class=HTMLResponse)
def login_page():
    return """
    <html>
    <body>
        <h2>Candidate Login</h2>
        <form method="post">
            Email:<br>
            <input type="text" name="username"><br><br>
            Password:<br>
            <input type="password" name="password"><br><br>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """


@app.post("/login")
def login_user(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter_by(username=username, password=password).first()

    if not candidate:
        return {"error": "Invalid credentials"}

    return RedirectResponse(
        url=f"/ai-interview/{candidate.id}/{candidate.role}",
        status_code=302
    )


@app.get("/ai-interview/{candidate_id}/{role}", response_class=HTMLResponse)
def interview_page(candidate_id: str, role: str, db: Session = Depends(get_db)):

    existing = db.query(InterviewAnswer).filter_by(candidate_id=candidate_id).first()

    if not existing:
        questions = generate_questions(role)
        for i, q in enumerate(questions):
            db.add(InterviewAnswer(
                candidate_id=candidate_id,
                question_number=i + 1,
                question_text=q
            ))
        db.commit()

    return f"""
    <html>
    <body>
        <h2>AI Interview - {role}</h2>
        <video id="video" width="400" autoplay muted></video>
        <h3 id="question"></h3>
        <h4 id="timer">Time: 120</h4>

        <button onclick="startRecording()">Start Answer</button>
        <button onclick="stopRecording()">Stop Answer</button>

        <script>
        let mediaRecorder;
        let chunks = [];
        let currentStream;
        let timerInterval;
        let timeLeft = 120;

        async function loadQuestion() {{
            const res = await fetch("/interview/question/{candidate_id}");
            const data = await res.json();

            if (data.finished) {{
                document.getElementById("question").innerText =
                "Interview completed. You may close this window.";
                document.getElementById("timer").innerText = "";
                return;
            }}

            document.getElementById("question").innerText = data.question;
        }}

        async function startCamera() {{
            currentStream = await navigator.mediaDevices.getUserMedia({{
                video: true,
                audio: true
            }});
            document.getElementById("video").srcObject = currentStream;
        }}

        function startTimer() {{
            timeLeft = 120;
            document.getElementById("timer").innerText = "Time: " + timeLeft;

            timerInterval = setInterval(() => {{
                timeLeft--;
                document.getElementById("timer").innerText = "Time: " + timeLeft;

                if(timeLeft <= 0) {{
                    clearInterval(timerInterval);
                    stopRecording();
                }}
            }}, 1000);
        }}

        function startRecording() {{
            chunks = [];
            mediaRecorder = new MediaRecorder(currentStream);
            mediaRecorder.ondataavailable = e => chunks.push(e.data);
            mediaRecorder.onstop = sendAnswer;
            mediaRecorder.start();
            startTimer();
        }}

        function stopRecording() {{
            if(mediaRecorder && mediaRecorder.state !== "inactive") {{
                mediaRecorder.stop();
            }}
        }}

        async function sendAnswer() {{
            const blob = new Blob(chunks, {{ type: "video/webm" }});
            const formData = new FormData();
            formData.append("file", blob);

            await fetch("/interview/answer/{candidate_id}", {{
                method: "POST",
                body: formData
            }});

            loadQuestion();
        }}

        startCamera();
        loadQuestion();
        </script>
    </body>
    </html>
    """