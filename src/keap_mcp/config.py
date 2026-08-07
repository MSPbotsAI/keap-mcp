from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mcp_transport: Literal["stdio", "http"] = "stdio"
    mcp_http_port: int = 8080
    mcp_http_host: str = "0.0.0.0"

    # Auth mode:
    # "gateway" — production/SOP-compliant: token from HTTP header per request (no global state)
    # "env"     — local dev only: shared token from KEAP_ACCESS_TOKEN env var (not SOP-compliant)
    auth_mode: Literal["env", "gateway"] = "gateway"

    keap_access_token: str | None = None

    keap_access_token_header: str = "X-Keap-Access-Token"

    @property
    def has_credentials(self) -> bool:
        if self.auth_mode == "gateway":
            return True
        return self.keap_access_token is not None


def get_settings() -> Settings:
    return Settings()
