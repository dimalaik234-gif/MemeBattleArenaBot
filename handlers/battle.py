import random
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from memes import MEMES_CATALOG, simulate_battle
from config import BATTLE_REWARD

router = Router()


def select_meme_kb(action_prefix: str, memes):
    """Клавиатура выбора мема для боя/дуэли."""
    builder = InlineKeyboardBuilder()
    for m in memes:
        cat  = MEMES_CATALOG.get(m["meme_id"], {})
        name = cat.get("name", m["meme_id"])
        emoji = cat.get("emoji", "❓")
        label = f"{emoji} {name}  ❤️{m['hp']} ⚔️{m['attack']} 🛡{m['defense']}"
        builder.button(text=label, callback_data=f"{action_prefix}:{m['id']}")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def battle_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="⚔️ Биться с рандомом", callback_data="battle_random")
    builder.button(text="◀️ Назад",              callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(F.data == "battle_menu")
async def cb_battle_menu(call: CallbackQuery):
    await call.message.edit_text(
        "⚔️ <b>Арена</b>\n\nВыбери режим боя:",
        reply_markup=battle_menu_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "battle_random")
async def cb_battle_random(call: CallbackQuery):
    memes = db.get_user_memes(call.from_user.id)
    if not memes:
        await call.answer("❌ У тебя нет мемов! Купи в 🛒 Магазине.", show_alert=True)
        return
    await call.message.edit_text(
        "⚔️ Выбери мема для боя:",
        reply_markup=select_meme_kb("fight", memes),
    )


@router.callback_query(F.data.startswith("fight:"))
async def cb_fight(call: CallbackQuery):
    meme_row_id = int(call.data.split(":")[1])
    my_meme = db.get_user_meme_by_id(meme_row_id)

    if not my_meme or my_meme["user_id"] != call.from_user.id:
        await call.answer("❌ Мем не найден.", show_alert=True)
        return

    # Генерируем врага из случайного мема каталога
    enemy_id   = random.choice(list(MEMES_CATALOG.keys()))
    enemy_info = MEMES_CATALOG[enemy_id]
    from memes import roll_stats
    e_stats = roll_stats(enemy_id)

    my_cat = MEMES_CATALOG.get(my_meme["meme_id"], {})

    # Симуляция боя
    winner, log = simulate_battle(
        my_meme["hp"], my_meme["attack"], my_meme["defense"],
        e_stats["hp"], e_stats["attack"], e_stats["defense"],
    )

    short_log = log[:6]  # Показываем первые 6 ходов чтобы не спамить
    log_text  = "\n".join(short_log)
    if len(log) > 6:
        log_text += f"\n... ещё {len(log)-6} ходов ..."

    i_won = winner == 1
    if i_won:
        db.update_coins(call.from_user.id, BATTLE_REWARD)
        db.update_stats(call.from_user.id, won=True)
        result = f"🏆 <b>Ты победил!</b> +{BATTLE_REWARD} монет"
    else:
        db.update_stats(call.from_user.id, won=False)
        result = "💀 <b>Ты проиграл!</b> Купи мемов покруче и попробуй снова."

    text = (
        f"⚔️ <b>{my_cat.get('emoji','❓')} {my_cat.get('name','?')}</b>  "
        f"❤️{my_meme['hp']} ⚔️{my_meme['attack']} 🛡{my_meme['defense']}\n"
        f"  VS\n"
        f"🤖 <b>{enemy_info['emoji']} {enemy_info['name']}</b>  "
        f"❤️{e_stats['hp']} ⚔️{e_stats['attack']} 🛡{e_stats['defense']}\n\n"
        f"<code>{log_text}</code>\n\n"
        f"{result}"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="⚔️ Ещё раз", callback_data="battle_random")
    builder.button(text="◀️ Меню",   callback_data="main_menu")
    builder.adjust(2)

    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
