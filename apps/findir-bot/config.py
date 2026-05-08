from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    dashboard_api_url: str = "http://127.0.0.1:8001"
    dashboard_api_key: str
    owner_tg_id: int = 0
    manager_tg_id: int = 0
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parents[2] / ".env"),
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings(
    bot_token="",
    dashboard_api_key="",
)
# pydantic-settings ENV mapping (uppercase by default)
# FINDIR_BOT_TOKEN -> bot_token; DASHBOARD_API_URL -> dashboard_api_url; etc.
import os
settings.bot_token = os.getenv("FINDIR_BOT_TOKEN", "")
settings.dashboard_api_url = os.getenv("DASHBOARD_API_URL", "http://127.0.0.1:8001")
settings.dashboard_api_key = os.getenv("DASHBOARD_API_KEY", "")
settings.owner_tg_id = int(os.getenv("OWNER_TG_ID", "0") or 0)
settings.manager_tg_id = int(os.getenv("MANAGER_TG_ID", "0") or 0)
settings.log_level = os.getenv("LOG_LEVEL", "INFO")


def is_owner(tg_id: int) -> bool:
    return settings.owner_tg_id and tg_id == settings.owner_tg_id


def is_manager(tg_id: int) -> bool:
    return settings.manager_tg_id and tg_id == settings.manager_tg_id


def is_authorized(tg_id: int) -> bool:
    return is_owner(tg_id) or is_manager(tg_id)
