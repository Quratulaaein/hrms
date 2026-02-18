def build_candidate_text(profile: dict):
    parts = []

    if profile.get("current_role"):
        parts.append(profile["current_role"])

    if profile.get("key_skills"):
        parts.append("Skills: " + ", ".join(profile["key_skills"]))

    if profile.get("domains"):
        parts.append("Domains: " + ", ".join(profile["domains"]))

    if profile.get("tools"):
        parts.append("Tools: " + ", ".join(profile["tools"]))

    return " | ".join(parts)
