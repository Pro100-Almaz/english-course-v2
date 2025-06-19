from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

download_channel_but = KeyboardButton('Добавить Канал')
download_material_but = KeyboardButton('Добавить Материал')
view_materials_but = KeyboardButton('Просмотр Материалов')
view_channels_but = KeyboardButton('Просмотр Каналов')
canceal_but = KeyboardButton('Отмена Загрузки')
delete_but_channel = KeyboardButton('Удалить Канал')


kb_manage = ReplyKeyboardMarkup(resize_keyboard=True)
kb_manage.add(canceal_but).add(download_channel_but).insert(delete_but_channel).add(download_material_but).insert(view_materials_but).add(view_channels_but)