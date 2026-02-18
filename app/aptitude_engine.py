import random

QUESTIONS = [
    {
        "question": "If 5 people complete a task in 10 days, how long for 10 people?",
        "options": ["5 days", "10 days", "20 days", "2 days"],
        "answer": "5 days"
    },
    {
        "question": "What comes next: 2, 4, 8, 16, ?",
        "options": ["18", "24", "32", "30"],
        "answer": "32"
    },
    {
        "question": "If ALL roses are flowers, are ALL flowers roses?",
        "options": ["Yes", "No"],
        "answer": "No"
    }
]

def generate_aptitude_test(count=3):
    return random.sample(QUESTIONS, count)


def evaluate_aptitude(questions, responses):
    score = 0

    for q, user_ans in zip(questions, responses):
        if user_ans == q["answer"]:
            score += 1

    percentage = (score / len(questions)) * 100

    return {
        "score": score,
        "total": len(questions),
        "percentage": percentage,
        "qualified": percentage >= 60
    }
