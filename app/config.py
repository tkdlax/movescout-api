from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://movescout:changeme@localhost:5432/movescout"
    encryption_key: str = ""
    # API host (not the web UI at movescoutpro.sirva.com)
    movescout_base_url: str = "https://movescoutproapi.sirva.com"
    # Browser Origin header expected by MoveScout (SPA login site)
    movescout_origin: str = "https://movescoutpro.sirva.com"
    # Only sent on create/update if set (omit if your tenant does not use tenantId)
    movescout_tenant_id: int | None = None
    movescout_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
    )
    log_level: str = "info"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "development"
    trusted_proxy_ips: str = "127.0.0.1,::1"
    rate_limit_per_minute: int = 60
    disable_public_docs: bool = False

    token_expiry_seconds: int = 86400
    token_refresh_buffer_seconds: int = 300
    export_page_size: int = 500
    default_page_size: int = 100
    max_page_size: int = 1000
    lov_cache_ttl_seconds: int = 86400

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")

    @property
    def trusted_proxies(self) -> list[str]:
        return [ip.strip() for ip in self.trusted_proxy_ips.split(",") if ip.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
