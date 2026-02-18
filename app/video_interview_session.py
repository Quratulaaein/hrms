def create_video_session(candidate_id, questions):
    return {
        "candidate_id": candidate_id,
        "questions": questions,
        "current_index": 0,
        "submitted_answers": [],
        "camera_on": False,
        "mic_on": False,
        "completed": False
    }
