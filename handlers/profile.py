from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from memes import MEMES_CATALOG, RARITY_COLORS

router = Router()


def profile_text(user_id: int, username: str) -> str:
    user = db.get_user(user_id)
    if not user:
        return "❌ Профиль не найден. Напиши /start"

    memes = db.get_user_memes(user_id)
    total = user["wins"] + user["losses"]
    wr = round(user["wins"] / total * 100) if total > 0 else 0

    lines = [
        f"👤 <b>{username}</b>",
        f"💰 Монеты: <b>{user['coins']}</b>",
        f"🏆 Победы: <b>{user['wins']}</b>  |  💀 Поражения: <b>{user['losses']}</b>",
        f"📊 Винрейт: <b>{wr}%</b>",
        f"\n🃏 Коллекция мемов ({len(memes)} шт.):",
    ]

    if memes:
        for m in memes:
            cat = MEMES_CATALOG.get(m["meme_id"], {})
            emoji = cat.get("emoji", "❓")
            name  = cat.get("name",  m["meme_id"])
            rarity = cat.get("rarity", "?")
            color  = RARITY_COLORS.get(rarity, "⬛")
            lines.append(
                f"  {color} {emoji} <b>{name}</b>  "
                f"❤️{m['hp']} ⚔️{m['attack']} 🛡{m['defense']}"
            )
    else:
        lines.append("  Пусто — загляни в 🛒 Магазин!")

    return "\n".join(lines)


def back_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="main_menu")
    return builder.as_markup()


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    text = profile_text(message.from_user.id, message.from_user.first_name)
    await message.answer(text, parse_mode="HTML", reply_markup=back_kb())


@router.callback_query(F.data == "profile")
async def cb_profile(call: CallbackQuery):
    text = profile_text(call.from_user.id, call.from_user.first_name)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_kb())
