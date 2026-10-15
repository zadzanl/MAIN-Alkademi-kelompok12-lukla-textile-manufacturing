import os
from pathlib import Path

class Settings:
    # Database URLs
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres@127.0.0.1:5433/lukla_test")
    LUKLA_APP_DATABASE_URL: str = os.getenv("LUKLA_APP_DATABASE_URL", "postgresql+psycopg://lukla_app:lukla_secret@127.0.0.1:5433/lukla_test")

    # Tenant defect taxonomy for quality inspection. It is deployment configuration, not a
    # code list, because the frozen schema has no taxonomy table (QC & MES design decision 4).
    QC_DEFECT_TAXONOMY_PATH: str = os.getenv(
        "QC_DEFECT_TAXONOMY_PATH",
        str(Path(__file__).resolve().parents[2] / "quality-control" / "config" / "defect_taxonomy.json")
    )

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "lukla-secret-super-secure-key-for-jwt-signing-hs256")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

settings = Settings()
