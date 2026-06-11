import os
from typing import List, Union
from pydantic import AnyHttpUrl, BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated

def parse_cors_origins(v: Union[str, List[str]]) -> List[str]:
    """Parse CORS origins from env var.
    Handles: plain CSV string, JSON-encoded list string, or already-parsed list.
    pydantic-settings v2 may pass the raw env string or a partially parsed value.
    """
    import json
    if isinstance(v, list):
        return [str(i).strip() for i in v]
    if isinstance(v, str):
        v = v.strip()
        if v.startswith("["):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(i).strip() for i in parsed]
            except json.JSONDecodeError:
                pass
        # Plain CSV string (e.g. "http://a,http://b")
        return [i.strip() for i in v.split(",") if i.strip()]
    raise ValueError(f"Cannot parse ALLOWED_ORIGINS from value: {v!r}")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    APP_NAME: str = "Knowledge Sphere"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "your-super-secret-key-change-in-production-at-least-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Databases
    DATABASE_URL: str = "postgresql+asyncpg://knowledge_user:knowledge_pass@localhost:5432/knowledge_sphere"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "knowledge_neo4j_pass"
    NEO4J_DATABASE: str = "neo4j"

    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION_DOCUMENTS: str = "documents_v4"
    CHROMA_COLLECTION_ENTITIES: str = "entities_v4"

    # LLM Settings
    OPENAI_API_KEY: str = ""
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4o"

    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-2"

    # Helper to detect placeholder keys (e.g., 'YOUR_GEMINI_API_KEY')
    @staticmethod
    def is_real_key(key: str) -> bool:
        if not key or not key.strip():
            return False
        k = key.strip()
        if k.upper().startswith("YOUR_") or "DUMMY" in k.upper():
                return False
        return True

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    DEFAULT_LLM_PROVIDER: str = "gemini"  # openai | gemini | ollama
    DEFAULT_EMBEDDING_PROVIDER: str = "gemini"  # openai | gemini | ollama

    # Email Config
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@knowledgesphere.ai"
    EMAILS_FROM_NAME: str = "Knowledge Sphere"

    # Storage Config
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = "pdf,docx,txt,csv,html,htm"

    # Cloudinary Config
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    USE_CLOUDINARY: bool = False

    # CORS
    ALLOWED_ORIGINS: Annotated[
        List[str], BeforeValidator(parse_cors_origins)
    ] = ["http://localhost:5173", "http://localhost:3000"]

    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

settings = Settings()
