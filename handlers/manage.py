from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from magic_filter import F
from create_bot import dp, bot, master_id
from school_database import sqlite_db
from keyboards import kb_manage

"""Администрирование Бота через FSM
Внесение изменений в базу через интерфейс Telegram
Владелец школы сможет сам управлять содержимым каналов и материалов
в мобильном телефоне.
"""

ID_MASTER = int(master_id)


class FSMchannel(StatesGroup):
    channel_id = State()
    title = State()
    description = State()
    topic = State()


class FSMmaterial(StatesGroup):
    channel_selection = State()
    title = State()
    content_type = State()
    content = State()
    file = State()
    discussion_link = State()


"""Бот проверяет является ли пользователь хозяином бота.
Проверка ID_MASTER по ID на совпадение
В целях безопасности необходимо установить запрет на добавление Бота в другие группы!
Активация клавиатуры администратора по команде /moderate
"""


#@dp.message_handler(commands=['moderate'])
async def verify_owner(message: types.Message):
    id_check = message.from_user.id
    if id_check == ID_MASTER:
        await bot.send_message(message.from_user.id, 'Готов к работе, пожалуйста выбери команды на клавиатуре', reply_markup=kb_manage)
        
    else:
        await bot.send_message(message.from_user.id, 'Доступ запрещен')
    await message.delete()


"""Функция отмены, выход из state, если администратор передумал вносить правки в бота
"""
#@dp.message_handler(Text(equals='Отмена Загрузки'), state="*")
#@dp.message_handler(F.text.contains(['отмена', 'stop']).lower(), state="*")
async def cancel_state(message: types.Message, state=FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    else:
        await state.finish()
        await message.reply('Изменения не внесены')


"""Запуск FSM для внесения информации о каналах
"""
# Начало загрузки данных о канале
async def add_channel(message: types.Message):
    if message.from_user.id == ID_MASTER:
        await FSMchannel.channel_id.set()
        await message.reply('Загрузи ID канала (например: @channel_name или -1001234567890)')


# Бот ловит ответ и пишет в словарь ID канала
async def load_channel_id(message: types.Message, state=FSMContext):
    if message.from_user.id == ID_MASTER:
        async with state.proxy() as data_channel:
            data_channel['channel_id'] = message.text
        await FSMchannel.next()
        await message.reply('Загрузи название канала')


# Бот ловит ответ и пишет в словарь название канала
async def load_channel_title(message: types.Message, state=FSMContext):
    if message.from_user.id == ID_MASTER:
        async with state.proxy() as data_channel:
            data_channel['title'] = message.text
        await FSMchannel.next()
        await message.reply('Загрузи описание канала')


# Бот ловит ответ и пишет в словарь описание канала
async def load_channel_description(message: types.Message, state=FSMContext):
    if message.from_user.id == ID_MASTER:
        async with state.proxy() as data_channel:
            data_channel['description'] = message.text
        await FSMchannel.next()
        await message.reply('Загрузи тему канала')


# Бот ловит ответ и пишет в словарь тему канала
async def load_channel_topic(message: types.Message, state=FSMContext):
    if message.from_user.id == ID_MASTER:
        async with state.proxy() as data_channel:
            data_channel['topic'] = message.text

        await sqlite_db.sql_add_commands_channels(state)
        await state.finish()
        await message.reply('Загрузка информации о канале окончена')


"""Запуск FSM для внесения материалов
"""
# Начало загрузки данных о материале
async def add_material(message: types.Message):
    print(f"add_material called by user {message.from_user.id}")  # Debug print
    if message.from_user.id == ID_MASTER:
        try:
            # Получаем список каналов для выбора
            channels = await sqlite_db.get_channels_for_materials()
            if not channels:
                await message.reply('Сначала добавьте канал!')
                return
            
            # Создаем инлайн клавиатуру с каналами
            keyboard = InlineKeyboardMarkup()
            for channel_id, title in channels:
                keyboard.add(InlineKeyboardButton(title, callback_data=f'select_channel_{channel_id}'))
            
            # Add a test button
            keyboard.add(InlineKeyboardButton("Test Button", callback_data='test_button'))
            
            await FSMmaterial.channel_selection.set()
            await message.reply(f'Выберите канал для добавления материала (найдено каналов: {len(channels)}):', reply_markup=keyboard)
        except Exception as e:
            await message.reply(f'Ошибка при получении каналов: {str(e)}')
    else:
        await message.reply('Доступ запрещен')


# Test callback handler to see if any callbacks are being received
async def test_callback(callback_query: types.CallbackQuery):
    print(f"Test callback received: {callback_query.data}")
    await callback_query.answer("Test callback received!")


# Alternative callback handlers using decorators
@dp.callback_query_handler(lambda c: c.data == 'test_button')
async def test_callback_decorator(callback_query: types.CallbackQuery):
    print(f"Decorator test callback received: {callback_query.data}")
    await callback_query.answer("Decorator test callback received!")


@dp.callback_query_handler(lambda c: c.data.startswith('select_channel_'))
async def process_channel_selection_decorator(callback_query: types.CallbackQuery, state=FSMContext):
    print(f"Decorator channel selection callback received: {callback_query.data}")
    if callback_query.from_user.id == ID_MASTER:
        try:
            channel_id = callback_query.data.replace('select_channel_', '')
            print(f"Selected channel_id: {channel_id}")
            async with state.proxy() as data_material:
                data_material['channel_id'] = channel_id
            
            await FSMmaterial.next()
            await callback_query.message.reply('Введите название материала')
            await callback_query.answer()
        except Exception as e:
            print(f"Error in decorator process_channel_selection: {e}")
            await callback_query.message.reply(f'Ошибка при выборе канала: {str(e)}')
            await callback_query.answer()
    else:
        await callback_query.answer('Доступ запрещен')


# Бот ловит ответ и пишет в словарь название материала
async def load_material_title(message: types.Message, state=FSMContext):
    if message.from_user.id == ID_MASTER:
        async with state.proxy() as data_material:
            data_material['title'] = message.text
        await FSMmaterial.next()
        await message.reply('Выберите тип контента:\n1. Текст\n2. Фото\n3. Документ\n4. Видео\n5. Аудио\n\nОтправьте номер (1-5)')


# Бот ловит ответ и пишет в словарь тип контента
async def load_content_type(message: types.Message, state=FSMContext):
    if message.from_user.id == ID_MASTER:
        content_types = {
            '1': 'text',
            '2': 'photo', 
            '3': 'document',
            '4': 'video',
            '5': 'audio'
        }
        
        if message.text not in content_types:
            await message.reply('Пожалуйста, введите число от 1 до 5')
            return
            
        async with state.proxy() as data_material:
            data_material['content_type'] = content_types[message.text]
        
        await FSMmaterial.next()
        await message.reply('Отправьте контент (текст, фото, документ, видео или аудио)')


# Бот ловит контент и сохраняет в словарь
async def load_content(message: types.Message, state=FSMContext):
    if message.from_user.id == ID_MASTER:
        async with state.proxy() as data_material:
            if message.content_type == 'text':
                data_material['content'] = message.text
                data_material['file_id'] = None
            elif message.content_type == 'photo':
                data_material['content'] = message.caption or ''
                data_material['file_id'] = message.photo[0].file_id
            elif message.content_type == 'document':
                data_material['content'] = message.caption or ''
                data_material['file_id'] = message.document.file_id
            elif message.content_type == 'video':
                data_material['content'] = message.caption or ''
                data_material['file_id'] = message.video.file_id
            elif message.content_type == 'audio':
                data_material['content'] = message.caption or ''
                data_material['file_id'] = message.audio.file_id
            else:
                await message.reply('Неподдерживаемый тип контента')
                return
        
        await FSMmaterial.next()
        await message.reply('Отправьте ссылку на обсуждение материала')


# Бот ловит ссылку на обсуждение и сохраняет материал
async def load_discussion_link(message: types.Message, state=FSMContext):
    if message.from_user.id == ID_MASTER:
        async with state.proxy() as data_material:
            data_material['discussion_link'] = message.text

        await sqlite_db.sql_add_commands_materials(state)
        await state.finish()
        await message.reply(f'Материал успешно добавлен!\nСсылка на обсуждение: {message.text}')


"""Инлайн кнопки для удаления из базы сведений о каналах
"""

#@dp.callback_query_handler(lambda x: x.data and x.data.startswith('del_channel '))
async def inform_delete_callback_channels(callback_query: types.CallbackQuery):
    await sqlite_db.delete_channel(callback_query.data.replace('del_channel_', ''))
    await callback_query.answer(text=f'канал {callback_query.data.replace("del_channel_", "")} удален')
    

#@dp.message_handler(Text(equals='Удалить Канал', ignore_case=True))
async def delete_channel_info(message: types.Message):
    if message.from_user.id == ID_MASTER:
        info = await sqlite_db.choose_delete_channels()
        for info_ch in info:
            await bot.send_message(message.from_user.id, f'{info_ch[1]}\nID: {info_ch[0]}\nОписание: {info_ch[2]}')
            await bot.send_message(message.from_user.id, text='Удалить канал?', reply_markup=InlineKeyboardMarkup().\
                add(InlineKeyboardButton(f'delete {info_ch[0]}', callback_data=f'del_channel_{info_ch[0]}')))


#@dp.message_handler(Text(equals='Просмотр Материалов', ignore_case=True))
async def view_materials(message: types.Message):
    if message.from_user.id == ID_MASTER:
        await sqlite_db.sql_read_materials(message)


#@dp.message_handler(Text(equals='Просмотр Каналов', ignore_case=True))
async def view_channels(message: types.Message):
    if message.from_user.id == ID_MASTER:
        await sqlite_db.sql_read_from_channels(message)


# Test message handler
async def test_message(message: types.Message):
    print(f"Test message received: {message.text}")
    await message.reply("Test message received!")


"""Регистрируем хендлеры
"""


def handlers_register_manage(dp: Dispatcher):
    # FSM для каналов
    dp.register_message_handler(verify_owner, commands=['moderate'])
    dp.register_message_handler(
        cancel_state, Text(equals='Отмена Загрузки'), state="*")
    dp.register_message_handler(cancel_state, F.text.contains(
        ['отмена', 'stop']).lower(), state="*")
    
    dp.register_message_handler(add_channel, Text(equals='Добавить Канал', ignore_case=True), state=None)
    dp.register_message_handler(load_channel_id, state=FSMchannel.channel_id)
    dp.register_message_handler(load_channel_title, state=FSMchannel.title)
    dp.register_message_handler(load_channel_description, state=FSMchannel.description)
    dp.register_message_handler(load_channel_topic, state=FSMchannel.topic)
    
    # FSM для материалов
    dp.register_message_handler(add_material, Text(equals='Добавить Материал', ignore_case=True), state=None)
    dp.register_message_handler(load_material_title, state=FSMmaterial.title)
    dp.register_message_handler(load_content_type, state=FSMmaterial.content_type)
    dp.register_message_handler(load_content, content_types=['text', 'photo', 'document', 'video', 'audio'], state=FSMmaterial.content)
    dp.register_message_handler(load_discussion_link, state=FSMmaterial.discussion_link)
    
    # Callback query handlers - register them separately
    dp.register_callback_query_handler(process_channel_selection_decorator, lambda c: c.data.startswith('select_channel_'))
    dp.register_callback_query_handler(test_callback_decorator, lambda c: c.data == 'test_button')
    dp.register_callback_query_handler(inform_delete_callback_channels, lambda c: c.data.startswith('del_channel_'))
    
    dp.register_message_handler(delete_channel_info, Text(equals='Удалить Канал', ignore_case=True))
    dp.register_message_handler(view_materials, Text(equals='Просмотр Материалов', ignore_case=True))
    dp.register_message_handler(view_channels, Text(equals='Просмотр Каналов', ignore_case=True))
    dp.register_message_handler(test_message, Text(equals='test', ignore_case=True))

