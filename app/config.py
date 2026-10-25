from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # LLM
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    
    # Application
    DATABASE_PATH: str = "./data/nara.db"
    BACKEND_URL: str = "http://backend:8000"
    DEFAULT_TIMEZONE: str = "Asia/Jakarta"
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_PER_MINUTE: int = 30
    
    # Creative defaults
    DEFAULT_STYLE: str = "santai"
    DEFAULT_PERSONA: str = "nara"
    DEFAULT_TEMPERATURE: float = 0.6
    DEFAULT_MAX_OUTPUT_TOKENS: int = 800

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
