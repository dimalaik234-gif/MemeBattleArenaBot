import random

MEMES_CATALOG = {
    # ── Обычные (50-70) ────────────────────────────────────────
    "doge":       {"name": "Doge",          "emoji": "🐕", "price": 50,  "base_hp": 80,  "base_atk": 20, "base_def": 15, "rarity": "Обычный",    "ability": None, "min_level": 1},
    "trollface":  {"name": "Trollface",     "emoji": "😈", "price": 50,  "base_hp": 70,  "base_atk": 25, "base_def": 10, "rarity": "Обычный",    "ability": None, "min_level": 1},
    "nyan_cat":   {"name": "Nyan Cat",      "emoji": "🌈", "price": 60,  "base_hp": 90,  "base_atk": 15, "base_def": 20, "rarity": "Обычный",    "ability": None, "min_level": 1},
    "pepe":       {"name": "Pepe",          "emoji": "🐸", "price": 70,  "base_hp": 85,  "base_atk": 22, "base_def": 18, "rarity": "Обычный",    "ability": None, "min_level": 1},
    "harold":     {"name": "Hide Pain Harold","emoji":"😬","price": 55,  "base_hp": 95,  "base_atk": 18, "base_def": 22, "rarity": "Обычный",    "ability": None, "min_level": 1},
    "cat_bonk":   {"name": "Bonk Cat",      "emoji": "🐱", "price": 65,  "base_hp": 75,  "base_atk": 28, "base_def": 12, "rarity": "Обычный",    "ability": None, "min_level": 1},

    # ── Редкие (120-160) ───────────────────────────────────────
    "chad":       {"name": "Chad",          "emoji": "💪", "price": 150, "base_hp": 120, "base_atk": 40, "base_def": 30, "rarity": "Редкий",     "ability": "crit",  "min_level": 2},
    "crying_cat": {"name": "Crying Cat",    "emoji": "😿", "price": 120, "base_hp": 100, "base_atk": 35, "base_def": 25, "rarity": "Редкий",     "ability": "heal",  "min_level": 2},
    "drake":      {"name": "Drake",         "emoji": "🤴", "price": 140, "base_hp": 110, "base_atk": 38, "base_def": 28, "rarity": "Редкий",     "ability": "dodge", "min_level": 2},
    "cheems":     {"name": "Cheems",        "emoji": "🐶", "price": 130, "base_hp": 115, "base_atk": 32, "base_def": 35, "rarity": "Редкий",     "ability": "armor", "min_level": 2},
    "wojak":      {"name": "Wojak",         "emoji": "😢", "price": 125, "base_hp": 130, "base_atk": 30, "base_def": 20, "rarity": "Редкий",     "ability": "heal",  "min_level": 2},
    "pikachu":    {"name": "Surprised Pikachu","emoji":"⚡","price": 160, "base_hp": 105, "base_atk": 42, "base_def": 22, "rarity": "Редкий",     "ability": "crit",  "min_level": 3},

    # ── Эпические (280-400) ────────────────────────────────────
    "stonks":     {"name": "Stonks Man",    "emoji": "📈", "price": 300, "base_hp": 180, "base_atk": 60, "base_def": 50, "rarity": "Эпический",  "ability": "crit",  "min_level": 4},
    "gigachad":   {"name": "GigaChad",      "emoji": "🗿", "price": 350, "base_hp": 200, "base_atk": 70, "base_def": 55, "rarity": "Эпический",  "ability": "armor", "min_level": 4},
    "big_brain":  {"name": "Big Brain",     "emoji": "🧠", "price": 320, "base_hp": 160, "base_atk": 75, "base_def": 40, "rarity": "Эпический",  "ability": "crit",  "min_level": 5},
    "morbius":    {"name": "Morbius",       "emoji": "🧛", "price": 380, "base_hp": 190, "base_atk": 65, "base_def": 60, "rarity": "Эпический",  "ability": "lifesteal","min_level": 5},
    "skibidi":    {"name": "Skibidi Toilet","emoji": "🚽", "price": 280, "base_hp": 170, "base_atk": 55, "base_def": 45, "rarity": "Эпический",  "ability": "dodge", "min_level": 4},

    # ── Легендарные (500-800) ──────────────────────────────────
    "shrek":      {"name": "Shrek",         "emoji": "🧅", "price": 600, "base_hp": 300, "base_atk": 100,"base_def": 80, "rarity": "Легендарный","ability": "heal",      "min_level": 6},
    "among_us":   {"name": "Among Us Red",  "emoji": "🔴", "price": 500, "base_hp": 250, "base_atk": 90, "base_def": 75, "rarity": "Легендарный","ability": "backstab",  "min_level": 6},
    "rickroll":   {"name": "Rick Astley",   "emoji": "🎤", "price": 700, "base_hp": 280, "base_atk": 95, "base_def": 85, "rarity": "Легендарный","ability": "dodge",     "min_level": 7},
    "thanos":     {"name": "Thanos",        "emoji": "🟣", "price": 800, "base_hp": 350, "base_atk": 110,"base_def": 90, "rarity": "Легендарный","ability": "snap",      "min_level": 8},
}

RARITY_COLORS = {
    "Обычный":     "⬜",
    "Редкий":      "🟦",
    "Эпический":   "🟪",
    "Легендарный":  "🟨",
}

ABILITY_NAMES = {
    "crit":      "🎯 Крит (шанс x2 урона)",
    "dodge":     "💨 Уклонение (шанс увернуться)",
    "heal":      "💚 Регенерация (лечение каждый 3-й ход)",
    "armor":     "🛡 Броня (снижение урона 20%)",
    "lifesteal": "🩸 Вампиризм (лечится от урона)",
    "backstab":  "🔪 Удар в спину (первый удар x3)",
    "snap":      "💥 Щелчок (шанс мгновенного убийства)",
}


def roll_stats(meme_id: str) -> dict:
    m = MEMES_CATALOG[meme_id]
    def roll(base):
        return max(1, int(base * random.uniform(0.8, 1.2)))
    return {"hp": roll(m["base_hp"]), "attack": roll(m["base_atk"]), "defense": roll(m["base_def"])}


def get_available_memes(player_level: int) -> dict:
    """Возвращает мемов доступных для уровня игрока."""
    return {k: v for k, v in MEMES_CATALOG.items() if v["min_level"] <= player_level}


def simulate_battle(
    name1: str, hp1: int, atk1: int, def1: int, ability1,
    name2: str, hp2: int, atk2: int, def2: int, ability2,
) -> tuple[int, list[str]]:
    """Пошаговый бой с абилками. Возвращает (победитель 1/2, лог)."""
    log = []
    cur_hp1, cur_hp2 = hp1, hp2
    max_hp1, max_hp2 = hp1, hp2

    # Backstab — первый удар x3
    backstab1 = ability1 == "backstab"
    backstab2 = ability2 == "backstab"

    for turn in range(1, 51):
        # ── Атака 1 → 2 ──────────────────────────
        if ability2 == "dodge" and random.random() < 0.15:
            log.append(f"💨 Ход {turn}: {name2} уклонился!")
        else:
            dmg = max(1, atk1 - random.randint(0, def2))

            # Armor: -20% урона
            if ability2 == "armor":
                dmg = max(1, int(dmg * 0.8))

            # Crit: 20% шанс x2
            crit = ability1 == "crit" and random.random() < 0.20
            if crit:
                dmg *= 2

            # Backstab: первый удар x3
            if backstab1:
                dmg *= 3
                backstab1 = False

            cur_hp2 -= dmg
            crit_txt = " 🎯 КРИТ!" if crit else ""
            log.append(f"⚔️ Ход {turn}: {name1} → {dmg} урона{crit_txt} (HP {name2}: {max(0, cur_hp2)})")

            # Lifesteal
            if ability1 == "lifesteal":
                heal = dmg // 4
                cur_hp1 = min(max_hp1, cur_hp1 + heal)

        # Snap: 3% шанс мгновенного килла
        if ability1 == "snap" and cur_hp2 > 0 and random.random() < 0.03:
            cur_hp2 = 0
            log.append(f"💥 {name1} ЩЁЛКНУЛ! {name2} уничтожен мгновенно!")

        if cur_hp2 <= 0:
            break

        # Heal: каждый 3-й ход
        if ability2 == "heal" and turn % 3 == 0:
            heal = int(max_hp2 * 0.08)
            cur_hp2 = min(max_hp2, cur_hp2 + heal)
            log.append(f"💚 {name2} восстановил {heal} HP")

        # ── Атака 2 → 1 ──────────────────────────
        if ability1 == "dodge" and random.random() < 0.15:
            log.append(f"💨 Ход {turn}: {name1} уклонился!")
        else:
            dmg2 = max(1, atk2 - random.randint(0, def1))

            if ability1 == "armor":
                dmg2 = max(1, int(dmg2 * 0.8))

            crit2 = ability2 == "crit" and random.random() < 0.20
            if crit2:
                dmg2 *= 2

            if backstab2:
                dmg2 *= 3
                backstab2 = False

            cur_hp1 -= dmg2
            crit_txt = " 🎯 КРИТ!" if crit2 else ""
            log.append(f"🛡 Ход {turn}: {name2} → {dmg2} урона{crit_txt} (HP {name1}: {max(0, cur_hp1)})")

            if ability2 == "lifesteal":
                heal = dmg2 // 4
                cur_hp2 = min(max_hp2, cur_hp2 + heal)

        if ability2 == "snap" and cur_hp1 > 0 and random.random() < 0.03:
            cur_hp1 = 0
            log.append(f"💥 {name2} ЩЁЛКНУЛ! {name1} уничтожен мгновенно!")

        if cur_hp1 <= 0:
            break

        if ability1 == "heal" and turn % 3 == 0:
            heal = int(max_hp1 * 0.08)
            cur_hp1 = min(max_hp1, cur_hp1 + heal)
            log.append(f"💚 {name1} восстановил {heal} HP")

    winner = 1 if cur_hp1 > 0 else 2
    return winner, log
