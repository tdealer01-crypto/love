import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="สวัสดีครับ ผมคือเอเจ้นlove พร้อมรับคำสั่งแล้วครับ! ลองส่งข้อความอะไรมาก็ได้ แล้วผมจะสรุปเป็นภาษาไทยให้ครับ"
    )

import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure the Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None
    logging.warning("GEMINI_API_KEY not found. Summarization will be disabled.")

async def summarize_text(text_to_summarize: str) -> str:
    """Uses Gemini to summarize the given text in Thai."""
    if not model:
        return "ขออภัยครับ ฟังก์ชันสรุปข้อความยังไม่พร้อมใช้งานเนื่องจาก API Key ของ Gemini หายไป"

    try:
        prompt = f"กรุณาสรุปข้อความต่อไปนี้ให้เป็นภาษาไทยที่เข้าใจง่ายและกระชับ: \n\n\"{text_to_summarize}\""
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        return f"เกิดข้อผิดพลาดในการสรุปข้อความ: {e}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives user messages, summarizes them, and sends back the summary."""
    user_text = update.message.text
    chat_id = update.effective_chat.id

    # Acknowledge receipt
    await context.bot.send_message(chat_id=chat_id, text="ได้รับข้อความแล้ว กำลังสรุปให้ครับ...")

    summary = await summarize_text(user_text)

    await context.bot.send_message(chat_id=chat_id, text=summary)


if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment variables.")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("AgentLove Bot is running...")
    application.run_polling()
