import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "StreamForge API"
    APP_VERSION: str = "1.0.0"

    # Postgres
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "streamforge")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    # Trino
    TRINO_HOST: str = os.getenv("TRINO_HOST", "localhost")
    TRINO_PORT: int = int(os.getenv("TRINO_PORT", "8081"))
    TRINO_USER: str = os.getenv("TRINO_USER", "admin")
    TRINO_CATALOG: str = os.getenv("TRINO_CATALOG", "minio")
    TRINO_SCHEMA: str = os.getenv("TRINO_SCHEMA", "retail")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
