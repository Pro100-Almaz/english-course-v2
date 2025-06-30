"""import sqlite3 as sq
from create_bot import bot
from aiogram import types

"""

import os
import sqlite3
from aiogram import types
from aiogram.types import user
from create_bot import bot

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bot_sql.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


# --- Database Setup ---
def bot_tables_sql():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                url TEXT UNIQUE NOT NULL,
                description TEXT,
                channel_id TEXT NOT NULL DEFAULT '-1002519961960'
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payment_status BOOLEAN DEFAULT FALSE NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS support (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL
            )
            """
        )

        cur = conn.execute("SELECT COUNT(*) AS cnt FROM courses")
        if cur.fetchone()["cnt"] == 0:
            conn.executemany(
                "INSERT INTO  courses (name, url, description) VALUES (?, ?, ?)",
                [
                    ("Grammar Shots", "https://t.me/+0s5EUexRd0tmMTFi", "Здесь ты найдёшь короткие и понятные "
                                                                              "видеоуроки (10–15 минут), где я просто "
                                                                              "объясняю сложные правила."),
                    ("Daily Dose", "https://t.me/+2WlfIjQ55eFhZjJi", "Здесь мы делимся всем, что цепляет нас прямо "
                                                                      "сейчас: мысли, советы, фильмы, путешествия, "
                                                                      "события, лайфхаки."),
                    ("Mentor Support", "https://t.me/+HnvGAVdmN1YzNzJi", "Здесь ты можешь задавать любой вопрос по "
                                                                         "обучению — в любое время, 24/7.\n"
                                                                         "Наши преподаватели и команда всегда на связи, "
                                                                         "чтобы помочь тебе разобраться и не оставить "
                                                                         "без ответа.")
                ]
            )

        conn.commit()


# --- Helpers ---
def load_courses_url():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, url FROM courses ORDER BY id")
        return { row["name"]: row["url"] for row in cur.fetchall() }


def load_courses_url():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, url FROM courses ORDER BY id")
        return { row["name"]: row['url'] for row in cur.fetchall() }


def load_courses_text() -> str:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT name, url, description
              FROM courses
          ORDER BY id
        """)
        # if your cursor returns tuples change to `for name, url, description in cur.fetchall():`
        return [
            {'name': row['name'],
             'url': row['url'],
             'description': row['description']}
            for row in cur.fetchall()
        ]


# Record payment only if not exists
def record_payment(user_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT payment_status FROM users WHERE user_id = ?", (user_id,))
        return cur.fetchone()["payment_status"] == 1


# def update_record_payment(user_id: int) -> bool:
#     try:
#         with get_db_connection() as conn:
#             conn.execute(
#                 "INSERT INTO payments (user_id) VALUES (?)",
#                 (user_id, ))
#             conn.commit()
#         return True
#     except sqlite3.IntegrityError:
#         return False

# Course and support commands

def is_admin(user_id: int) -> bool:
    if user_id in [972366203, 266058709]:
        return True
    return False


def add_course_to_db(name: str, url: str, id: str) -> bool:
    try:
        with get_connection() as conn:
            conn.execute("INSERT INTO courses (name, url, channel_id) VALUES (?, ?, ?)",
                         (name, url, id))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def rename_course_in_db(old: str, new: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE courses SET name = ? WHERE name = ?", (new, old)
        )
        conn.commit()
        return cur.rowcount > 0
    return None

def save_new_user(user: types.User):
    with get_connection() as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user.id,))
        if not cur.fetchone():
            conn.execute(
                "INSERT INTO users (user_id, first_name, last_name, username, payment_status) VALUES (?, ?, ?, ?, FALSE)",
                (user.id, user.first_name, user.last_name, user.username)
            )
            conn.commit()


def get_user_by_id(user_id: int) -> types.User | None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))

        if not cur.fetchone():
            return None

        return types.User(cur.fetchone())


def load_support():
    with get_connection() as conn:
        support = {row['id']: row['user_id'] for row in conn.execute("SELECT id, user_id FROM courses ORDER BY id")}
        return next(iter(support.values()))
    return None


def add_support(user_id: int):
    with get_connection() as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user.id,))
        if not cur.fetchone():
            conn.execute(
                "INSERT INTO support (user_id) VALUES (?)",
                (user_id,)
            )
            conn.commit()


def delete_support(user_id: int):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM support WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()

def get_support():
    with get_connection() as conn:
        return {row['id']: row['user_id'] for row in conn.execute("SELECT id, user_id FROM support ORDER BY id")}
    return None
