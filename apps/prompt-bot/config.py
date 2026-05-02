from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    anton_chat_id: int
    anthropic_api_key: str
    vault_path: Path = Path("/opt/fba/vault")
    fba_db_path: Path = Path("/opt/fba/vault/apps/dashboard/projects/fba-2-0.db")
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
