from fastapi import FastAPI, UploadFile, File, Depends, BackgroundTasks, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import pandas as pd
import uuid
import shutil
import os
import re
import requests
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Candidate, InterviewAnswer
from app.cv_parser import parse_cv
from app.resume_ai import parse_resume_with_ai
from app.matcher import score_candidate
from app.jd_engine import get_jd_requirements
from app.interview_question_generator import generate_questions
from app.config import settings

app = FastAPI()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

CV_THRESHOLD = 50
TOTAL_QUESTIONS = 5


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


def upsert_ghl_contact(name, email, phone, interview_link, score, username, password):
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
            {"id": settings.GHL_PASSWORD_FIELD_ID, "value": password}
        ]
    }

    requests.post(settings.GHL_API_URL, headers=headers, json=payload)


@app.get("/")
def root():
    return {"status": "HRMS ATS running"}


@app.post("/excel/upload")
async def upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    df = pd.read_excel(file.file)
    jd_map = get_jd_requirements()

    for _, row in df.iterrows():
        name = row["Applicant Name"]
        email = row["Email"]
        phone = row.get("Mobile", "")
        role = row.get("Role", "Outbound Sales")
        cv_url = row["CV URL"]

        local_cv = download_cv_from_drive(cv_url)
        if not local_cv:
            continue

        resume_text = parse_cv(local_cv)
        profile = parse_resume_with_ai(resume_text)

        jd = jd_map.get(role)
        if not jd:
            continue

        cv_score, _ = score_candidate(profile, jd)

        username = email
        password = str(uuid.uuid4())[:8]

        candidate = Candidate(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            role=role,
            username=username,
            password=password,
            cv_score=cv_score,
            status="shortlisted" if cv_score >= CV_THRESHOLD else "rejected",
            interview_deadline=datetime.utcnow() + timedelta(days=3),
            created_at=datetime.utcnow()
        )

        db.add(candidate)
        db.commit()

        if cv_score >= CV_THRESHOLD:
            link = "https://yourdomain.com/login"
            upsert_ghl_contact(
                name=name,
                email=email,
                phone=phone,
                interview_link=link,
                score=0,
                username=username,
                password=password
            )

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
                question_number=i+1,
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
                "Thank you for completing the interview. Please close this window.";
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


@app.get("/interview/question/{candidate_id}")
def get_question(candidate_id: str, db: Session = Depends(get_db)):
    answers = db.query(InterviewAnswer)\
        .filter_by(candidate_id=candidate_id)\
        .order_by(InterviewAnswer.question_number)\
        .all()

    answered = len([a for a in answers if a.audio_path])

    if answered >= TOTAL_QUESTIONS:
        return {"finished": True}

    return {"question": answers[answered].question_text}


@app.post("/interview/answer/{candidate_id}")
async def save_answer(
    candidate_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    answers = db.query(InterviewAnswer)\
        .filter_by(candidate_id=candidate_id)\
        .order_by(InterviewAnswer.question_number)\
        .all()

    current = len([a for a in answers if a.audio_path])

    if current >= TOTAL_QUESTIONS:
        return {"message": "Already completed"}

    file_path = os.path.join(UPLOAD_FOLDER, f"{candidate_id}_{current+1}.webm")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    answer = answers[current]
    answer.audio_path = file_path
    db.commit()

    return {"message": "Answer saved"}


@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(db: Session = Depends(get_db)):
    candidates = db.query(Candidate).all()

    html = "<h2>Admin Dashboard</h2><br>"

    for c in candidates:
        html += f"<b>{c.name}</b> | {c.status} | "
        html += f"<a href='/admin/recordings/{c.id}'>View Recordings</a><br><br>"

    return html


@app.get("/admin/recordings/{candidate_id}", response_class=HTMLResponse)
def view_recordings(candidate_id: str, db: Session = Depends(get_db)):
    answers = db.query(InterviewAnswer).filter_by(candidate_id=candidate_id).all()

    html = "<h3>Interview Recordings</h3><br>"

    for a in answers:
        if a.audio_path:
            html += f"""
            Question {a.question_number}<br>
            <video width="400" controls>
                <source src="/uploads/{os.path.basename(a.audio_path)}" type="video/webm">
            </video><br><br>
            """

    return html
