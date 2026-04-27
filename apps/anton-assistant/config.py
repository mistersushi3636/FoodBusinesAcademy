from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    bot_token: str
    anton_chat_id: int
    tg_channel_id: str = "@Food_Busines_Academy"  # for auto-posting
    leadmagnet_bot_token: str = ""

    # Paths
    vault_path: Path = Path("/opt/fba/vault")
    log_level: str = "INFO"

    # AI
    anthropic_api_key: str = ""
    openai_api_key: str = ""        # DALL-E 3 + Whisper API

    # Notifications
    notifications_enabled: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Vault paths
VAULT = settings.vault_path

TRANSCRIPTS_INBOX  = VAULT / "knowledge-base" / "transcripts" / "inbox"
TRANSCRIPTS_DIR    = VAULT / "knowledge-base" / "transcripts"
CONTENT_DRAFTS     = VAULT / "content" / "drafts"
CONTENT_PUBLISHED  = VAULT / "content" / "published"
CONTENT_IDEAS      = VAULT / "content" / "ideas"
CONTENT_PLANS      = VAULT / "content" / "plans"
METRICS_DIR        = VAULT / "analytics" / "metrics"
PATTERNS_FILE      = VAULT / "patterns" / "learnings.md"
BRAND_DIR          = VAULT / "brand"
BRAND_EXAMPLES_DIR = VAULT / "brand" / "examples"
DESIGN_BRIEFS_DIR  = VAULT / "design-system" / "briefs"

# Platform format rules (read by /draft skill)
PLATFORM_RULES = {
    "telegram":  VAULT / "platforms" / "telegram"  / "format-rules.md",
    "instagram": VAULT / "platforms" / "instagram" / "format-rules.md",
    "youtube":   VAULT / "platforms" / "youtube"   / "format-rules.md",
}

PLATFORMS = list(PLATFORM_RULES.keys())
