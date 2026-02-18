def get_jd_requirements():
    return {
        "Outbound Sales": {
            "category": "sales",
            "required_skills": [
                "lead generation", "cold calling", "outreach",
                "client acquisition", "sales"
            ],
            "tools": ["crm", "salesforce", "hubspot"],
            "min_exp": 1
        },
        "Tech Consultant": {
            "category": "tech",
            "required_skills": [
                "python", "sql", "cloud", "support", "troubleshooting"
            ],
            "tools": ["jira", "servicenow"],
            "min_exp": 1
        }
    }
