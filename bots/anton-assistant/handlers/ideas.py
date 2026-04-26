from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from loguru import logger

from config import settings, IDEA_STATUSES
from keyboards.main_menu import main_menu, back_to_main
from keyboards.ideas_menu import ideas_status_menu, ideas_list_keyboard, idea_actions_keyboard
from services.vault_writer import save_new_idea, find_idea_by_slug, move_idea, append_to_idea
from services.claude_cli import analyze_idea_via_claude, build_plan_via_claude
from utils.markdown import list_idea_files, read_markdown


router = Router(name="ideas")


class IdeaStates(StatesGroup):
    waiting_text = State()
    waiting_refinement = State()


def _is_anton(event) -> bool:
    return event.from_user.id == settings.anton_chat_id


@router.callback_query(F.data == "new_idea")
async def new_idea_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    text = (
        "💡 <b>Новая идея</b>\n\n"
        "Расскажи. Текстом или голосовым — как удобнее.\n"
        "Я запишу, проанализирую, предложу улучшения."
    )
    await callback.message.edit_text(text, reply_markup=back_to_main())
    await state.set_state(IdeaStates.waiting_text)
    await callback.answer()


@router.message(StateFilter(IdeaStates.waiting_text), F.text)
async def receive_idea_text(message: Message, state: FSMContext) -> None:
    if not _is_anton(message):
        return
    text = message.text.strip()
    if len(text) < 10:
        await message.answer("Слишком коротко. Расскажи подробнее — что за идея, для чего?")
        return

    path = await save_new_idea(text, source="telegram-text")
    logger.info(f"New idea saved: {path.name}")

    await state.clear()
    await message.answer(
        f"✅ Записал. Идея <b>{path.stem[:50]}…</b>\n\n"
        "Сейчас передаю на анализ. Через пару минут пришлю предложения по улучшению.\n\n"
        "Анализирую...",
        reply_markup=back_to_main(),
    )

    try:
        analysis = await analyze_idea_via_claude(path)
        new_path = await move_idea(path, "analyzing")
        await message.answer(
            f"🔍 <b>Анализ готов</b>\n\n{analysis[:3500]}\n\n"
            "Открой «📋 Мои идеи → На анализе» чтобы продолжить работу.",
            reply_markup=main_menu(),
        )
    except Exception as e:
        logger.error(f"Idea analysis failed: {e}")
        await message.answer(
            "⚠️ Анализ не удался автоматически. Идея сохранена в incoming.\n"
            "Открой Claude Code и запусти /idea-curator вручную.",
            reply_markup=main_menu(),
        )


@router.callback_query(F.data == "my_ideas")
async def my_ideas_menu(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    await callback.message.edit_text(
        "📋 <b>Мои идеи</b>\nВыбери статус:",
        reply_markup=ideas_status_menu(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ideas_status:"))
async def ideas_by_status(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    status = callback.data.split(":", 1)[1]
    folder = next((p for s, _, p in IDEA_STATUSES if s == status), None)
    label = next((l for s, l, _ in IDEA_STATUSES if s == status), status)
    if not folder:
        await callback.answer("Неизвестный статус.", show_alert=True)
        return
    ideas = list_idea_files(folder)
    if not ideas:
        await callback.message.edit_text(
            f"{label}\n\nПусто.",
            reply_markup=ideas_status_menu(),
        )
    else:
        await callback.message.edit_text(
            f"{label} ({len(ideas)})\n\nВыбери идею:",
            reply_markup=ideas_list_keyboard(status, ideas),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("idea:"))
async def show_idea(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    parts = callback.data.split(":", 2)
    status, slug = parts[1], parts[2]
    path = await find_idea_by_slug(slug)
    if not path:
        await callback.answer("Идея не найдена.", show_alert=True)
        return
    metadata, content = await read_markdown(path)
    title = metadata.get("title", slug)
    preview = content[:1500]
    text = (
        f"📄 <b>{title}</b>\n"
        f"Статус: {status}\n"
        f"Создано: {metadata.get('created', '?')[:10]}\n\n"
        f"{preview}{'…' if len(content) > 1500 else ''}"
    )
    await callback.message.edit_text(text, reply_markup=idea_actions_keyboard(status, slug))
    await callback.answer()


@router.callback_query(F.data.startswith("action:"))
async def idea_action(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    parts = callback.data.split(":", 3)
    action, status, slug = parts[1], parts[2], parts[3]
    path = await find_idea_by_slug(slug)
    if not path:
        await callback.answer("Идея не найдена.", show_alert=True)
        return

    if action == "analyze":
        await callback.message.edit_text("🔍 Анализирую заново...", reply_markup=back_to_main())
        try:
            result = await analyze_idea_via_claude(path)
            await move_idea(path, "analyzing")
            await callback.message.answer(f"✅ Анализ готов:\n\n{result[:3500]}", reply_markup=main_menu())
        except Exception as e:
            await callback.message.answer(f"⚠️ Ошибка: {e}", reply_markup=main_menu())
    elif action == "plan":
        await callback.message.edit_text("📅 Строю план...", reply_markup=back_to_main())
        try:
            result = await build_plan_via_claude(path)
            await move_idea(path, "planned")
            await callback.message.answer(f"✅ План готов:\n\n{result[:3500]}", reply_markup=main_menu())
        except Exception as e:
            await callback.message.answer(f"⚠️ Ошибка: {e}", reply_markup=main_menu())
    elif action == "refine":
        await state.update_data(idea_slug=slug, idea_status=status)
        await state.set_state(IdeaStates.waiting_refinement)
        await callback.message.edit_text(
            "✏️ Что доработать? Напиши уточнения / правки / новые мысли.",
            reply_markup=back_to_main(),
        )
    elif action == "start":
        await move_idea(path, "in-progress")
        await callback.message.edit_text("⚡ Идея в работе.", reply_markup=main_menu())
    elif action == "complete":
        await move_idea(path, "completed")
        await callback.message.edit_text("✅ Идея завершена.", reply_markup=main_menu())
    elif action == "archive":
        await move_idea(path, "archived")
        await callback.message.edit_text("🗄️ Идея в архиве.", reply_markup=main_menu())
    await callback.answer()


@router.message(StateFilter(IdeaStates.waiting_refinement), F.text)
async def receive_refinement(message: Message, state: FSMContext) -> None:
    if not _is_anton(message):
        return
    data = await state.get_data()
    slug = data.get("idea_slug")
    path = await find_idea_by_slug(slug) if slug else None
    if not path:
        await message.answer("Идея не найдена. Начни заново.", reply_markup=main_menu())
        await state.clear()
        return
    await append_to_idea(path, "## История диалогов", f"уточнение от Антона: {message.text}")
    await move_idea(path, "refined")
    await state.clear()
    await message.answer("✅ Уточнение записано. Идея перешла в «Доработаны».", reply_markup=main_menu())
