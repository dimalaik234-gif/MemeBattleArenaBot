from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.filters.command import CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db

router = Router()


def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Профиль",   callback_data="profile")
    builder.button(text="🛒 Магазин",   callback_data="shop")
    builder.button(text="⚔️ Бой",       callback_data="battle_menu")
    builder.button(text="🤝 Дуэль",     callback_data="duel_menu")
    builder.button(text="🎁 Бонус",     callback_data="daily")
    builder.adjust(2)
    return builder.as_markup()


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep(message: Message):
    """Обработка deep link (дуэли)."""
    from handlers.duel import handle_duel_link
    db.init_db()
    args = message.text.split(maxsplit=1)
    if len(args) > 1 and args[1].startswith("duel_"):
        # Регистрируем если новый
        if not db.get_user(message.from_user.id):
            db.create_user(message.from_user.id, message.from_user.username or message.from_user.first_name)
        await handle_duel_link(message, args[1][5:])
    else:
        await cmd_start_normal(message)


@router.message(CommandStart())
async def cmd_start_normal(message: Message):
    db.init_db()
    user = db.get_user(message.from_user.id)
    if not user:
        db.create_user(message.from_user.id, message.from_user.username or message.from_user.first_name)
        text = (
            f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
            "Добро пожаловать в <b>Meme Battle</b> 🎭\n\n"
            "Покупай мемов, прокачивай коллекцию и побеждай других игроков!\n\n"
            "💰 Тебе выдано <b>100 монет</b> для старта."
        )
    else:
        text = f"👋 С возвращением, <b>{message.from_user.first_name}</b>!"

    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("🏠 Главное меню:", reply_markup=main_menu_kb())


@router.callback_query(F.data == "main_menu")
async def back_to_menu(call: CallbackQuery):
    await call.message.edit_text("🏠 Главное меню:", reply_markup=main_menu_kb())


@router.callback_query(F.data == "daily")
async def daily_bonus(call: CallbackQuery):
    success = db.claim_daily(call.from_user.id)
    if success:
        await call.answer("🎁 +50 монет! Приходи завтра за новым бонусом.", show_alert=True)
    else:
        await call.answer("⏳ Бонус уже получен сегодня. Возвращайся завтра!", show_alert=True)
