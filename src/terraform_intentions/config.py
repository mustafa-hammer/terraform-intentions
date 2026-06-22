"""Application configuration, loaded from the environment / a local .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Values come from ``TFI_``-prefixed env vars or ``.env``."""

    model_config = SettingsConfigDict(env_prefix="TFI_", env_file=".env", extra="ignore")

    # Shared HMAC key configured on the TFC run task; used to verify request signatures.
    tfc_hmac_key: str

    # Timeout (seconds) for the outbound callback POST to TFC.
    request_timeout: float = 10.0


@lru_cache
def get_settings() -> Settings:
    """Return cached settings so the .env file is read once per process."""
    return Settings()  # type: ignore[call-arg]  # values are supplied via env/.env
