"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized configuration via environment variables."""

    # ── Redis ─────────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_CACHE_TTL: int = 3600  # 1 hour

    # ── Database ──────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://lotomind:lotomind_secret@localhost:5432/lotomind"

    # ── CORS ──────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    # ── Lotofácil ─────────────────────────────────────────────
    LOTOFACIL_MIN_NUMBER: int = 1
    LOTOFACIL_MAX_NUMBER: int = 25
    LOTOFACIL_DRAW_SIZE: int = 15

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
