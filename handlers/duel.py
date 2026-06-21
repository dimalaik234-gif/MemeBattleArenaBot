import uuid
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from memes import MEMES_CATALOG, simulate_battle
from config import DUEL_BET
from handlers.battle import select_meme_kb

router = Router()


def duel_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🤝 Создать дуэль", callback_data="duel_create")
    builder.button(text="◀️ Назад",          callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(F.data == "duel_menu")
async def cb_duel_menu(call: CallbackQuery):
    await call.message.edit_text(
        f"🤝 <b>Дуэль с другом</b>\n\n"
        f"Победитель забирает <b>{DUEL_BET * 2} монет</b>!\n"
        f"(Ставка: {DUEL_BET} монет с каждого)\n\n"
        "Создай дуэль — тебе дадут ссылку, которую отправишь другу.",
        reply_markup=duel_menu_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "duel_create")
async def cb_duel_create(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    if not user or user["coins"] < DUEL_BET:
        await call.answer(f"❌ Нужно {DUEL_BET} монет для дуэли.", show_alert=True)
        return

    memes = db.get_user_memes(call.from_user.id)
    if not memes:
        await call.answer("❌ У тебя нет мемов! Купи в 🛒 Магазине.", show_alert=True)
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
        await call.answer(f"❌ Нужно {DUEL_BET} монет.", show_alert=True)
        return

    duel_id = str(uuid.uuid4())[:8]
    db.create_duel(duel_id, call.from_user.id, meme_row_id)
    db.update_coins(call.from_user.id, -DUEL_BET)  # Резервируем ставку

    # Ссылка для вступления в дуэль
    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=duel_{duel_id}"

    my_cat = MEMES_CATALOG.get(my_meme["meme_id"], {})

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Меню", callback_data="main_menu")

    await call.message.edit_text(
        f"🤝 <b>Дуэль создана!</b>\n\n"
        f"Твой мем: {my_cat.get('emoji','❓')} <b>{my_cat.get('name','?')}</b>\n"
        f"❤️{my_meme['hp']} ⚔️{my_meme['attack']} 🛡{my_meme['defense']}\n\n"
        f"📨 Отправь другу эту ссылку:\n<code>{link}</code>\n\n"
        f"Ставка: <b>{DUEL_BET} монет</b> уже заморожена.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


# ── Принятие дуэли через /start duel_XXXXX ──────────────────

@router.message(Command("start"))
async def handle_duel_deep_link(message: Message):
    """Обрабатываем /start duel_XXXXX — вступление в дуэль."""
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].startswith("duel_"):
        return  # Обычный старт обрабатывает handlers/start.py

    duel_id = args[1][5:]
    duel = db.get_duel(duel_id)

    if not duel:
        await message.answer("❌ Дуэль не найдена или уже завершена.")
        return
    if duel["status"] != "waiting":
        await message.answer("❌ Эта дуэль уже началась или завершена.")
        return
    if duel["challenger_id"] == message.from_user.id:
        await message.answer("😅 Нельзя биться с самим собой!")
        return

    user = db.get_user(message.from_user.id)
    if not user:
        db.create_user(message.from_user.id, message.from_user.username or message.from_user.first_name)
        user = db.get_user(message.from_user.id)

    if user["coins"] < DUEL_BET:
        await message.answer(f"❌ Не хватает монет для дуэли. Нужно {DUEL_BET}💰")
        return

    memes = db.get_user_memes(message.from_user.id)
    if not memes:
        await message.answer("❌ У тебя нет мемов! Купи в /start → 🛒 Магазин.")
        return

    # Показываем выбор мема для принятия дуэли
    await message.answer(
        f"⚔️ Тебя вызвали на дуэль!\nСтавка: <b>{DUEL_BET}</b> монет\nВыбери своего бойца:",
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
        await call.answer("❌ Дуэль уже недоступна.", show_alert=True)
        return

    my_meme = db.get_user_meme_by_id(meme_row_id)
    if not my_meme or my_meme["user_id"] != call.from_user.id:
        await call.answer("❌ Мем не найден.", show_alert=True)
        return

    user = db.get_user(call.from_user.id)
    if user["coins"] < DUEL_BET:
        await call.answer(f"❌ Не хватает монет ({DUEL_BET}💰).", show_alert=True)
        return

    db.update_coins(call.from_user.id, -DUEL_BET)
    db.accept_duel(duel_id, call.from_user.id, meme_row_id)

    # Загружаем мема challenger'а
    ch_meme = db.get_user_meme_by_id(duel["challenger_meme_id"])
    op_meme = my_meme

    ch_cat = MEMES_CATALOG.get(ch_meme["meme_id"], {})
    op_cat = MEMES_CATALOG.get(op_meme["meme_id"], {})

    winner, log = simulate_battle(
        ch_meme["hp"], ch_meme["attack"], ch_meme["defense"],
        op_meme["hp"], op_meme["attack"], op_meme["defense"],
    )
    db.close_duel(duel_id)

    short_log = "\n".join(log[:8])
    prize     = DUEL_BET * 2

    if winner == 1:
        win_id, lose_id = duel["challenger_id"], call.from_user.id
        win_name  = f"{ch_cat.get('emoji','❓')} {ch_cat.get('name','?')}"
        lose_name = f"{op_cat.get('emoji','❓')} {op_cat.get('name','?')}"
    else:
        win_id, lose_id = call.from_user.id, duel["challenger_id"]
        win_name  = f"{op_cat.get('emoji','❓')} {op_cat.get('name','?')}"
        lose_name = f"{ch_cat.get('emoji','❓')} {ch_cat.get('name','?')}"

    db.update_coins(win_id, prize)
    db.update_stats(win_id, won=True)
    db.update_stats(lose_id, won=False)

    result_text = (
        f"⚔️ <b>Дуэль!</b>\n\n"
        f"{ch_cat.get('emoji','❓')} <b>{ch_cat.get('name','?')}</b>  ❤️{ch_meme['hp']} ⚔️{ch_meme['attack']} 🛡{ch_meme['defense']}\n"
        f"  VS\n"
        f"{op_cat.get('emoji','❓')} <b>{op_cat.get('name','?')}</b>  ❤️{op_meme['hp']} ⚔️{op_meme['attack']} 🛡{op_meme['defense']}\n\n"
        f"<code>{short_log}</code>\n\n"
        f"🏆 Победил <b>{win_name}</b>!\n"
        f"💰 Приз: <b>{prize} монет</b>"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Меню", callback_data="main_menu")

    await call.message.edit_text(result_text, reply_markup=builder.as_markup(), parse_mode="HTML")

    # Уведомляем challenger'а
    try:
        await bot.send_message(
            duel["challenger_id"],
            result_text,
            parse_mode="HTML",
        )
    except Exception:
        pass
