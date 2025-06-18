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

# --- Database Setup ---

def bot_tables_sql():
    base_sql = sqlite3.connect(DB_PATH)
    base_sql.row_factory = sqlite3.Row
    conn = base_sql.cursor()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            url TEXT UNIQUE NOT NULL,
            channel_id TEXT NOT NULL DEFAULT '-1002519961960'
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS support (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL
        )
        """
    )
    # Seed default courses
    cur = conn.execute("SELECT COUNT(*) AS cnt FROM courses")
    if cur.fetchone()["cnt"] == 0:
        conn.executemany(
            "INSERT INTO  courses (name, url) VALUES (?, ?)",
            [("Экспресс-грамматика", "https://t.me/+uKg4xGQ0MDtkMTBi"), ("Путешествия", "https://t.me/+umKj0R00Rb9jNzE6")]
        )
    base_sql.commit()

# --- Helpers ---
def load_courses_url():
    with get_db_connection() as conn:
        return {row["name"]: row["url"] for row in conn.execute("SELECT name, url FROM courses ORDER BY id")}
    return None


def load_courses_id():
    with get_db_connection() as conn:
        return {row['name']: row['channel_id'] for row in conn.execute("SELECT name, channel_id FROM courses ORDER BY id")}
    return None


# Record payment only if not exists
def record_payment(user_id: int) -> bool:
    with get_db_connection() as conn:
        cur = conn.execute(
            "SELECT 1 FROM payments WHERE user_id = ?",
            (user_id, )
        )
        if cur.fetchone(): return True
        else: return False
    return None


def update_record_payment(user_id: int) -> bool:
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO payments (user_id) VALUES (?)",
                (user_id, ))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Course and support commands

def not_admin(user_id: int) -> bool:
    try:
        with get_db_connection() as conn:
            cur = conn.execute("SELECT * FROM admin WHERE user_id = ?",
                         (user_id,))
            if cur.fetchone():
                return False
            return True
    except sqlite3.IntegrityError:
        return False
    return None

def add_course_to_db(name: str, url: str, id: str) -> bool:
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO courses (name, url, channel_id) VALUES (?, ?, ?)",
                         (name, url, id))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def rename_course_in_db(old: str, new: str) -> bool:
    with get_db_connection() as conn:
        cur = conn.execute(
            "UPDATE courses SET name = ? WHERE name = ?", (new, old)
        )
        conn.commit()
        return cur.rowcount > 0
    return None

def save_new_user(user: types.User):
    with get_db_connection() as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user.id,))
        if not cur.fetchone():
            conn.execute(
                "INSERT INTO users (user_id, first_name, last_name, username) VALUES (?, ?, ?, ?)",
                (user.id, user.first_name, user.last_name, user.username)
            )
            conn.commit()

def load_support():
    with get_db_connection() as conn:
        support = {row['id']: row['user_id'] for row in conn.execute("SELECT id, user_id FROM courses ORDER BY id")}
        return next(iter(support.values()))
    return None

def add_support(user_id: int):
    with get_db_connection() as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user.id,))
        if not cur.fetchone():
            conn.execute(
                "INSERT INTO support (user_id) VALUES (?)",
                (user_id,)
            )
            conn.commit()

def delete_support(user_id: int):
    with get_db_connection() as conn:
        conn.execute(
            "DELETE FROM support WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()

def get_support():
    with get_db_connection() as conn:
        return {row['id']: row['user_id'] for row in conn.execute("SELECT id, user_id FROM support ORDER BY id")}
    return None


async def sql_add_commands_courses(state):
    async with state.proxy() as data_course:
        cur.execute('INSERT INTO courses VALUES (?, ?, ?, ?, ?, ?)',
                    tuple(data_course.values()))

    base_sql.commit()


async def sql_add_commands_teachers(state):
    async with state.proxy() as data_teacher:
        cur.execute('INSERT INTO teachers VALUES (?, ?, ?, ?)',
                    tuple(data_teacher.values()))

    base_sql.commit()


async def sql_read_from_courses(message: types.Message):
    for info_c in cur.execute('SELECT * FROM courses').fetchall():
        await bot.send_photo(message.from_user.id, info_c[1],\
            f'{info_c[0]}\nОписание: {info_c[2]}\n'\
                f'Расписание: {info_c[3]}\nПродолжительность тренировки: {info_c[4]}\nСтоимость тренировки: {info_c[5]} рублей')


async def sql_read_from_teachers(message: types.Message):
    for info_t in cur.execute('SELECT * FROM teachers').fetchall():
        await bot.send_photo(message.from_user.id, info_t[1], \
            f'{info_t[0]}\nОписание: {info_t[2]}\nТренировки: {info_t[3]}')


async def choose_delete_courses():
    return cur.execute('SELECT * FROM courses').fetchall()


async def delete_course(data):
    cur.execute('DELETE FROM courses WHERE title == ?', (data,))
    base_sql.commit()


async def choose_delete_teachers():
    return cur.execute('SELECT * FROM teachers').fetchall()


async def delete_teacher(data):
    cur.execute('DELETE FROM teachers WHERE name == ?', (data, ))
    base_sql.commit()
