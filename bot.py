import os
import random
import openai
from telegram import Update, ReplyKeyboardMarkup
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
    raise RuntimeError("Missing ENV variables")

openai.api_key = OPENAI_API_KEY

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = """
أنت أب كاهن قبطي أرثوذكسي.
تلتزم فقط بتعليم الكنيسة القبطية الأرثوذكسية.
أسلوبك أبوي، دقيق، ومشجع.
"""

# ================== STORAGE ==================
users = set()

# ================== KEYBOARD ==================
keyboard = ReplyKeyboardMarkup(
    [
        ["📖 آية", "⛪ قديس اليوم"],
        ["📅 قراءات اليوم", "🙏 صلاة"],
        ["💭 سؤال روحي"],
        ["🔄 إعادة ضبط"]
    ],
    resize_keyboard=True
)

# ================== DAILY VERSES ==================
DAILY_VERSES = [
    "«اطلبوا أولًا ملكوت الله وبره» (متى 6:33)",
    "«بدوني لا تقدرون أن تفعلوا شيئًا» (يوحنا 15:5)",
    "«كن أمينًا إلى الموت» (رؤيا 2:10)",
    "«قريب هو الرب من المنسحقين القلوب» (مزمور 34)",
    "«طوبى لأنقياء القلب لأنهم يعاينون الله» (متى 5:8)",
    "«الرب نوري وخلاصي ممن أخاف» (مزمور 27)"
]

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_user.id)

    await update.message.reply_text(
        "✝️ أهلاً بيك في البوت الكنسي الأرثوذكسي\n\n"
        "من دلوقتي هيوصلك كل يوم إشعار بآية من الكتاب المقدس.\n\n"
        "🛠️ تطوير: جرجس رضا",
        reply_markup=keyboard
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.discard(update.effective_user.id)
    await update.message.reply_text("🔄 تم إعادة الضبط ✝️", reply_markup=keyboard)

# ================== BUTTONS ==================
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📖 آية":
        await update.message.reply_text(random.choice(DAILY_VERSES))

    elif text == "🙏 صلاة":
        await update.message.reply_text("يا رب يسوع المسيح، بارك هذا اليوم وعلّمنا طريقك.")

    elif text == "⛪ قديس اليوم":
        await update.message.reply_text("القديس الأنبا أنطونيوس – مثال الجهاد والصلاة.")

    elif text == "📅 قراءات اليوم":
        await update.message.reply_text("إنجيل اليوم: يوحنا 6 – خبز الحياة.")

    elif text == "💭 سؤال روحي":
        await update.message.reply_text("هل صلاتك نابعة من قلبك أم عادة؟")

    elif text == "🔄 إعادة ضبط":
        await reset(update, context)

    else:
        await update.message.reply_text(
            "خلّينا نركّز على التعليم الروحي الأرثوذكسي ✝️"
        )

# ================== DAILY JOB ==================
async def daily_verse(context: ContextTypes.DEFAULT_TYPE):
    verse = random.choice(DAILY_VERSES)
    message = f"📖 آية اليوم:\n\n{verse}\n\nربنا يبارك يومك ✝️"

    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
        except:
            pass

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    # إشعار يومي – 9 صباحًا بتوقيت السيرفر
    app.job_queue.run_daily(
        daily_verse,
        time=__import__("datetime").time(hour=9, minute=0)
    )

    print("✝️ Orthodox Bot with Daily Notifications Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
