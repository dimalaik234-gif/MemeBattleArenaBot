import random
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from memes import MEMES_CATALOG, ABILITY_NAMES, simulate_battle, roll_stats
from config import BATTLE_REWARD, XP_PER_WIN, XP_PER_LOSS

router = Router()


def select_meme_kb(action_prefix: str, memes):
    b = InlineKeyboardBuilder()
    for m in memes:
        cat   = MEMES_CATALOG.get(m["meme_id"], {})
        name  = cat.get("name", m["meme_id"])
        emoji = cat.get("emoji", "❓")
        lvl   = f" Ур.{m['level']}" if m["level"] > 1 else ""
        label = f"{emoji} {name}{lvl}  ❤️{m['hp']} ⚔️{m['attack']} 🛡{m['defense']}"
        b.button(text=label, callback_data=f"{action_prefix}:{m['id']}")
    b.button(text="◀️ Назад", callback_data="main_menu")
    b.adjust(1)
    return b.as_markup()


def battle_menu_kb():
    b = InlineKeyboardBuilder()
    b.button(text="⚔️ Лёгкий бой",       callback_data="battle:easy")
    b.button(text="⚔️ Средний бой",      callback_data="battle:normal")
    b.button(text="⚔️ Тяжёлый бой",      callback_data="battle:hard")
    b.button(text="💀 Босс",             callback_data="battle:boss")
    b.button(text="◀️ Назад",            callback_data="main_menu")
    b.adjust(2)
    return b.as_markup()


DIFFICULTY = {
    "easy":   {"label": "Лёгкий",   "pool": ["doge","trollface","nyan_cat","pepe","harold","cat_bonk"], "reward_mult": 0.8, "xp_mult": 0.7},
    "normal": {"label": "Средний",   "pool": ["chad","crying_cat","drake","cheems","wojak","pikachu"],   "reward_mult": 1.0, "xp_mult": 1.0},
    "hard":   {"label": "Тяжёлый",   "pool": ["stonks","gigachad","big_brain","morbius","skibidi"],      "reward_mult": 1.5, "xp_mult": 1.5},
    "boss":   {"label": "💀 Босс",   "pool": ["shrek","among_us","rickroll","thanos"],                  "reward_mult": 3.0, "xp_mult": 2.5},
}


@router.callback_query(F.data == "battle_menu")
async def cb_battle_menu(call: CallbackQuery):
    energy, eta = db.get_energy(call.from_user.id)
    eta_text = f"\nСлед. восстановление: {eta}" if eta else ""
    await call.message.edit_text(
        f"⚔️ <b>Арена</b>\n\n"
        f"⚡ Энергия: <b>{energy}/5</b>{eta_text}\n\n"
        "Выбери сложность:",
        reply_markup=battle_menu_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("battle:"))
async def cb_battle_select(call: CallbackQuery):
    diff = call.data.split(":")[1]
    if diff not in DIFFICULTY:
        return

    if not db.use_energy(call.from_user.id):
        await call.answer("⚡ Энергия закончилась! Получи бонус или подожди.", show_alert=True)
        return

    memes = db.get_user_memes(call.from_user.id)
    if not memes:
        await call.answer("❌ Нет мемов! Купи в Магазине.", show_alert=True)
        return

    await call.message.edit_text(
        f"⚔️ <b>{DIFFICULTY[diff]['label']}</b> бой\nВыбери мема:",
        reply_markup=select_meme_kb(f"fight:{diff}", memes),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("fight:"))
async def cb_fight(call: CallbackQuery):
    parts = call.data.split(":")
    diff = parts[1]
    meme_row_id = int(parts[2])
    my_meme = db.get_user_meme_by_id(meme_row_id)

    if not my_meme or my_meme["user_id"] != call.from_user.id:
        await call.answer("❌ Мем не найден.", show_alert=True)
        return

    d = DIFFICULTY.get(diff, DIFFICULTY["normal"])

    # Генерируем врага
    enemy_id   = random.choice(d["pool"])
    enemy_info = MEMES_CATALOG[enemy_id]
    e_stats    = roll_stats(enemy_id)

    my_cat = MEMES_CATALOG.get(my_meme["meme_id"], {})
    my_name = f"{my_cat.get('emoji','❓')} {my_cat.get('name','?')}"
    en_name = f"{enemy_info['emoji']} {enemy_info['name']}"

    winner, log = simulate_battle(
        my_name, my_meme["hp"], my_meme["attack"], my_meme["defense"],
        my_cat.get("ability"),
        en_name, e_stats["hp"], e_stats["attack"], e_stats["defense"],
        enemy_info.get("ability"),
    )

    # Берём интересные моменты из лога
    short_log = []
    for line in log:
        if any(k in line for k in ["КРИТ", "уклонился", "ЩЁЛКНУЛ", "восстановил"]):
            short_log.append(line)
    if len(short_log) < 3:
        short_log = log[:4]
    short_log = short_log[:6]
    log_text = "\n".join(short_log)
    if len(log) > len(short_log):
        log_text += f"\n... ещё {len(log) - len(short_log)} ходов ..."

    i_won = winner == 1

    # Награды
    reward = int(BATTLE_REWARD * d["reward_mult"])
    xp_gain = int((XP_PER_WIN if i_won else XP_PER_LOSS) * d["xp_mult"])

    # Бонус за серию побед
    user = db.get_user(call.from_user.id)
    streak_bonus = 0
    if i_won and user["win_streak"] >= 3:
        streak_bonus = user["win_streak"] * 5
        reward += streak_bonus

    db.update_stats(call.from_user.id, won=i_won)
    new_level, leveled_up = db.add_xp(call.from_user.id, xp_gain)

    if i_won:
        db.update_coins(call.from_user.id, reward)
        result = f"🏆 <b>Победа!</b> +{reward}💰  +{xp_gain}XP"
        if streak_bonus:
            result += f"\n🔥 Бонус за серию: +{streak_bonus}💰"
    else:
        result = f"💀 <b>Поражение.</b> +{xp_gain}XP"

    if leveled_up:
        result += f"\n\n🎉 <b>УРОВЕНЬ {new_level}!</b> Новые мемы в магазине!"

    my_ab = my_cat.get("ability")
    en_ab = enemy_info.get("ability")
    my_ab_text = ABILITY_NAMES.get(my_ab, "").split("(")[0].strip() if my_ab else ""
    en_ab_text = ABILITY_NAMES.get(en_ab, "").split("(")[0].strip() if en_ab else ""

    text = (
        f"⚔️ <b>{d['label']}</b>\n\n"
        f"{my_name}  ❤️{my_meme['hp']} ⚔️{my_meme['attack']} 🛡{my_meme['defense']}"
        f"{' '+my_ab_text if my_ab_text else ''}\n"
        f"  VS\n"
        f"🤖 {en_name}  ❤️{e_stats['hp']} ⚔️{e_stats['attack']} 🛡{e_stats['defense']}"
        f"{' '+en_ab_text if en_ab_text else ''}\n\n"
        f"<code>{log_text}</code>\n\n"
        f"{result}"
    )

    b = InlineKeyboardBuilder()
    b.button(text="⚔️ Ещё бой", callback_data="battle_menu")
    b.button(text="◀️ Меню",    callback_data="main_menu")
    b.adjust(2)

    await call.message.edit_text(text, reply_markup=b.as_markup(), parse_mode="HTML")
