"""import sqlite3 as sq
from create_bot import bot
from aiogram import types

"""

import os
import sqlite3
from aiogram import types
from aiogram.types import user
from create_bot import bot


def bot_tables_sql():
    global base_sql
    global cur
    base_sql = sq.connect('bot_sql.db')
    cur = base_sql.cursor()

    if base_sql == True:
        print('Database connected')
    
    cur.execute("""CREATE TABLE IF NOT EXISTS channels(
        channel_id Text PRIMARY KEY,
        title Text,
        description Text,
        topic Text)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS materials(
        material_id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id Text,
        title Text,
        content_type Text,
        content Text,
        file_id Text,
        discussion_link Text,
        FOREIGN KEY (channel_id) REFERENCES channels (channel_id))""")

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


async def sql_add_commands_channels(state):
    async with state.proxy() as data_channel:
        cur.execute('INSERT INTO channels VALUES (?, ?, ?, ?)',
                    tuple(data_channel.values()))

    base_sql.commit()


async def sql_add_commands_materials(state):
    async with state.proxy() as data_material:
        cur.execute('INSERT INTO materials (channel_id, title, content_type, content, file_id, discussion_link) VALUES (?, ?, ?, ?, ?, ?)',
                    (data_material['channel_id'], data_material['title'], data_material['content_type'], 
                     data_material['content'], data_material['file_id'], data_material['discussion_link']))

    base_sql.commit()


async def sql_read_from_channels(message: types.Message):
    channels = cur.execute('SELECT * FROM channels').fetchall()
    if not channels:
        await bot.send_message(message.from_user.id, 'Каналы не найдены')
        return
    
    for info_ch in channels:
        await bot.send_message(message.from_user.id, 
            f'📺 Канал: {info_ch[1]}\n🆔 ID: {info_ch[0]}\n📝 Описание: {info_ch[2]}\n🏷️ Тема: {info_ch[3]}')


async def choose_delete_channels():
    return cur.execute('SELECT * FROM channels').fetchall()


async def delete_channel(data):
    cur.execute('DELETE FROM channels WHERE channel_id == ?', (data,))
    base_sql.commit()


async def get_channels_for_materials():
    return cur.execute('SELECT channel_id, title FROM channels').fetchall()


async def get_materials_for_channel(channel_id):
    return cur.execute('SELECT * FROM materials WHERE channel_id == ?', (channel_id,)).fetchall()


async def get_all_materials():
    return cur.execute('SELECT m.*, c.title as channel_title FROM materials m JOIN channels c ON m.channel_id = c.channel_id').fetchall()


async def sql_read_materials(message: types.Message):
    materials = await get_all_materials()
    if not materials:
        await bot.send_message(message.from_user.id, 'Материалы не найдены')
        return
    
    for material in materials:
        material_id, channel_id, title, content_type, content, file_id, discussion_link, channel_title = material
        
        message_text = f"📚 Материал: {title}\n"
        message_text += f"📺 Канал: {channel_title}\n"
        message_text += f"📝 Тип: {content_type}\n"
        if content:
            message_text += f"📄 Содержание: {content[:100]}{'...' if len(content) > 100 else ''}\n"
        message_text += f"🔗 Обсуждение: {discussion_link}"
        
        await bot.send_message(message.from_user.id, message_text)
