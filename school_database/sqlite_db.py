"""import sqlite3 as sq
from create_bot import bot
from aiogram import types

"""

import os
import sqlite3
from aiogram import types
from aiogram.types import user
from aiogram.dispatcher import FSMContext

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
                channel_id TEXT NOT NULL DEFAULT '-1002519961960',
                navigation_text TEXT,
                nav_message_id INTEGER 
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
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chapters (
                channel_id INTEGER NOT NULL,
                chapter_name TEXT NOT NULL,
                chapter_message_id INTEGER NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS materials (
                channel_id INTEGER NOT NULL,
                chapter_name TEXT NOT NULL,
                material_message_id INTEGER NOT NULL
            )
            """
        )


        cur = conn.execute("SELECT COUNT(*) AS cnt FROM courses")
        if cur.fetchone()["cnt"] == 0:
            conn.executemany(
                "INSERT INTO  courses (name, url, description) VALUES (?, ?, ?)",
                [
                    # ("Grammar Shots", "https://t.me/+0s5EUexRd0tmMTFi", "Здесь ты найдёшь короткие и понятные " #https://t.me/+T7i7THyfTRNhMmYy
                    #                                                           "видеоуроки (10–15 минут), где я просто "
                    #                                                           "объясняю сложные правила."),
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
        cur.execute("SELECT name, channel_id FROM courses ORDER BY id")
        return { row["name"]: row["channel_id"] for row in cur.fetchall() }


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



def get_channel_by_id(channel_id: str | int) -> dict | None:
    """Возвращает запись курса по Telegram channel_id"""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM courses WHERE channel_id = ?", (str(channel_id),))
        row = cur.fetchone()
        return dict(row) if row else None


def update_channel_field(channel_id: str | int, field: str, value):
    """Обновляет произвольное поле в таблице courses по channel_id"""
    with get_connection() as conn:
        conn.execute(
            f"UPDATE courses SET {field} = ? WHERE channel_id = ?",
            (value, str(channel_id))
        )
        conn.commit()

async def sql_add_commands_channels(state: FSMContext):
    """Сохраняет новый канал в таблице courses на основе данных FSMContext"""
    data = await state.get_data()
    name = data.get('title')
    url = data.get('url')
    description = data.get('description')
    channel_id = data.get('channel_id')
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO courses (name, url, description, channel_id) VALUES (?, ?, ?, ?)",
            (name, url, description, str(channel_id))
        )
        conn.commit()


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

def update_user_info(user_id: str | int, field: str, value):
    """Обновляет произвольное поле в таблице users по user_id"""
    with get_connection() as conn:
        conn.execute(
            f"UPDATE users SET {field} = ? WHERE user_id = ?",
            (value, str(user_id))
        )
        conn.commit()

def get_user_payment_status(user_id: int) -> int | None:
    with get_connection() as conn:
        cur = conn.execute("SELECT payment_status FROM users WHERE user_id = ?", (user_id,))
        return cur.fetchone()["payment_status"]

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

#chapters logic
#
#             CREATE TABLE IF NOT EXISTS chapters (
#                 channel_id INTEGER NOT NULL,
#                 chapter_name TEXT NOT NULL,
#                 chapter_message_id INTEGER NOT NULL
#             )
#
#             CREATE TABLE IF NOT EXISTS materials (
#                 channel_id INTEGER NOT NULL
#                 chapter_name TEXT NOT NULL,
#                 material_message_id INTEGER NOT NULL
#             )

def get_chapter_by_channel_id(channel_id: int):
    with get_connection() as conn:
        return {row['chapter_name']: row['chapter_message_id'] for row in conn.execute("SELECT chapter_name, chapter_message_id FROM chapters WHERE channel_id = ?",
                                                                                       (channel_id,))}
    return None

def get_chapter_from_channel_by_chapter_id(channel_id: int, chapter_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT chapter_name FROM chapters WHERE channel_id = ? AND chapter_message_id = ?",
                           (channel_id, chapter_id)).fetchone()
        if row:
            chapter_name = row['chapter_name']
            return {'chapter_name': chapter_name,
                    'chapter_message_id': chapter_id,
                    'channel_id': channel_id,}
        else:
            return None

def add_chapter_by_channel_id(channel_id: int, chapter_name: str, message_id: int):
    with get_connection() as conn:
        cur = conn.execute("SELECT 1 FROM chapters WHERE channel_id = ? AND chapter_message_id = ?", (channel_id, message_id))
        if cur.fetchone():
            return {row['chapter_name']: row['chapter_message_id'] for row in conn.execute("SELECT chapter_name, chapter_message_id FROM chapters WHERE channel_id = ?", (channel_id,))}
        conn.execute(
            "INSERT INTO chapters (channel_id, chapter_name, chapter_message_id) VALUES (?, ?, ?)",
            (channel_id, chapter_name, message_id)
        )
        conn.commit()
        return {row['chapter_name']: row['chapter_message_id'] for row in conn.execute("SELECT chapter_name, chapter_message_id FROM chapters WHERE channel_id = ?", (channel_id,))}


def add_material_to_chapter(channel_id: int, chapter_name: str, message_id: int):
    with get_connection() as conn:
        cur = conn.execute("SELECT 1 FROM materials WHERE channel_id = ? AND chapter_name = ? AND material_message_id = ?",
                           (chapter_name, message_id, channel_id))
        if cur.fetchone():
            return {'message_id': row['material_message_id'] for row in conn.execute("SELECT material_message_id FROM materials WHERE  channel_id = ? AND chapter_name = ?",
                                                            (channel_id, chapter_name,))}
        conn.execute(
            "INSERT INTO materials (channel_id, chapter_name, material_message_id) VALUES (?, ?, ?)",
            (channel_id, chapter_name, message_id)
        )
        conn.commit()
        return { row['material_message_id'] for row in conn.execute("SELECT material_message_id FROM materials WHERE  channel_id = ? AND chapter_name = ?",
                                                        (channel_id, chapter_name))}
    return None