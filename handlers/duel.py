import uuid
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from memes import MEMES_CATALOG, ABILITY_NAMES, simulate_battle
from config import DUEL_BET, XP_PER_WIN, XP_PER_LOSS
from handlers.battle import select_meme_kb

router = Router()


def duel_menu_kb():
    b = InlineKeyboardBuilder()
    b.button(text="🤝 Создать дуэль", callback_data="duel_create")
    b.button(text="◀️ Назад",          callback_data="main_menu")
    b.adjust(1)
    return b.as_markup()


@router.callback_query(F.data == "duel_menu")
async def cb_duel_menu(call: CallbackQuery):
    await call.message.edit_text(
        f"🤝 <b>Дуэль с другом</b>\n\n"
        f"Победитель забирает <b>{DUEL_BET * 2}💰</b>\n"
        f"Ставка: {DUEL_BET}💰 с каждого\n\n"
        "Создай дуэль и отправь ссылку другу!",
        reply_markup=duel_menu_kb(), parse_mode="HTML",
    )


@router.callback_query(F.data == "duel_create")
async def cb_duel_create(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    if not user or user["coins"] < DUEL_BET:
        await call.answer(f"❌ Нужно {DUEL_BET}💰 для дуэли.", show_alert=True)
        return
    memes = db.get_user_memes(call.from_user.id)
    if not memes:
        await call.answer("❌ Нет мемов!", show_alert=True)
        return
    await call.message.edit_text(
        "🤝 Выбери мема для дуэли:",
        reply_markup=select_meme_kb("duel_pick", memes),
    )


@router.callback_query(F.data.startswith("duel_pick:"))
async def cb_duel_pick(call: CallbackQuery, bot: Bot):
    meme_row_id = int(call.data.split(":")[1])
    my_meme = db.get_user_meme_by_id(meme_row_id)
    if not my_meme or my_meme["user_id"] != call.from_user.id:
        await call.answer("❌ Мем не найден.", show_alert=True)
        return

    user = db.get_user(call.from_user.id)
    if user["coins"] < DUEL_BET:
        await call.answer(f"❌ Нужно {DUEL_BET}💰.", show_alert=True)
        return

    duel_id = str(uuid.uuid4())[:8]
    db.create_duel(duel_id, call.from_user.id, meme_row_id)
    db.update_coins(call.from_user.id, -DUEL_BET)

    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=duel_{duel_id}"
    my_cat = MEMES_CATALOG.get(my_meme["meme_id"], {})

    b = InlineKeyboardBuilder()
    b.button(text="◀️ Меню", callback_data="main_menu")

    await call.message.edit_text(
        f"🤝 <b>Дуэль создана!</b>\n\n"
        f"Мем: {my_cat.get('emoji','❓')} <b>{my_cat.get('name','?')}</b>\n"
        f"❤️{my_meme['hp']} ⚔️{my_meme['attack']} 🛡{my_meme['defense']}\n\n"
        f"📨 Ссылка:\n<code>{link}</code>\n\n"
        f"Ставка {DUEL_BET}💰 заморожена.",
        reply_markup=b.as_markup(), parse_mode="HTML",
    )


# ── Принятие дуэли (вызывается из start.py) ──────────────────

async def handle_duel_link(message: Message, duel_id: str):
    duel = db.get_duel(duel_id)
    if not duel:
        await message.answer("❌ Дуэль не найдена.")
        return
    if duel["status"] != "waiting":
        await message.answer("❌ Дуэль уже завершена.")
        return
    if duel["challenger_id"] == message.from_user.id:
        await message.answer("😅 Нельзя биться с самим собой!")
        return

    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала напиши /start")
        return
    if user["coins"] < DUEL_BET:
        await message.answer(f"❌ Не хватает монет ({DUEL_BET}💰).")
        return

    memes = db.get_user_memes(message.from_user.id)
    if not memes:
        await message.answer("❌ Нет мемов! Купи в /start → 🛒 Магазин.")
        return

    await message.answer(
        f"⚔️ Тебя вызвали на дуэль!\nСтавка: <b>{DUEL_BET}💰</b>\nВыбери бойца:",
        reply_markup=select_meme_kb(f"duel_accept:{duel_id}", memes),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("duel_accept:"))
async def cb_duel_accept(call: CallbackQuery, bot: Bot):
    parts = call.data.split(":")
    duel_id     = parts[1]
    meme_row_id = int(parts[2])

    duel = db.get_duel(duel_id)
    if not duel or duel["status"] != "waiting":
        await call.answer("❌ Дуэль недоступна.", show_alert=True)
        return

    op_meme = db.get_user_meme_by_id(meme_row_id)
    if not op_meme or op_meme["user_id"] != call.from_user.id:
        await call.answer("❌ Мем не найден.", show_alert=True)
        return

    user = db.get_user(call.from_user.id)
    if user["coins"] < DUEL_BET:
        await call.answer(f"❌ Не хватает монет ({DUEL_BET}💰).", show_alert=True)
        return

    db.update_coins(call.from_user.id, -DUEL_BET)
    db.accept_duel(duel_id, call.from_user.id, meme_row_id)

    ch_meme = db.get_user_meme_by_id(duel["challenger_meme_id"])
    ch_cat  = MEMES_CATALOG.get(ch_meme["meme_id"], {})
    op_cat  = MEMES_CATALOG.get(op_meme["meme_id"], {})

    ch_name = f"{ch_cat.get('emoji','❓')} {ch_cat.get('name','?')}"
    op_name = f"{op_cat.get('emoji','❓')} {op_cat.get('name','?')}"

    winner, log = simulate_battle(
        ch_name, ch_meme["hp"], ch_meme["attack"], ch_meme["defense"], ch_cat.get("ability"),
        op_name, op_meme["hp"], op_meme["attack"], op_meme["defense"], op_cat.get("ability"),
    )
    db.close_duel(duel_id)

    short_log = "\n".join(log[:10])
    prize = DUEL_BET * 2

    if winner == 1:
        win_id, lose_id = duel["challenger_id"], call.from_user.id
        win_name = ch_name
    else:
        win_id, lose_id = call.from_user.id, duel["challenger_id"]
        win_name = op_name

    db.update_coins(win_id, prize)
    db.update_stats(win_id, won=True)
    db.update_stats(lose_id, won=False)
    db.add_xp(win_id, XP_PER_WIN)
    db.add_xp(lose_id, XP_PER_LOSS)

    result_text = (
        f"⚔️ <b>Дуэль!</b>\n\n"
        f"{ch_name}  ❤️{ch_meme['hp']} ⚔️{ch_meme['attack']} 🛡{ch_meme['defense']}\n"
        f"  VS\n"
        f"{op_name}  ❤️{op_meme['hp']} ⚔️{op_meme['attack']} 🛡{op_meme['defense']}\n\n"
        f"<code>{short_log}</code>\n\n"
        f"🏆 Победил <b>{win_name}</b>!\n"
        f"💰 Приз: <b>{prize}💰</b>"
    )

    b = InlineKeyboardBuilder()
    b.button(text="◀️ Меню", callback_data="main_menu")

    await call.message.edit_text(result_text, reply_markup=b.as_markup(), parse_mode="HTML")

    try:
        await bot.send_message(duel["challenger_id"], result_text, parse_mode="HTML")
    except Exception:
        pass
