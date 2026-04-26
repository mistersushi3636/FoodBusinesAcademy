from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    anton_chat_id: int
    vault_path: Path = Path("/Users/anton/Food Business Academy")
    whisper_model: str = "medium"
    whisper_compute_type: str = "int8"
    claude_cli_path: str = str(Path(__file__).parent / "claude-wrapper.sh")
    notifications_enabled: bool = True
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


VAULT = settings.vault_path
IDEAS_INCOMING = VAULT / "ideas-bot" / "incoming"
IDEAS_ANALYZING = VAULT / "ideas-bot" / "analyzing"
IDEAS_REFINED = VAULT / "ideas-bot" / "refined"
IDEAS_PLANNED = VAULT / "ideas-bot" / "planned"
IDEAS_IN_PROGRESS = VAULT / "ideas-bot" / "in-progress"
IDEAS_COMPLETED = VAULT / "ideas-bot" / "completed"
IDEAS_ARCHIVED = VAULT / "ideas-bot" / "archived"

METRICS_DIR = VAULT / "analytics" / "metrics"
PLANS_DIR = VAULT / "content" / "plans"

VOICE_INBOX = VAULT / "knowledge-base" / "transcripts" / "inbox"

IDEA_STATUSES = [
    ("incoming", "📥 Новые", IDEAS_INCOMING),
    ("analyzing", "🔍 На анализе", IDEAS_ANALYZING),
    ("refined", "✏️ Доработаны", IDEAS_REFINED),
    ("planned", "📅 С планом", IDEAS_PLANNED),
    ("in-progress", "⚡ В работе", IDEAS_IN_PROGRESS),
    ("completed", "✅ Готовы", IDEAS_COMPLETED),
    ("archived", "🗄️ Архив", IDEAS_ARCHIVED),
]
