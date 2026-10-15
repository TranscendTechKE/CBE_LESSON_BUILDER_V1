from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "CBE Lesson Builder"
    debug: bool = False
    max_upload_mb: int = 50


settings = Settings()
