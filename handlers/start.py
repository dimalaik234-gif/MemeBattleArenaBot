from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from config import MAX_ENERGY

router = Router()


def main_menu_kb():
    b = InlineKeyboardBuilder()
    b.button(text="👤 Профиль",      callback_data="profile")
    b.button(text="🛒 Магазин",      callback_data="shop")
    b.button(text="⚔️ Бой",          callback_data="battle_menu")
    b.button(text="🤝 Дуэль",        callback_data="duel_menu")
    b.button(text="🏆 Таблица",      callback_data="leaderboard")
    b.button(text="🎁 Бонус",        callback_data="daily")
    b.adjust(2)
    return b.as_markup()


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep(message: Message):
    db.init_db()
    args = message.text.split(maxsplit=1)
    if len(args) > 1 and args[1].startswith("duel_"):
        if not db.get_user(message.from_user.id):
            db.create_user(message.from_user.id, message.from_user.username or message.from_user.first_name)
        from handlers.duel import handle_duel_link
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
            "🎭 <b>Meme Battle</b> — покупай мемов, прокачивай и сражайся!\n\n"
            "💰 Тебе выдано <b>100 монет</b>\n"
            f"⚡ Энергия: <b>{MAX_ENERGY}/{MAX_ENERGY}</b>\n\n"
            "🆕 Зайди в 🛒 Магазин и купи первого мема!"
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
        await call.answer("🎁 +50 монет и полная энергия! Приходи завтра.", show_alert=True)
    else:
        await call.answer("⏳ Бонус уже получен. Возвращайся завтра!", show_alert=True)


@router.callback_query(F.data == "leaderboard")
async def cb_leaderboard(call: CallbackQuery):
    top = db.get_leaderboard(10)
    if not top:
        await call.answer("Пока никто не играл!", show_alert=True)
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Таблица лидеров</b>\n"]
    for i, row in enumerate(top):
        medal = medals[i] if i < 3 else f" {i+1}."
        total = row["wins"] + row["losses"]
        wr = round(row["wins"] / total * 100) if total > 0 else 0
        lines.append(
            f"{medal} <b>{row['username']}</b> — "
            f"Ур.{row['level']} | {row['wins']}W | WR {wr}% | "
            f"🔥 Серия: {row['best_streak']}"
        )

    b = InlineKeyboardBuilder()
    b.button(text="◀️ Назад", callback_data="main_menu")
    await call.message.edit_text("\n".join(lines), reply_markup=b.as_markup(), parse_mode="HTML")
