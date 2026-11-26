import os
from pathlib import Path
from typing import List

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "SmartSched AI API")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = Path(os.getenv("SMARTSCHED_DB_PATH", str(DATA_DIR / "smartsched.db")))
    
    # Database URL: defaults to PostgreSQL if set, otherwise SQLite fallback
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://sagarsukhadev@localhost:5432/smartsched"
    )

    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "smartsched-super-secure-production-secret-key-2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # CORS Allowlist
    @property
    def CORS_ORIGINS(self) -> List[str]:
        origins_env = os.getenv("CORS_ORIGINS", "")
        if origins_env:
            return [origin.strip() for origin in origins_env.split(",") if origin.strip()]
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8501",
            "http://127.0.0.1:8501",
            "https://smartsched-ai.vercel.app"
        ]

settings = Settings()
