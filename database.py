import sqlite3
import json
from typing import Optional

DB_PATH = "meme_battle.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                coins       INTEGER DEFAULT 100,
                wins        INTEGER DEFAULT 0,
                losses      INTEGER DEFAULT 0,
                daily_claimed TEXT DEFAULT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_memes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                meme_id     TEXT,
                hp          INTEGER,
                attack      INTEGER,
                defense     INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS duels (
                duel_id     TEXT PRIMARY KEY,
                challenger_id INTEGER,
                opponent_id   INTEGER DEFAULT NULL,
                challenger_meme_id INTEGER,
                opponent_meme_id   INTEGER DEFAULT NULL,
                status      TEXT DEFAULT 'waiting',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


# ── Пользователи ──────────────────────────────────────────────

def get_user(user_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()


def create_user(user_id: int, username: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username or "Аноним"),
        )
        conn.commit()


def update_coins(user_id: int, delta: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET coins = coins + ? WHERE user_id = ?",
            (delta, user_id),
        )
        conn.commit()


def update_stats(user_id: int, won: bool):
    field = "wins" if won else "losses"
    with get_conn() as conn:
        conn.execute(
            f"UPDATE users SET {field} = {field} + 1 WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()


def claim_daily(user_id: int) -> bool:
    """Возвращает True если бонус ещё не забирали сегодня."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT daily_claimed FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not row:
            return False
        today = __import__("datetime").date.today().isoformat()
        if row["daily_claimed"] == today:
            return False
        conn.execute(
            "UPDATE users SET daily_claimed = ?, coins = coins + 50 WHERE user_id = ?",
            (today, user_id),
        )
        conn.commit()
        return True


# ── Мемы пользователя ─────────────────────────────────────────

def get_user_memes(user_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM user_memes WHERE user_id = ?", (user_id,)
        ).fetchall()


def add_meme_to_user(user_id: int, meme_id: str, hp: int, attack: int, defense: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO user_memes (user_id, meme_id, hp, attack, defense) VALUES (?, ?, ?, ?, ?)",
            (user_id, meme_id, hp, attack, defense),
        )
        conn.commit()


def get_user_meme_by_id(meme_row_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM user_memes WHERE id = ?", (meme_row_id,)
        ).fetchone()


# ── Дуэли ─────────────────────────────────────────────────────

def create_duel(duel_id: str, challenger_id: int, challenger_meme_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO duels (duel_id, challenger_id, challenger_meme_id) VALUES (?, ?, ?)",
            (duel_id, challenger_id, challenger_meme_id),
        )
        conn.commit()


def get_duel(duel_id: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM duels WHERE duel_id = ?", (duel_id,)
        ).fetchone()


def accept_duel(duel_id: str, opponent_id: int, opponent_meme_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE duels SET opponent_id=?, opponent_meme_id=?, status='active' WHERE duel_id=?",
            (opponent_id, opponent_meme_id, duel_id),
        )
        conn.commit()


def close_duel(duel_id: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE duels SET status='done' WHERE duel_id=?", (duel_id,)
        )
        conn.commit()
