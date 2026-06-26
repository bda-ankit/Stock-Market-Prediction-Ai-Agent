from pydantic import BaseModel


class Settings(BaseModel):
    APP_NAME: str = "Stock Market Prediction AI"

    API_PREFIX: str = "/api"

    OLLAMA_URL: str = "http://127.0.0.1:11434"

    OLLAMA_MODEL: str = "deepseek-r1:8b"

    TEMPERATURE: float = 0.1

    MAX_CONTEXT: int = 8192


settings = Settings()