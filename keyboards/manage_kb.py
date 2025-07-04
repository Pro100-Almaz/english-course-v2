from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

download_channel_but = KeyboardButton('Добавить Канал')
update_channel_but = KeyboardButton('Обновить Канал')
delete_channel_but = KeyboardButton('Удалить Канал')

download_material_but = KeyboardButton('Добавить Материал')
view_materials_but = KeyboardButton('Просмотр Материалов')
view_channels_but = KeyboardButton('Просмотр Каналов')
cancel_but = KeyboardButton('Отмена Загрузки')



kb_manage = ReplyKeyboardMarkup(resize_keyboard=True)
(kb_manage.add(cancel_but).add(download_channel_but).insert(delete_channel_but).insert(update_channel_but).
 add(download_material_but).insert(view_materials_but).add(view_channels_but))