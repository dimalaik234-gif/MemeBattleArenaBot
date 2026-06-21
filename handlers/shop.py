from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from memes import MEMES_CATALOG, RARITY_COLORS, roll_stats

router = Router()

PAGE_SIZE = 4


def shop_page_kb(page: int = 0):
    builder = InlineKeyboardBuilder()
    items = list(MEMES_CATALOG.items())
    start = page * PAGE_SIZE
    end   = min(start + PAGE_SIZE, len(items))

    for meme_id, info in items[start:end]:
        color = RARITY_COLORS.get(info["rarity"], "⬛")
        label = f"{color} {info['emoji']} {info['name']} — {info['price']}💰"
        builder.button(text=label, callback_data=f"buy:{meme_id}")

    # Пагинация
    nav = []
    if page > 0:
        nav.append(("◀️", f"shop_page:{page-1}"))
    if end < len(items):
        nav.append(("▶️", f"shop_page:{page+1}"))
    for label, data in nav:
        builder.button(text=label, callback_data=data)

    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def shop_text():
    return (
        "🛒 <b>Магазин мемов</b>\n\n"
        "Выбери мема и купи его!\n"
        "Каждый мем имеет <b>случайные</b> статы при покупке.\n\n"
        f"{RARITY_COLORS['Обычный']} Обычный  "
        f"{RARITY_COLORS['Редкий']} Редкий  "
        f"{RARITY_COLORS['Эпический']} Эпический  "
        f"{RARITY_COLORS['Легендарный']} Легендарный"
    )


@router.callback_query(F.data == "shop")
async def cb_shop(call: CallbackQuery):
    await call.message.edit_text(shop_text(), reply_markup=shop_page_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("shop_page:"))
async def cb_shop_page(call: CallbackQuery):
    page = int(call.data.split(":")[1])
    await call.message.edit_text(shop_text(), reply_markup=shop_page_kb(page), parse_mode="HTML")


@router.callback_query(F.data.startswith("buy:"))
async def cb_buy(call: CallbackQuery):
    meme_id = call.data.split(":", 1)[1]
    info    = MEMES_CATALOG.get(meme_id)
    if not info:
        await call.answer("❌ Мем не найден", show_alert=True)
        return

    user = db.get_user(call.from_user.id)
    if not user:
        await call.answer("Сначала напиши /start", show_alert=True)
        return

    if user["coins"] < info["price"]:
        await call.answer(
            f"💸 Не хватает монет! Нужно {info['price']}, у тебя {user['coins']}.",
            show_alert=True,
        )
        return

    # Списать монеты и выдать мема со случайными статами
    db.update_coins(call.from_user.id, -info["price"])
    stats = roll_stats(meme_id)
    db.add_meme_to_user(call.from_user.id, meme_id, **stats)

    await call.answer(
        f"✅ Куплен {info['emoji']} {info['name']}!\n"
        f"❤️ HP: {stats['hp']}  ⚔️ ATK: {stats['attack']}  🛡 DEF: {stats['defense']}",
        show_alert=True,
    )
