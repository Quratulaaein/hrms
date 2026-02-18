import json
import os
from datetime import datetime

def log_violation(candidate_id: str, reason: str):
    path = f"data/interviews/{candidate_id}/violations.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)

    violations = []
    if os.path.exists(path):
        violations = json.load(open(path))

    violations.append({
        "reason": reason,
        "time": datetime.utcnow().isoformat()
    })

    json.dump(violations, open(path, "w"))
