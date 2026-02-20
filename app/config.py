from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    # GHL
    GHL_API_KEY: str
    GHL_LOCATION_ID: str
    GHL_API_BASE: str
    GHL_SCORE_FIELD_ID: str
    GHL_LINK_FIELD_ID: str
    GHL_USERNAME_FIELD_ID: str
    GHL_PASSWORD_FIELD_ID: str
    HR_INTERVIEW_CALENDAR: str

    # GROQ
    GROQ_API_KEY: str
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    class Config:
        env_file = ".env"


settings = Settings()
