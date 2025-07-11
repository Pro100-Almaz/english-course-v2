from create_bot import dp, bot, client_commands, Dispatcher
from aiogram import types

 
#@dp.message_handler() # Фильтрация спама и мата в чате клиентской части
async def clean_chat(message: types.Message):
     # Only clean messages in groups, not in private chats
     if message.chat.type == 'private' and message.text not in client_commands:
         await message.delete()
         await bot.send_message(message.from_user.id, 'Бот Вас не понял, пожалуйста воспользуйтесь командами на клавиатуре')
         

async def delete_service_updates(message: types.Message):
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

def register_common_handlers(dp: Dispatcher):
    dp.register_message_handler(clean_chat)
    dp.register_message_handler(delete_service_updates,lambda m: m.pinned_message or m.new_chat_photo or m.left_chat_member, content_types=types.ContentType.ANY)