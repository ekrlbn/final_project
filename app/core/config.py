# app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Retirement Planning Tool"
    # Add other settings like database URLs, API keys, etc.
    # Example: DATABASE_URL: str = "sqlite:///./test.db"
    # OPENAI_API_KEY: str = "your_openai_api_key_here"

    # ChromaDB settings
    CHROMA_DB_PATH: str = "./chroma_db_store"
    CHROMA_COLLECTION_NAME: str = "retirement_docs"

    # Security settings for authentication
    SECRET_KEY: str = "a_very_secret_key_that_should_be_changed_and_kept_safe"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env" # If you use a .env file for environment variables

settings = Settings() 