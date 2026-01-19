import os
import openai
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("ENV variables BOT_TOKEN أو OPENAI_API_KEY مش موجودة")

openai.api_key = OPENAI_API_KEY

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = """
أنت مساعد مسيحي شبيه ChatGPT.
متخصص في تفسير الكتاب المقدس،
الإجابة على الأسئلة الروحية،
والشرح البسيط المليان محبة.
"""

# ================== MEMORY ==================
user_sessions = {}

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✝️ أهلاً بيك!\n\n"
        "أنا مساعد مسيحي.\n"
        "اسأل أي سؤال كتابي أو روحي.\n\n"
        "🖼️ لإنشاء صورة:\n"
        "/image وصف الصورة"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_sessions.clear()
    await update.message.reply_text("🔄 تم مسح المحادثة.")

# ================== IMAGE ==================
async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🖼️ اكتب وصف الصورة بعد /image")
        return

    prompt = " ".join(context.args)
    await update.message.reply_text("🎨 جاري إنشاء الصورة...")

    try:
        result = openai.images.generate(
            model="gpt-image-1",
            prompt=f"Christian religious art, sacred style: {prompt}",
            size="1024x1024"
        )
        await update.message.reply_photo(result.data[0].url)
    except Exception as e:
        print(e)
        await update.message.reply_text("❌ حصل خطأ أثناء إنشاء الصورة")

# ================== PHOTO ==================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📷 وصلت الصورة.\nاكتب: ايه ده؟ أو اسألني عنها."
    )

# ================== CHAT ==================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    user_sessions[user_id].append({"role": "user", "content": text})

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=user_sessions[user_id],
            temperature=0.4
        )
        reply = response.choices[0].message.content
        user_sessions[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except Exception as e:
        print(e)
        await update.message.reply_text("❌ حصل خطأ أثناء الرد")

# ================== MAIN ==================
def main():
    # حل نهائي لمشكلة Conflict
    bot = Bot(token=BOT_TOKEN)
    bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook deleted – Polling safe")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("image", image))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
