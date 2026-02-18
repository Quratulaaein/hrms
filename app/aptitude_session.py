from datetime import datetime

def create_aptitude_session(candidate_id, questions):
    return {
        "candidate_id": candidate_id,
        "questions": questions,
        "answers": {},
        "marked_for_review": [],
        "camera_on": False,
        "mic_on": False,
        "screen_share_detected": False,
        "start_time": datetime.utcnow(),
        "submitted": False
    }
