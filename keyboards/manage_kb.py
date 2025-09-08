from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

download_channel_but = KeyboardButton('Добавить Канал')
update_channel_but = KeyboardButton('Обновить Канал')
delete_channel_but = KeyboardButton('Удалить Канал')

download_material_but = KeyboardButton('Обновить ссылки в глав. канале')
view_channels_but = KeyboardButton('Просмотр Каналов')
cancel_but = KeyboardButton('Отмена Загрузки')
update_manager = KeyboardButton('Обновить менеджера')
link_update = KeyboardButton('Обновить ссылку')
link_payment_update = KeyboardButton('Обновить информацию про пользователя')



kb_manage = ReplyKeyboardMarkup(resize_keyboard=True)
(kb_manage.add(cancel_but).add(download_channel_but).insert(delete_channel_but).insert(update_channel_but).
 add(download_material_but).add(view_channels_but).insert(link_update)).add(link_payment_update).insert(update_manager)