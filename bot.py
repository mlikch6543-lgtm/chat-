import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
import openai

# ================== ENV ==================
BOT_TOKEN = "7664154726:AAGpxqrDNCbk8W1ihUtQW9pqOWnXo6vPIuE"
OPENAI_API_KEY = "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"
openai.api_key = "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"

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = """
أنت مساعد مسيحي شبيه ChatGPT.
متخصص في تفسير الكتاب المقدس، الإجابة على الأسئلة الروحية،
والشرح البسيط المليان محبة.
"""

# ================== MEMORY ==================
user_sessions = {}

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✝️ أهلاً بيك!\n\n"
        "أنا مساعد مسيحي زي ChatGPT.\n"
        "اسأل أي سؤال كتابي أو روحي.\n\n"
        "🖼️ لإنشاء صورة مسيحية:\n"
        "/image وصف الصورة\n\n"
        "⚙️ إعداد: جرجس رضا"
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
        await update.message.reply_text("❌ حصل خطأ أثناء إنشاء الصورة")
        print(e)

# ================== PHOTO ==================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📷 وصلت الصورة.\n"
        "اكتب: *ايه ده؟* أو اسألني عنها.",
        parse_mode="Markdown"
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
        await update.message.reply_text("❌ حصل خطأ أثناء الرد")
        print(e)

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("image", image))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
