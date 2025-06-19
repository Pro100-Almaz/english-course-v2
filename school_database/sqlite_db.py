import sqlite3 as sq
from create_bot import bot
from aiogram import types


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

    base_sql.commit()


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