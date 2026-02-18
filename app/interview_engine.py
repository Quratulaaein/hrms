def get_initial_question(role: str) -> str:
    if role == "Outbound Sales":
        return "Please introduce yourself and explain your sales experience."
    return "Please introduce yourself and explain your technical background."

def get_followup_question(role: str, previous_answer: str) -> str:
    if role == "Outbound Sales":
        return "How would you handle a prospect who is not interested?"
    return "How would you troubleshoot a production issue?"
