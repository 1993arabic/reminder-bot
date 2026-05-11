import os
import logging
import asyncio
from datetime import datetime, timedelta
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- الإعدادات ---
# سيتم جلب التوكن ورابط الاستضافة من متغيرات البيئة (Environment Variables)
API_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://your-app-name.onrender.com")
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# إعدادات الخادم (Render يحدد البورت تلقائياً)
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv("PORT", 8080))

# --- تهيئة البوت ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Asia/Riyadh")

# --- الأوامر والدوال ---
async def send_reminder(chat_id: int, text: str):
    await bot.send_message(chat_id, f"⏰ تذكير: {text}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("مرحباً! 👋\nأنا بوت التذكير.\nاستخدم الأمر:\n/remind [عدد_الدقائق] [نص_التذكير]")

@dp.message(Command("remind"))
async def cmd_remind(message: types.Message):
    try:
        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            await message.answer("❌ الصيغة خاطئة. مثال: /remind 15 شرب الماء")
            return

        minutes = int(args[1])
        text = args[2]
        remind_time = datetime.now() + timedelta(minutes=minutes)
        
        scheduler.add_job(send_reminder, 'date', run_date=remind_time, args=[message.chat.id, text])
        await message.answer(f"✅ تم ضبط التذكير بعد {minutes} دقيقة.")
    except ValueError:
        await message.answer("⚠️ يرجى إدخال عدد الدقائق كرقم صحيح.")

# --- دوال تشغيل الويب هوك ---
async def on_startup(bot: Bot):
    # إخبار تيليجرام برابط الويب هوك
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to {WEBHOOK_URL}")
    scheduler.start()

async def on_shutdown(bot: Bot):
    # حذف الويب هوك عند إيقاف البوت
    await bot.delete_webhook()
    logging.info("Webhook deleted")

# --- تشغيل الخادم ---
def main():
    logging.basicConfig(level=logging.INFO)
    
    # إنشاء تطبيق ويب
    app = web.Application()
    
    # ربط البوت بتطبيق الويب
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # إعدادات بدء التشغيل والإيقاف
    setup_application(app, dp, on_startup=on_startup, on_shutdown=on_shutdown, bot=bot)
    
    # تشغيل الخادم
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

if __name__ == '__main__':
    main()