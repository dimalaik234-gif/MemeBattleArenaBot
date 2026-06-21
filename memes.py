import random

# Каталог мемов: id -> {name, emoji, price, base_hp, base_atk, base_def, rarity}
MEMES_CATALOG = {
    # ── Обычные (Common) ──────────────────────────────────────
    "doge": {
        "name": "Doge",
        "emoji": "🐕",
        "price": 50,
        "base_hp": 80,
        "base_atk": 20,
        "base_def": 15,
        "rarity": "Обычный",
    },
    "trollface": {
        "name": "Trollface",
        "emoji": "😈",
        "price": 50,
        "base_hp": 70,
        "base_atk": 25,
        "base_def": 10,
        "rarity": "Обычный",
    },
    "nyan_cat": {
        "name": "Nyan Cat",
        "emoji": "🌈",
        "price": 60,
        "base_hp": 90,
        "base_atk": 15,
        "base_def": 20,
        "rarity": "Обычный",
    },
    "pepe": {
        "name": "Pepe the Frog",
        "emoji": "🐸",
        "price": 70,
        "base_hp": 85,
        "base_atk": 22,
        "base_def": 18,
        "rarity": "Обычный",
    },
    # ── Редкие (Rare) ──────────────────────────────────────────
    "chad": {
        "name": "Chad",
        "emoji": "💪",
        "price": 150,
        "base_hp": 120,
        "base_atk": 40,
        "base_def": 30,
        "rarity": "Редкий",
    },
    "crying_cat": {
        "name": "Crying Cat",
        "emoji": "😿",
        "price": 120,
        "base_hp": 100,
        "base_atk": 35,
        "base_def": 25,
        "rarity": "Редкий",
    },
    "drake": {
        "name": "Drake",
        "emoji": "🤴",
        "price": 140,
        "base_hp": 110,
        "base_atk": 38,
        "base_def": 28,
        "rarity": "Редкий",
    },
    # ── Эпические (Epic) ───────────────────────────────────────
    "stonks": {
        "name": "Stonks Man",
        "emoji": "📈",
        "price": 300,
        "base_hp": 180,
        "base_atk": 60,
        "base_def": 50,
        "rarity": "Эпический",
    },
    "gigachad": {
        "name": "GigaChad",
        "emoji": "🗿",
        "price": 350,
        "base_hp": 200,
        "base_atk": 70,
        "base_def": 55,
        "rarity": "Эпический",
    },
    # ── Легендарные (Legendary) ────────────────────────────────
    "shrek": {
        "name": "Shrek",
        "emoji": "🧅",
        "price": 600,
        "base_hp": 300,
        "base_atk": 100,
        "base_def": 80,
        "rarity": "Легендарный",
    },
    "among_us": {
        "name": "Among Us Red",
        "emoji": "🔴",
        "price": 500,
        "base_hp": 250,
        "base_atk": 90,
        "base_def": 75,
        "rarity": "Легендарный",
    },
}

RARITY_COLORS = {
    "Обычный":    "⬜",
    "Редкий":     "🟦",
    "Эпический":  "🟪",
    "Легендарный":"🟨",
}


def roll_stats(meme_id: str) -> dict:
    """Генерирует случайные статы на базе meme_id с ±20% разбросом."""
    m = MEMES_CATALOG[meme_id]
    def roll(base):
        return max(1, int(base * random.uniform(0.8, 1.2)))
    return {
        "hp":      roll(m["base_hp"]),
        "attack":  roll(m["base_atk"]),
        "defense": roll(m["base_def"]),
    }


def simulate_battle(
    hp1: int, atk1: int, def1: int,
    hp2: int, atk2: int, def2: int
) -> tuple[int, list[str]]:
    """
    Пошаговый бой. Возвращает (победитель: 1 или 2, лог боя).
    """
    log = []
    cur_hp1, cur_hp2 = hp1, hp2
    turn = 0

    while cur_hp1 > 0 and cur_hp2 > 0:
        turn += 1
        if turn > 30:          # защита от бесконечного цикла
            break

        # Атака 1 → 2
        dmg = max(1, atk1 - random.randint(0, def2))
        cur_hp2 -= dmg
        log.append(f"⚔️ Ход {turn}: Мем 1 бьёт на {dmg} урона. HP противника: {max(0, cur_hp2)}")

        if cur_hp2 <= 0:
            break

        # Атака 2 → 1
        dmg2 = max(1, atk2 - random.randint(0, def1))
        cur_hp1 -= dmg2
        log.append(f"🛡 Ход {turn}: Мем 2 бьёт на {dmg2} урона. HP твоего мема: {max(0, cur_hp1)}")

    winner = 1 if cur_hp1 > 0 else 2
    return winner, log
