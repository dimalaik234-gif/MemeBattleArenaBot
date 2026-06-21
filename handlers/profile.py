from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from memes import MEMES_CATALOG, RARITY_COLORS, ABILITY_NAMES
from config import LEVEL_XP, SELL_PERCENT, MAX_MEME_LEVEL

router = Router()


def profile_text(user_id: int, username: str) -> str:
    user = db.get_user(user_id)
    if not user:
        return "❌ Профиль не найден. Напиши /start"

    memes = db.get_user_memes(user_id)
    total = user["wins"] + user["losses"]
    wr = round(user["wins"] / total * 100) if total > 0 else 0
    energy, eta = db.get_energy(user_id)

    # XP прогресс
    lvl = user["level"]
    cur_xp = user["xp"]
    next_xp = LEVEL_XP[lvl] if lvl < len(LEVEL_XP) else "MAX"
    xp_text = f"{cur_xp}/{next_xp}" if isinstance(next_xp, int) else f"{cur_xp} (MAX)"

    energy_text = f"⚡ {energy}/5"
    if eta:
        energy_text += f" (след. через {eta})"

    lines = [
        f"👤 <b>{username}</b>  Ур. {lvl}",
        f"✨ XP: {xp_text}",
        f"💰 Монеты: <b>{user['coins']}</b>",
        energy_text,
        f"🏆 {user['wins']}W / {user['losses']}L  |  WR: {wr}%",
        f"🔥 Серия побед: {user['win_streak']} (лучшая: {user['best_streak']})",
        f"\n🃏 Коллекция ({len(memes)} шт.):",
    ]

    if memes:
        for m in memes:
            cat = MEMES_CATALOG.get(m["meme_id"], {})
            emoji = cat.get("emoji", "❓")
            name  = cat.get("name", m["meme_id"])
            rarity = cat.get("rarity", "?")
            color  = RARITY_COLORS.get(rarity, "⬛")
            lvl_str = f" [Ур.{m['level']}]" if m["level"] > 1 else ""
            ability = cat.get("ability")
            ab_str = f" {ABILITY_NAMES.get(ability, '').split('(')[0].strip()}" if ability else ""
            lines.append(
                f"  {color} {emoji} <b>{name}</b>{lvl_str}{ab_str}\n"
                f"    ❤️{m['hp']} ⚔️{m['attack']} 🛡{m['defense']}"
            )
    else:
        lines.append("  Пусто — загляни в 🛒 Магазин!")

    return "\n".join(lines)


def profile_kb(memes):
    b = InlineKeyboardBuilder()
    if memes:
        b.button(text="⬆️ Улучшить мема",  callback_data="upgrade_menu")
        b.button(text="💸 Продать мема",    callback_data="sell_menu")
    b.button(text="◀️ Назад", callback_data="main_menu")
    b.adjust(2)
    return b.as_markup()


@router.callback_query(F.data == "profile")
async def cb_profile(call: CallbackQuery):
    text = profile_text(call.from_user.id, call.from_user.first_name)
    memes = db.get_user_memes(call.from_user.id)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=profile_kb(memes))


# ── Улучшение ──────────────────────────────────────────────────

@router.callback_query(F.data == "upgrade_menu")
async def cb_upgrade_menu(call: CallbackQuery):
    memes = db.get_user_memes(call.from_user.id)
    if not memes:
        await call.answer("Нет мемов!", show_alert=True)
        return

    b = InlineKeyboardBuilder()
    for m in memes:
        if m["level"] >= MAX_MEME_LEVEL:
            continue
        cat  = MEMES_CATALOG.get(m["meme_id"], {})
        name = cat.get("name", "?")
        cost = db.get_upgrade_cost(m["level"])
        b.button(
            text=f"{cat.get('emoji','❓')} {name} Ур.{m['level']}→{m['level']+1} ({cost}💰)",
            callback_data=f"upgrade:{m['id']}",
        )
    b.button(text="◀️ Назад", callback_data="profile")
    b.adjust(1)
    await call.message.edit_text(
        "⬆️ <b>Улучшение мема</b>\n\n+10% ко всем статам за уровень.\nВыбери мема:",
        reply_markup=b.as_markup(), parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("upgrade:"))
async def cb_upgrade(call: CallbackQuery):
    meme_row_id = int(call.data.split(":")[1])
    meme = db.get_user_meme_by_id(meme_row_id)
    if not meme or meme["user_id"] != call.from_user.id:
        await call.answer("❌ Мем не найден.", show_alert=True)
        return
    if meme["level"] >= MAX_MEME_LEVEL:
        await call.answer("🔝 Мем уже на макс. уровне!", show_alert=True)
        return

    cost = db.get_upgrade_cost(meme["level"])
    user = db.get_user(call.from_user.id)
    if user["coins"] < cost:
        await call.answer(f"💸 Нужно {cost} монет, у тебя {user['coins']}.", show_alert=True)
        return

    db.update_coins(call.from_user.id, -cost)
    db.upgrade_meme(meme_row_id)
    updated = db.get_user_meme_by_id(meme_row_id)
    cat = MEMES_CATALOG.get(meme["meme_id"], {})
    await call.answer(
        f"✅ {cat.get('emoji','❓')} {cat.get('name','?')} → Ур.{updated['level']}!\n"
        f"❤️{updated['hp']} ⚔️{updated['attack']} 🛡{updated['defense']}",
        show_alert=True,
    )
    # Обновляем меню
    await cb_upgrade_menu(call)


# ── Продажа ────────────────────────────────────────────────────

@router.callback_query(F.data == "sell_menu")
async def cb_sell_menu(call: CallbackQuery):
    memes = db.get_user_memes(call.from_user.id)
    if not memes:
        await call.answer("Нет мемов!", show_alert=True)
        return

    b = InlineKeyboardBuilder()
    for m in memes:
        cat   = MEMES_CATALOG.get(m["meme_id"], {})
        name  = cat.get("name", "?")
        price = int(cat.get("price", 0) * SELL_PERCENT / 100)
        b.button(
            text=f"{cat.get('emoji','❓')} {name} Ур.{m['level']} → {price}💰",
            callback_data=f"sell:{m['id']}",
        )
    b.button(text="◀️ Назад", callback_data="profile")
    b.adjust(1)
    await call.message.edit_text(
        "💸 <b>Продажа мема</b>\n\nВозврат 40% от цены. Выбери:",
        reply_markup=b.as_markup(), parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("sell:"))
async def cb_sell(call: CallbackQuery):
    meme_row_id = int(call.data.split(":")[1])
    meme = db.get_user_meme_by_id(meme_row_id)
    if not meme or meme["user_id"] != call.from_user.id:
        await call.answer("❌ Мем не найден.", show_alert=True)
        return

    cat = MEMES_CATALOG.get(meme["meme_id"], {})
    refund = int(cat.get("price", 0) * SELL_PERCENT / 100)
    db.delete_meme(meme_row_id)
    db.update_coins(call.from_user.id, refund)
    await call.answer(f"💸 Продан {cat.get('name','?')} за {refund} монет.", show_alert=True)
    await cb_sell_menu(call)
