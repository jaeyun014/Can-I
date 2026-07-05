from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    cors_origin_regex: str = (
        r"https?://(localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|"
        r"192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|"
        r"172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?"
    )
    openai_api_key: str = ""
    vision_model: str = "gpt-4o-mini"
    ocr_engine: str = "tesseract"
    google_client_id: str = ""
    database_url: str = "sqlite:///can_i.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
