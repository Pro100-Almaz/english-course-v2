import asyncio
import os
import traceback
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils import executor
from create_bot import dp, bot
from pathlib import Path
import json

PUBLIC_TERMINAL_ID = os.getenv("PUBLIC_TERMINAL_ID")
template_path = Path(__file__).parent.parent / 'templates' / 'pay.html'
PUBLIC_URL = os.getenv('PUBLIC_URL')

@dp.message_handler(lambda msg: msg.web_app_data is not None)
async def webapp_payment_handler(msg: types.Message):
    """
    This will fire when your Web App calls sendData(...)
    """
    raw = msg.web_app_data.data                    # the JSON string you sent
    try:
        result = json.loads(raw)                   # decode to a dict
    except json.JSONDecodeError:
        await msg.reply("❌ Could not decode payment result.")
        return

    # 👉 Inspect result to see what fields you get
    # You can print it or log it:

    print("💳 Payment widget returned:", result)

    # For example, WidgetResult might contain:
    #   result.success (bool)
    #   result.paymentId
    #   result.externalId
    #   result.amount
    #   result.currency
    #   result.cardMask
    #   result.errorCode / errorMessage
    #
    # Adjust these to match the real shape you see in your console.

    if result.get("success"):
        # 1) Acknowledge to the user
        await msg.reply(f"✅ Payment succeeded!\nOrder ID: {result.get('externalId')}\nAmount: {result.get('amount')}{result.get('currency')}")
        # 2) TODO: save to your database, e.g.:
        #    db.payments.insert_one({
        #      "user_id": msg.from_user.id,
        #      "payment_id": result["paymentId"],
        #      "external_id": result["externalId"],
        #      "amount": result["amount"], …
        #    })
    else:
        await msg.reply(f"❌ Payment failed: {result.get('errorMessage', 'Unknown error')}")

async def start_tiptop(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text='Оплатить',
                web_app=WebAppInfo(url=PUBLIC_URL)
            )
        ]]
    )
    await message.answer('Нажмите кнопку для оплаты:', reply_markup=keyboard)

# aiohttp handler for the payment page
def create_app():
    app = web.Application()
    print("create_app is triggered")

    async def pay(request):
        try:
            # 1) Resolve & verify the template path
            tpl = template_path.resolve()
            print(f"🔍 Loading template from {tpl}")
            if not tpl.exists():
                raise FileNotFoundError(f"Template not found at {tpl}")

            # 2) Read & inject
            html = tpl.read_text(encoding="utf-8")
            html = html.replace("{{PUBLIC_TERMINAL_ID}}", PUBLIC_TERMINAL_ID or "")

            return web.Response(text=html, content_type="text/html")

        except Exception:
            # This will show the real error in your console
            traceback.print_exc()
            return web.Response(
                text="<h1>Internal Server Error</h1>",
                content_type="text/html",
                status=500
            )
    app.router.add_get('/pay', pay)
    return app