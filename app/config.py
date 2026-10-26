"""Application settings, loaded from environment variables and the .env file."""

from functools import lru_cache
from urllib.parse import quote

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # extra="ignore": .env also holds variables other modules will read later
    # (e.g. API keys); unknown keys must not fail validation here.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str
    # SecretStr keeps the password out of reprs, logs and tracebacks.
    postgres_password: SecretStr
    postgres_db: str
    # 127.0.0.1, not "localhost": docker-compose.yml binds the port to IPv4 only, and on
    # Windows "localhost" resolves to IPv6 ::1 first, so the connection stalls before
    # falling back to IPv4.
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432

    # Optional so that commands and tests that never call OpenAI work without a key;
    # app/ingest.py checks for it before embedding.
    openai_api_key: SecretStr | None = None
    embedding_model: str = "text-embedding-3-small"
    # Must match the vector(...) size of rag.chunks.embedding (migrations/003_rag_schema.sql).
    embedding_dimensions: int = 1536

    @property
    def database_url(self) -> str:
        """libpq connection URL. User and password are percent-encoded so characters
        like '@', ':' or '/' in a generated password cannot break the URL."""
        user = quote(self.postgres_user, safe="")
        password = quote(self.postgres_password.get_secret_value(), safe="")
        return (
            f"postgresql://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Read settings once per process; tests can call get_settings.cache_clear()."""
    return Settings()
