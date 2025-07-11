from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
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
    url           = State()  # Step 1: URL of the channel
    forward       = State()  # Step 2: forwarded message from channel
    title         = State()
    description   = State()
    topic         = State()


class FSMmaterial(StatesGroup):
    channel_selection = State()
    title = State()
    content_type = State()
    content = State()
    file = State()
    discussion_link = State()


class FSMChannelUpdate(StatesGroup):
    choose_channel = State()
    choose_param   = State()
    input_value    = State()
    choose_chapter = State()
    send_video = State()
    chapter_disc = State()


"""Бот проверяет является ли пользователь хозяином бота.
Проверка ID_MASTER по ID на совпадение
В целях безопасности необходимо установить запрет на добавление Бота в другие группы!
Активация клавиатуры администратора по команде /moderate
"""


#@dp.message_handler(commands=['moderate'])
async def verify_owner(message: types.Message):
    id_check = message.from_user.id
    print(id_check)
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
    if message.from_user.id != ID_MASTER:
        return await message.reply("🚫 Доступ запрещён.")

    await FSMchannel.url.set()
    await message.reply(
        "Шаг 1/5: Отправьте URL канала (например https://t.me/my_channel или пригласительную ссылку)."
    )


async def load_channel_url(message: types.Message, state: FSMContext):
    if message.from_user.id != ID_MASTER:
        return
    async with state.proxy() as data:
        data['url'] = message.text.strip()
    await FSMchannel.next()
    await message.reply(
        "Шаг 2/5: Перешлите любое сообщение из этого канала, чтобы бот узнал его numeric ID."
    )


async def load_channel_forward(message: types.Message, state: FSMContext):
    if message.from_user.id != ID_MASTER:
        return

    if not message.forward_from_chat or message.forward_from_chat.type != 'channel':
        return await message.reply("❗️ Пожалуйста, перешлите сообщение именно из канала.")

    channel_chat = message.forward_from_chat
    async with state.proxy() as data:
        data['channel_id'] = channel_chat.id
        data['channel_username'] = getattr(channel_chat, 'username', None)

    # -> move to title entry
    await FSMchannel.next()  # FSMchannel.title
    await message.reply("Шаг 3/5: Введите название канала:")


async def load_channel_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = message.text.strip()
    await FSMchannel.next()  # FSMchannel.description
    await message.reply("Шаг 4/5: Введите описание канала:")


async def load_channel_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text.strip()
    await FSMchannel.next()  # FSMchannel.topic
    await message.reply("Шаг 5/5: Введите тему канала:")


async def load_channel_topic(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['topic'] = message.text.strip()
        await sqlite_db.sql_add_commands_channels(state)

    await state.finish()
    await message.reply("✅ Информация о канале успешно добавлена.")


"""Запуск FSM для обновления информации о каналах
"""
async def update_channel(message: types.Message):
    if message.from_user.id != ID_MASTER:
        return await message.reply("🚫 Доступ запрещён.")

    channels = sqlite_db.load_courses_url()

    kb = InlineKeyboardMarkup(row_width=2)
    for name, ch_id in channels.items():
        kb.add(
            InlineKeyboardButton(
                text=name,
                callback_data = f"upd_ch_{ch_id}"
            )
        )

    await FSMChannelUpdate.choose_channel.set()
    await message.reply(
        "Выберите канал, который хотите обновить:",
        reply_markup=kb
    )


@dp.callback_query_handler(lambda c: c.data.startswith("upd_ch_"), state=FSMChannelUpdate.choose_channel)
async def process_channel_chosen(cb: types.CallbackQuery, state: FSMContext):
    ch_id = int(cb.data.split("_")[-1])
    await state.update_data(channel_id=ch_id)

    kb = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🖋 Название",      callback_data="upd_param_title"),
        InlineKeyboardButton("✍️ Описание",     callback_data="upd_param_description"),
        InlineKeyboardButton("📚 Тема",          callback_data="upd_param_topic"),
        InlineKeyboardButton("🚦 Навигационный текст", callback_data="upd_param_navigation"),
        InlineKeyboardButton("❌ Удалить навигацию", callback_data="upd_param_nav_delete"),
        InlineKeyboardButton("Добавить видео", callback_data="upd_param_video"),
        InlineKeyboardButton("Добавить главу", callback_data="upd_param_chapter"),
    )
    await FSMChannelUpdate.next()  # -> choose_param
    await cb.message.edit_text("Шаг 2/3: Что нужно обновить?", reply_markup=kb)
    await cb.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("upd_param_"), state=FSMChannelUpdate.choose_param)
async def process_param_chosen(cb: types.CallbackQuery, state: FSMContext):
    param = cb.data.split("_")[-1]
    await state.update_data(param=param)
    data = await state.get_data()

    prompts = {
        'title':       "Введите новое название канала:",
        'description': "Введите новое описание канала:",
        'topic':       "Введите новую тему канала:",
        'pinned':      "Введите новый текст закреплённого сообщения:",
        'navigation': "Введите новый навигационный текст (Markdown HTML): \n",
        'video': "Выберите главу для добавления видео",
        'chapter': "Введите название для главы",
    }
    if param not in prompts:#если выбрали удалить
        ch_id = data['channel_id']
        rec = sqlite_db.get_channel_by_id(ch_id)
        if rec['nav_message_id'] is None:
            cb.message.answer("На этом канале нету навигационного сообщения.")
        else:
            await bot.delete_message(rec['channel_id'], rec['nav_message_id'])
            sqlite_db.update_channel_field(ch_id, 'nav_message_id', None)
            sqlite_db.update_channel_field(ch_id, 'navigation_text', None)
            await cb.message.answer("Навигационное сообщение удалено!")

        await state.finish()
        return

    if param == 'video':
        kb = InlineKeyboardMarkup(row_width=2)
        rec = sqlite_db.get_channel_by_id(data['channel_id'])
        chapters = sqlite_db.get_chapter_by_channel_id(rec['channel_id'])   #returs a dictionary of chapters from chapters table which contains {channel_id|chapter_name|chapter_message_id} channel_id and chapter_name are unique pair
                                                                            #contains {name: value, mesage_id: value}
        for chapter, chapter_message_id in chapters.items():
            kb.add(InlineKeyboardButton(text=chapter, callback_data=f"chapter_{chapter_message_id}"))
        await cb.message.answer(
            text=prompts[param],
            reply_markup=kb
        )
        await FSMChannelUpdate.choose_chapter.set()
        return

    else :
        await cb.message.answer(prompts[param])
        await FSMChannelUpdate.next()
        await cb.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("chapter_"), state=FSMChannelUpdate.choose_chapter)
async def process_chapter_selection(cb: types.CallbackQuery, state: FSMContext):
    chapter = cb.data.split("_")[-1]
    await state.update_data(chapter=chapter)
    await cb.message.answer("Отправьте видео:")#user sends video and then we send it to a chennel and add to navigation
    await FSMChannelUpdate.send_video.set()
    await cb.answer()

@dp.message_handler(state=FSMChannelUpdate.send_video, content_types=types.ContentType.VIDEO)
async def process_send_video(message: types.Message, state: FSMContext):
    await message.answer("видео было принято")
    data = await state.get_data()
    chapter_id = data['chapter']
    rec = sqlite_db.get_channel_by_id(int(data['channel_id']))
    chapter = sqlite_db.get_chapter_from_channel_by_chapter_id(channel_id=rec['channel_id'], chapter_id=chapter_id)
    if chapter is None :
        message.answer("Такой главы нету на этом канале")
        return
    kb = InlineKeyboardMarkup(row_width=2)

    try:
        sent = await bot.send_video(
            chat_id=rec['channel_id'],
            video=message.video.file_id,
            parse_mode=types.ParseMode.HTML,
        )
        if sent:
            await message.answer("Ваше видео было добавлено на канал")
    except Exception as e:
        await message.answer(f"Видео не отправилось на канал.\n причина:\n{e}")

    videos = sqlite_db.add_material_to_chapter(
        channel_id=rec['channel_id'],
        chapter_name=chapter['chapter_name'],
        message_id=sent.message_id)   #adds message_id to a videos table key is {chapter_name and chapter_video_id} pair is unique
                                    #returns an array of dictionaries of videos in a chapter_name from db contains: {video[id], video['message_id']}

    if videos is None :
        message.answer("Не получилось взять список материалов из БД")
    print(videos)

    for i, video in enumerate(videos, start=1):
        url = f"https://t.me/c/{rec['channel_id'][4:]}/{video}"
        kb.add(InlineKeyboardButton(text=str(i), url=url))
    print("--------------")
    print(kb)
    try:
        await bot.edit_message_reply_markup(
            chat_id=rec['channel_id'],
            message_id=int(chapter['chapter_message_id']),
            reply_markup=kb
        )
        await message.answer("Ваше видео было добавлено в навигацию")
    except Exception as e:
        await message.answer(f"Не получилось обновить навигацию главы.\n Причина:\n{e}")

    await state.finish()


# Step 4) Receive the new value & apply
@dp.message_handler(state=FSMChannelUpdate.input_value)
async def process_update_input(message: types.Message, state: FSMContext):
    data   = await state.get_data()
    ch_id  = data['channel_id']
    param  = data['param']
    newval = message.text.strip()
    kb = InlineKeyboardMarkup(row_width=2)

    if param == 'chapter':
        await state.update_data(chapter_name=newval) #save chapter name into state.data
        await message.answer("Введите описание для главы:")
        await FSMChannelUpdate.chapter_disc.set() #update state to recieve state discription
        return

    #if there is any hyperlinks add them to inline keyboard

    for entity in message.entities:
        print(entity)
        if entity.type == 'url':
            text = entity.get_text(message.text)
            kb.add(InlineKeyboardButton(text=text, url=text))
        if entity.type == 'text_link':
            text = entity.get_text(message.text)
            kb.add(InlineKeyboardButton(text=text, url=entity.url))

    # 4a) If it’s a DB field (title/description/topic), update your table
    if param in ('title', 'description', 'topic'):
        await sqlite_db.sql_update_channel_field(ch_id, param, newval)
        await message.reply(f"✅ Поле <b>{param}</b> обновлено!", parse_mode=types.ParseMode.HTML)

    # 4b) If it’s the pinned message text, edit in Telegram
    else:  # param == 'nav_message'
        # 1) get chat record from DB to know its Telegram chat_id
        rec = sqlite_db.get_channel_by_id(ch_id)
        chat_id = rec['channel_id']  # stored numeric ID or '@username'
        # 2) fetch the current pinned message
        chat    = await bot.get_chat(chat_id)
        pinned  = chat.pinned_message
        if not pinned:
            # nothing pinned yet → send & pin
            sent = await bot.send_message(
                chat_id= chat_id,
                text=newval,
                reply_markup=kb,
                parse_mode=types.ParseMode.HTML
            )
            await bot.pin_chat_message(chat_id, sent.message_id, disable_notification=True)
            sqlite_db.update_channel_field(ch_id, 'nav_message_id', sent.message_id)
            await message.reply("✅ Сообщение отправлено и закреплено в канале.")
        else:
            # edit existing pinned
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=pinned.message_id,
                    text=newval,
                    reply_markup=kb,
                    parse_mode=types.ParseMode.HTML,
                    disable_web_page_preview=True
                )
                sqlite_db.update_channel_field(ch_id, 'nav_message_id', pinned.message_id,)
                await message.reply("✅ Текст закреплённого сообщения обновлён!")
            except Exception as e:
                await bot.send_message("The message you have sent is exactly the same as the pinned message.")


    await state.finish()

@dp.message_handler(state=FSMChannelUpdate.chapter_disc)
async def process_chapter_name(message: types.Message, state: FSMContext):
    discription = message.text.strip()
    data = await state.get_data()
    ch_id = data['channel_id']
    rec = sqlite_db.get_channel_by_id(ch_id) #get channel info from database
    chapter_name = data['chapter_name']
    chat = await bot.get_chat(rec['channel_id'])
    pinned = chat.pinned_message# info on the channel navigation message
    # kb = InlineKeyboardMarkup(row_width=2)

    sent = await bot.send_message( #send chapter navifation message and save the message
        chat_id=ch_id,
        text=chapter_name + "\n" + discription,
        parse_mode = types.ParseMode.HTML,
        disable_web_page_preview = True
    )
    await message.answer("Навигация главы отправлено в группу!")

    sqlite_db.add_chapter_by_channel_id(int(rec['channel_id']), chapter_name, int(sent.message_id)) # save chapter information to database

    await message.answer("Глава добавлена в базу данных!")

    current_markup = pinned.reply_markup
    url = f"https://t.me/c/{rec['channel_id'][4:]}/{sent.message_id}"
    current_markup.add(InlineKeyboardButton(text=chapter_name, url=url))

    try:
        await bot.edit_message_reply_markup( # edit navigation message to add chapter buttons
            chat_id=ch_id,
            message_id=pinned.message_id,
            reply_markup=current_markup
        )
        await message.answer("Глава добавлена в навигацию канала!")
    except Exception as e:
        await message.answer(f"Обновление закрепленного сообщение не удалось. \n ошибка: \n {e}")
    await state.finish()


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
    dp.register_message_handler(load_channel_url, state=FSMchannel.url)
    dp.register_message_handler(load_channel_forward, content_types=types.ContentTypes.ANY, state=FSMchannel.forward)
    dp.register_message_handler(load_channel_title, state=FSMchannel.title)
    dp.register_message_handler(load_channel_description, state=FSMchannel.description)
    dp.register_message_handler(load_channel_topic, state=FSMchannel.topic)

    dp.register_message_handler(update_channel,
                                Text(equals='Обновить Канал', ignore_case=True), state=None)

    dp.register_callback_query_handler(
        process_channel_chosen,
        lambda c: c.data.startswith("upd_ch_"),
        state=FSMChannelUpdate.choose_channel)

    dp.register_callback_query_handler(
        process_param_chosen,
        lambda c: c.data.startswith("upd_param_"),
        state=FSMChannelUpdate.choose_param)

    dp.register_message_handler(
        process_update_input,
        state=FSMChannelUpdate.input_value)
    
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

