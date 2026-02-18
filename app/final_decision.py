def evaluate_answers(answers: list):
    total = 0

    for answer in answers:
        if not answer or len(answer.strip()) < 10:
            total += 5
        elif len(answer) < 50:
            total += 10
        elif len(answer) < 150:
            total += 15
        else:
            total += 20

    return min(total, 100)


def final_decision(ats, aptitude, interview):
    score = ats * 0.4 + aptitude * 0.3 + interview * 0.3

    if score >= 80:
        return "Strong Hire"
    if score >= 65:
        return "Hire"
    if score >= 55:
        return "Borderline"
    return "Reject"
