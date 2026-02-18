def recommend_role(score: int, profile: dict) -> str:
    if score >= 70:
        return "Strong Fit – Shortlist"
    if score >= 55:
        return "Good Fit – HR Review"
    if score >= 40:
        if profile.get("is_sales_profile"):
            return "Alternate Sales / Lead Gen Role"
        return "Possible Fit – Manual Review"
    return "Reject"
