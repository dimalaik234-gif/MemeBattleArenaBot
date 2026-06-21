from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from memes import MEMES_CATALOG, RARITY_COLORS, ABILITY_NAMES, roll_stats, get_available_memes

router = Router()
PAGE_SIZE = 4


def shop_page_kb(player_level: int, page: int = 0):
    available = list(get_available_memes(player_level).items())
    locked    = [(k, v) for k, v in MEMES_CATALOG.items() if v["min_level"] > player_level]

    b = InlineKeyboardBuilder()
    start = page * PAGE_SIZE
    end   = min(start + PAGE_SIZE, len(available))

    for meme_id, info in available[start:end]:
        color = RARITY_COLORS.get(info["rarity"], "⬛")
        label = f"{color} {info['emoji']} {info['name']} — {info['price']}💰"
        b.button(text=label, callback_data=f"buy:{meme_id}")

    # Показываем заблокированных (первые 2)
    for meme_id, info in locked[:2]:
        color = RARITY_COLORS.get(info["rarity"], "⬛")
        b.button(
            text=f"🔒 {color} {info['name']} (Ур.{info['min_level']})",
            callback_data=f"locked:{meme_id}",
        )

    # Пагинация
    nav_row = []
    if page > 0:
        b.button(text="◀️", callback_data=f"shop_page:{page-1}")
    if end < len(available):
        b.button(text="▶️", callback_data=f"shop_page:{page+1}")

    b.button(text="◀️ Назад", callback_data="main_menu")
    b.adjust(1)
    return b.as_markup()


def shop_text(player_level):
    return (
        "🛒 <b>Магазин мемов</b>\n\n"
        f"Твой уровень: <b>{player_level}</b>\n"
        "Каждый мем получает <b>случайные</b> статы при покупке.\n"
        "Повышай уровень, чтобы открыть крутых мемов!\n\n"
        f"{RARITY_COLORS['Обычный']} Обычный  "
        f"{RARITY_COLORS['Редкий']} Редкий  "
        f"{RARITY_COLORS['Эпический']} Эпический  "
        f"{RARITY_COLORS['Легендарный']} Легендарный"
    )


@router.callback_query(F.data == "shop")
async def cb_shop(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    lvl = user["level"] if user else 1
    await call.message.edit_text(
        shop_text(lvl), reply_markup=shop_page_kb(lvl), parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("shop_page:"))
async def cb_shop_page(call: CallbackQuery):
    page = int(call.data.split(":")[1])
    user = db.get_user(call.from_user.id)
    lvl = user["level"] if user else 1
    await call.message.edit_text(
        shop_text(lvl), reply_markup=shop_page_kb(lvl, page), parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("locked:"))
async def cb_locked(call: CallbackQuery):
    meme_id = call.data.split(":", 1)[1]
    info = MEMES_CATALOG.get(meme_id, {})
    ab = info.get("ability")
    ab_text = ABILITY_NAMES.get(ab, "Нет") if ab else "Нет"
    await call.answer(
        f"🔒 {info.get('name','?')} — откроется на уровне {info.get('min_level','?')}\n"
        f"Способность: {ab_text}",
        show_alert=True,
    )


@router.callback_query(F.data.startswith("buy:"))
async def cb_buy(call: CallbackQuery):
    meme_id = call.data.split(":", 1)[1]
    info = MEMES_CATALOG.get(meme_id)
    if not info:
        await call.answer("❌ Мем не найден.", show_alert=True)
        return

    user = db.get_user(call.from_user.id)
    if not user:
        await call.answer("Сначала /start", show_alert=True)
        return

    if user["level"] < info["min_level"]:
        await call.answer(f"🔒 Нужен уровень {info['min_level']}!", show_alert=True)
        return

    if user["coins"] < info["price"]:
        await call.answer(f"💸 Нужно {info['price']}💰, у тебя {user['coins']}.", show_alert=True)
        return

    db.update_coins(call.from_user.id, -info["price"])
    stats = roll_stats(meme_id)
    db.add_meme_to_user(call.from_user.id, meme_id, **stats)

    ab = info.get("ability")
    ab_text = f"\n🎯 Способность: {ABILITY_NAMES.get(ab, '?')}" if ab else ""

    await call.answer(
        f"✅ Куплен {info['emoji']} {info['name']}!\n"
        f"❤️{stats['hp']} ⚔️{stats['attack']} 🛡{stats['defense']}"
        f"{ab_text}",
        show_alert=True,
    )
