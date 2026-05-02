"""Хендлеры FbaPromptBot.

/start — меню
/pending — карточки контент-плана со статусом pending → выводит их visual_prompt
/preset — кнопки пресетов (обложка YT, карусель, Reels, чек-лист, гайд, пост)
/help — справка
свободный текст → расширенный ChatGPT Image промпт от Claude
"""
from __future__ import annotations

import html
import sqlite3
from typing import Iterable

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery, InlineKeyboardButton,
    InlineKeyboardMarkup, Message,
)
from loguru import logger

from config import settings
from brand import BRAND_GUIDE, PRESETS, ASPECT_RATIOS, LEAD_MAGNET_TYPES, LEAD_MAGNET_PROMPT

router = Router(name="prompts")


def _is_anton(uid: int) -> bool:
    return uid == settings.anton_chat_id


def _pending_cards() -> list[dict]:
    if not settings.fba_db_path.exists():
        return []
    conn = sqlite3.connect(str(settings.fba_db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, platform, format_type, topic, scheduled_date, visual_prompt, status "
        "FROM content_plan WHERE status IN ('pending','approved') "
        "AND visual_prompt != '' "
        "ORDER BY scheduled_date IS NULL, scheduled_date LIMIT 30"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── /start ──

MENU_KB = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📋 Промпты на утверждение", callback_data="pending")],
    [InlineKeyboardButton(text="🎨 Пресеты визуала", callback_data="presets")],
    [InlineKeyboardButton(text="🎁 Лид-магнит (промпт для ChatGPT)", callback_data="magnets")],
    [InlineKeyboardButton(text="🆘 Как пользоваться", callback_data="help")],
])

MAGNETS_KB = InlineKeyboardMarkup(inline_keyboard=(
    [[InlineKeyboardButton(text=f"{label} — {desc}", callback_data=f"magnet:{key}")]
     for key, (label, desc) in LEAD_MAGNET_TYPES.items()]
    + [[InlineKeyboardButton(text="← Меню", callback_data="menu")]]
))


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not _is_anton(message.from_user.id):
        await message.answer("Бот доступен только владельцу.")
        return
    await message.answer(
        "🎨 <b>FBA Prompt Bot</b>\n\n"
        "Выдаю готовые промпты для ChatGPT Image (DALL-E / GPT-Image-1).\n"
        "Скопируй → вставь в ChatGPT → получи картинку.\n\n"
        "Что я умею:\n"
        "• /pending — промпты для всех ожидающих карточек контент-плана\n"
        "• /preset — пресеты (обложка YT, карусель, Reels, чек-лист, гайд)\n"
        "• любой текст → расширенный промпт под бренд FBA\n",
        reply_markup=MENU_KB,
    )


@router.callback_query(F.data == "help")
async def cb_help(cb: CallbackQuery) -> None:
    if not _is_anton(cb.from_user.id):
        return
    await cb.message.edit_text(
        "<b>Как пользоваться:</b>\n\n"
        "1. <b>Готовые промпты по плану.</b> /pending — пройдись по карточкам.\n"
        "2. <b>Пресет под формат.</b> /preset → выбери (обложка YT, чек-лист и т.д.) → подставь свою тему.\n"
        "3. <b>Свободный запрос.</b> Просто опиши что нужно — я расширю под бренд FBA.\n\n"
        "<b>Бренд:</b> тёмный фон, бирюзовый акцент, минимализм, без стоковых лиц.",
        reply_markup=MENU_KB,
    )


# ── /pending ──

@router.message(Command("pending"))
@router.callback_query(F.data == "pending")
async def show_pending(event) -> None:
    uid = event.from_user.id
    if not _is_anton(uid):
        return
    answer_fn = event.message.answer if isinstance(event, CallbackQuery) else event.answer

    cards = _pending_cards()
    if not cards:
        await answer_fn("Нет карточек со статусом pending/approved и заполненным visual_prompt.")
        return

    await answer_fn(f"📋 Найдено {len(cards)} промптов. Шлю по одному:")
    for c in cards:
        plt = {"telegram": "TG", "instagram": "IG", "youtube": "YT", "cross": "Кросс"}.get(c["platform"], c["platform"])
        fmt = {
            "post": "пост", "carousel": "карусель", "reels": "Reels/Shorts",
            "longvideo": "длинное", "story": "сторис",
        }.get(c["format_type"], c["format_type"])
        head = (
            f"<b>#{c['id']} · {plt} · {fmt}</b>\n"
            f"📅 {c['scheduled_date'] or '—'} · статус: {c['status']}\n"
            f"🎯 {html.escape(c['topic'])}\n\n"
            f"<code>{html.escape(c['visual_prompt'])}</code>"
        )
        await answer_fn(head[:4000])


# ── /preset ──

PRESETS_KB = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎬 Обложка YouTube", callback_data="preset:cover_yt")],
    [InlineKeyboardButton(text="📺 Превью длинного YT-видео", callback_data="preset:long_thumb")],
    [InlineKeyboardButton(text="📚 Карусель TG/IG", callback_data="preset:carousel")],
    [InlineKeyboardButton(text="🎞 Reels/Shorts (обложка)", callback_data="preset:reels_thumb")],
    [InlineKeyboardButton(text="🖼 Пост (1:1)", callback_data="preset:post_visual")],
    [InlineKeyboardButton(text="✅ Чек-лист (PNG лид-магнит)", callback_data="preset:checklist_png")],
    [InlineKeyboardButton(text="📖 Мини-гайд (PNG лид-магнит)", callback_data="preset:guide_png")],
    [InlineKeyboardButton(text="← Меню", callback_data="menu")],
])


@router.message(Command("preset"))
@router.callback_query(F.data == "presets")
async def show_presets(event) -> None:
    uid = event.from_user.id
    if not _is_anton(uid):
        return
    answer_fn = event.message.answer if isinstance(event, CallbackQuery) else event.answer
    await answer_fn(
        "🎨 <b>Пресеты визуала</b>\n\nВыбери формат — пришлю шаблон промпта для ChatGPT Image. "
        "В нём останется заменить плейсхолдеры <code>&lt;ВСТАВЬ ...&gt;</code> на свою тему.",
        reply_markup=PRESETS_KB,
    )


@router.callback_query(F.data.startswith("preset:"))
async def cb_preset(cb: CallbackQuery) -> None:
    if not _is_anton(cb.from_user.id):
        return
    key = cb.data.split(":", 1)[1]
    template = PRESETS.get(key)
    if not template:
        await cb.answer("Пресет не найден")
        return
    ratio, label = ASPECT_RATIOS.get(key, ("—", key))
    body = (
        f"🎨 <b>{label}</b>\n"
        f"<i>{ratio}</i>\n\n"
        f"<code>{html.escape(template.strip())}</code>"
    )
    await cb.message.answer(body[:4000])
    await cb.answer()


@router.callback_query(F.data == "menu")
async def cb_menu(cb: CallbackQuery) -> None:
    if not _is_anton(cb.from_user.id):
        return
    await cb.message.edit_text(
        "🎨 <b>FBA Prompt Bot</b>\n\nВыбери действие:",
        reply_markup=MENU_KB,
    )


# ── /magnet ──

@router.message(Command("magnet"))
@router.callback_query(F.data == "magnets")
async def show_magnets(event) -> None:
    uid = event.from_user.id
    if not _is_anton(uid):
        return
    answer_fn = event.message.answer if isinstance(event, CallbackQuery) else event.answer
    await answer_fn(
        "🎁 <b>Лид-магниты</b>\n\nВыбери тип — пришлю промпт для ChatGPT (текст). "
        "Замени <code>&lt;ВСТАВЬ ТЕМУ&gt;</code> на свою — и копируй в чат GPT.\n\n"
        "После генерации текста — используй /preset «Чек-лист (PNG)» или «Мини-гайд (PNG)» для верстки визуала.",
        reply_markup=MAGNETS_KB,
    )


@router.callback_query(F.data.startswith("magnet:"))
async def cb_magnet(cb: CallbackQuery) -> None:
    if not _is_anton(cb.from_user.id):
        return
    key = cb.data.split(":", 1)[1]
    type_data = LEAD_MAGNET_TYPES.get(key)
    if not type_data:
        await cb.answer("Тип не найден")
        return
    label, _desc = type_data
    body = LEAD_MAGNET_PROMPT.format(magnet_type=label, theme="<ВСТАВЬ ТЕМУ>")
    await cb.message.answer(
        f"🎁 <b>Промпт лид-магнита: {label}</b>\n\nКопируй и вставь в ChatGPT (предварительно замени тему):\n\n"
        f"<code>{html.escape(body)}</code>"[:4000]
    )
    await cb.answer()


# ── свободный текст → Claude генерит промпт ──

GEN_SYSTEM = f"""Ты — арт-директор Food Business Academy (FBA), академии для рестораторов.
Антон (владелец) присылает короткое описание визуала. Твоя задача — превратить его в подробный промпт для ChatGPT Image (GPT-Image-1 / DALL-E 3).

{BRAND_GUIDE}

Твой ответ:
- Только готовый промпт на русском, без преамбулы и комментариев
- Структура: формат → композиция → цвета → шрифт → детали → запреты
- Промпт самодостаточный (без плейсхолдеров типа <вставь>)
- Длина 150–300 слов"""


@router.message(F.text)
async def gen_prompt(message: Message) -> None:
    if not _is_anton(message.from_user.id):
        return
    if message.text.startswith("/"):
        return  # не команды

    brief = message.text.strip()
    if len(brief) < 5:
        await message.answer("Опиши визуал чуть подробнее (что именно нужно нарисовать).")
        return

    msg = await message.answer("✍️ Генерирую промпт под бренд FBA…")
    try:
        # ленивый импорт shared
        import sys
        from pathlib import Path
        vault = Path(__file__).parents[3]
        if str(vault) not in sys.path:
            sys.path.insert(0, str(vault))
        from apps.shared.anthropic_client import ask

        out = await ask(
            api_key=settings.anthropic_api_key,
            system=GEN_SYSTEM,
            user=brief,
            max_tokens=900,
        )
        await msg.edit_text(
            f"🎨 <b>Промпт готов</b> · скопируй и вставь в ChatGPT Image:\n\n"
            f"<code>{html.escape(out.strip())}</code>"[:4000]
        )
    except Exception as e:
        logger.exception("prompt gen error")
        await msg.edit_text(f"⚠️ Ошибка: {e}")
