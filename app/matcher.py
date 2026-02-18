def score_candidate(profile: dict, jd: dict) -> tuple:
    score = 0
    reasons = []

    if jd["category"] == "sales" and profile.get("is_sales_profile"):
        score += 35
        reasons.append("Sales aligned role")

    skills = set(s.lower() for s in profile.get("key_skills") or [])
    jd_skills = set(s.lower() for s in jd["required_skills"])

    matched_skills = skills & jd_skills
    score += min(len(matched_skills) * 5, 25)

    if matched_skills:
        reasons.append(f"Matched skills: {', '.join(matched_skills)}")

    tools = set(t.lower() for t in profile.get("tools") or [])
    jd_tools = set(t.lower() for t in jd["tools"])

    matched_tools = tools & jd_tools
    score += min(len(matched_tools) * 5, 15)

    exp = profile.get("total_experience_years") or 0
    if exp >= jd["min_exp"]:
        score += 15
    elif exp >= jd["min_exp"] - 1:
        score += 10
    else:
        score += 5

    return score, reasons
