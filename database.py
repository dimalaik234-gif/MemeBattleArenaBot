import sqlite3
import datetime
import math
from typing import Optional
from config import (
    MAX_ENERGY, ENERGY_REFILL_HOURS, LEVEL_XP,
    UPGRADE_BASE_COST, UPGRADE_COST_MULT, MAX_MEME_LEVEL, UPGRADE_BONUS,
    START_COINS,
)

DB_PATH = "meme_battle.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id       INTEGER PRIMARY KEY,
                username      TEXT,
                coins         INTEGER DEFAULT 100,
                xp            INTEGER DEFAULT 0,
                level         INTEGER DEFAULT 1,
                wins          INTEGER DEFAULT 0,
                losses        INTEGER DEFAULT 0,
                win_streak    INTEGER DEFAULT 0,
                best_streak   INTEGER DEFAULT 0,
                energy        INTEGER DEFAULT 5,
                last_energy   TEXT DEFAULT NULL,
                daily_claimed TEXT DEFAULT NULL
            );
            CREATE TABLE IF NOT EXISTS user_memes (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER,
                meme_id   TEXT,
                hp        INTEGER,
                attack    INTEGER,
                defense   INTEGER,
                level     INTEGER DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            CREATE TABLE IF NOT EXISTS duels (
                duel_id           TEXT PRIMARY KEY,
                challenger_id     INTEGER,
                opponent_id       INTEGER DEFAULT NULL,
                challenger_meme_id INTEGER,
                opponent_meme_id  INTEGER DEFAULT NULL,
                status            TEXT DEFAULT 'waiting',
                created_at        TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.commit()


# ── Пользователи ──────────────────────────────────────────────

def get_user(user_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()


def create_user(user_id: int, username: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, coins, energy) VALUES (?,?,?,?)",
            (user_id, username or "Аноним", START_COINS, MAX_ENERGY),
        )
        conn.commit()


def update_coins(user_id: int, delta: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET coins=coins+? WHERE user_id=?", (delta, user_id))
        conn.commit()


def add_xp(user_id: int, xp: int) -> tuple[int, bool]:
    """Добавляет XP. Возвращает (новый_уровень, повысился_ли)."""
    user = get_user(user_id)
    new_xp = user["xp"] + xp
    old_level = user["level"]
    new_level = old_level

    for i, req in enumerate(LEVEL_XP):
        if new_xp >= req:
            new_level = i + 1

    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET xp=?, level=? WHERE user_id=?",
            (new_xp, new_level, user_id),
        )
        conn.commit()
    return new_level, new_level > old_level


def update_stats(user_id: int, won: bool):
    with get_conn() as conn:
        if won:
            conn.execute(
                "UPDATE users SET wins=wins+1, win_streak=win_streak+1 WHERE user_id=?",
                (user_id,),
            )
            # Обновляем лучшую серию
            user = get_user(user_id)
            if user and user["win_streak"] > user["best_streak"]:
                conn.execute(
                    "UPDATE users SET best_streak=? WHERE user_id=?",
                    (user["win_streak"], user_id),
                )
        else:
            conn.execute(
                "UPDATE users SET losses=losses+1, win_streak=0 WHERE user_id=?",
                (user_id,),
            )
        conn.commit()


# ── Энергия ────────────────────────────────────────────────────

def _refill_energy(user_id: int):
    """Восстанавливает энергию по таймеру."""
    user = get_user(user_id)
    if not user or user["energy"] >= MAX_ENERGY:
        return

    last = user["last_energy"]
    if not last:
        return

    now = datetime.datetime.now()
    last_dt = datetime.datetime.fromisoformat(last)
    hours_passed = (now - last_dt).total_seconds() / 3600
    refill = int(hours_passed / ENERGY_REFILL_HOURS)

    if refill > 0:
        new_energy = min(MAX_ENERGY, user["energy"] + refill)
        new_last = last_dt + datetime.timedelta(hours=refill * ENERGY_REFILL_HOURS)
        if new_energy >= MAX_ENERGY:
            new_last = None

        with get_conn() as conn:
            conn.execute(
                "UPDATE users SET energy=?, last_energy=? WHERE user_id=?",
                (new_energy, new_last.isoformat() if new_last else None, user_id),
            )
            conn.commit()


def use_energy(user_id: int) -> bool:
    """Тратит 1 энергию. Возвращает False если энергии нет."""
    _refill_energy(user_id)
    user = get_user(user_id)
    if not user or user["energy"] <= 0:
        return False

    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET energy=energy-1, last_energy=? WHERE user_id=?",
            (datetime.datetime.now().isoformat(), user_id),
        )
        conn.commit()
    return True


def get_energy(user_id: int) -> tuple[int, Optional[str]]:
    """Возвращает (текущая_энергия, время_до_следующей)."""
    _refill_energy(user_id)
    user = get_user(user_id)
    if not user:
        return 0, None

    if user["energy"] >= MAX_ENERGY:
        return user["energy"], None

    last = user["last_energy"]
    if last:
        last_dt = datetime.datetime.fromisoformat(last)
        next_refill = last_dt + datetime.timedelta(hours=ENERGY_REFILL_HOURS)
        diff = next_refill - datetime.datetime.now()
        if diff.total_seconds() > 0:
            mins = int(diff.total_seconds() / 60)
            return user["energy"], f"{mins // 60}ч {mins % 60}м"

    return user["energy"], None


# ── Ежедневный бонус ───────────────────────────────────────────

def claim_daily(user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT daily_claimed FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            return False
        today = datetime.date.today().isoformat()
        if row["daily_claimed"] == today:
            return False
        conn.execute(
            "UPDATE users SET daily_claimed=?, coins=coins+50, energy=? WHERE user_id=?",
            (today, MAX_ENERGY, user_id),
        )
        conn.commit()
        return True


# ── Мемы ───────────────────────────────────────────────────────

def get_user_memes(user_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM user_memes WHERE user_id=?", (user_id,)).fetchall()


def count_user_memes(user_id: int) -> int:
    with get_conn() as conn:
        r = conn.execute("SELECT COUNT(*) as c FROM user_memes WHERE user_id=?", (user_id,)).fetchone()
        return r["c"] if r else 0


def add_meme_to_user(user_id: int, meme_id: str, hp: int, attack: int, defense: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO user_memes (user_id, meme_id, hp, attack, defense) VALUES (?,?,?,?,?)",
            (user_id, meme_id, hp, attack, defense),
        )
        conn.commit()


def get_user_meme_by_id(meme_row_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM user_memes WHERE id=?", (meme_row_id,)).fetchone()


def upgrade_meme(meme_row_id: int) -> bool:
    """Улучшает мема на 1 уровень. Возвращает False если макс."""
    meme = get_user_meme_by_id(meme_row_id)
    if not meme or meme["level"] >= MAX_MEME_LEVEL:
        return False

    bonus = 1 + UPGRADE_BONUS
    new_hp  = int(meme["hp"]  * bonus)
    new_atk = int(meme["attack"] * bonus)
    new_def = int(meme["defense"] * bonus)

    with get_conn() as conn:
        conn.execute(
            "UPDATE user_memes SET level=level+1, hp=?, attack=?, defense=? WHERE id=?",
            (new_hp, new_atk, new_def, meme_row_id),
        )
        conn.commit()
    return True


def get_upgrade_cost(meme_level: int) -> int:
    return int(UPGRADE_BASE_COST * (UPGRADE_COST_MULT ** (meme_level - 1)))


def delete_meme(meme_row_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM user_memes WHERE id=?", (meme_row_id,))
        conn.commit()


# ── Таблица лидеров ────────────────────────────────────────────

def get_leaderboard(limit: int = 10):
    with get_conn() as conn:
        return conn.execute(
            "SELECT user_id, username, wins, losses, level, best_streak "
            "FROM users ORDER BY wins DESC, level DESC LIMIT ?",
            (limit,),
        ).fetchall()


# ── Дуэли ──────────────────────────────────────────────────────

def create_duel(duel_id: str, challenger_id: int, challenger_meme_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO duels (duel_id, challenger_id, challenger_meme_id) VALUES (?,?,?)",
            (duel_id, challenger_id, challenger_meme_id),
        )
        conn.commit()


def get_duel(duel_id: str):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM duels WHERE duel_id=?", (duel_id,)).fetchone()


def accept_duel(duel_id: str, opponent_id: int, opponent_meme_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE duels SET opponent_id=?, opponent_meme_id=?, status='active' WHERE duel_id=?",
            (opponent_id, opponent_meme_id, duel_id),
        )
        conn.commit()


def close_duel(duel_id: str):
    with get_conn() as conn:
        conn.execute("UPDATE duels SET status='done' WHERE duel_id=?", (duel_id,))
        conn.commit()
