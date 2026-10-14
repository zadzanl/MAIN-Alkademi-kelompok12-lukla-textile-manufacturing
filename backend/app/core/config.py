import os

class Settings:
    # Database URLs
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres@127.0.0.1:5433/lukla_test")
    LUKLA_APP_DATABASE_URL: str = os.getenv("LUKLA_APP_DATABASE_URL", "postgresql+psycopg://lukla_app:lukla_secret@127.0.0.1:5433/lukla_test")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "lukla-secret-super-secure-key-for-jwt-signing-hs256")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

settings = Settings()
