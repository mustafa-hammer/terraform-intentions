"""Application configuration, loaded from the environment / a local .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Values come from ``TFI_``-prefixed env vars or ``.env``."""

    model_config = SettingsConfigDict(env_prefix="TFI_", env_file=".env", extra="ignore")

    # Shared HMAC key configured on the TFC run task; used to verify request signatures.
    tfc_hmac_key: str

    # TFC team token used to read plan JSON and ingress-attributes.
    # Needs at least read access to the workspace's configuration versions and plans.
    tfc_team_token: str

    # Timeout (seconds) for outbound HTTP calls (TFC fetch + callback POST).
    request_timeout: float = 10.0

    # OpenAI API key used by the LangChain verdict chain.
    openai_api_key: str

    # Chat model to use for verdict generation.  gpt-4o gives the best results;
    # gpt-4o-mini is cheaper and fast enough for advisory-only use.
    openai_model: str = "gpt-4o-mini"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings so the .env file is read once per process."""
    return Settings()  # type: ignore[call-arg]  # values are supplied via env/.env
