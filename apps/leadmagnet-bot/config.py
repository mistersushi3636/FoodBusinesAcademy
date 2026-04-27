from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    channel_id: str = "@Food_Busines_Academy"
    lead_magnet_file: Path = Path(__file__).parent / "assets" / "checklist-10-oshibok.pdf"
    lead_magnet_caption: str = (
        "🎁 <b>Чек-лист: 10 ошибок при открытии доставки</b>\n\n"
        "Реальные ошибки из опыта «Мистер Суши» — Воронеж, 13 лет в ресторанном бизнесе.\n\n"
        "Подписывайся на канал → <a href='https://t.me/Food_Busines_Academy'>Food Business Academy</a>"
    )
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
