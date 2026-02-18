from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    GHL_API_KEY: str
    GHL_LOCATION_ID: str
    GHL_API_URL: str

    GHL_SCORE_FIELD_ID: str
    GHL_LINK_FIELD_ID: str
    GHL_USERNAME_FIELD_ID: str
    GHL_PASSWORD_FIELD_ID: str

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
