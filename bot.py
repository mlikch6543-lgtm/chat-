import os
import openai
import random
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
    raise RuntimeError("ENV variables missing")

openai.api_key = OPENAI_API_KEY

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = """
أنت أب كاهن وأب اعتراف أرثوذكسي.
تتكلم باللهجة المصرية الكنسية.
أسلوبك هادي، مش مُدين، مش متشدد.
ترشد بمحبة، تشجع التوبة، الصلاة، والرجاء.
كلامك قصير، عميق، وأبوي.
"""

# ================== KEYBOARD ==================
keyboard = ReplyKeyboardMarkup(
    [
        ["📖 آية", "⛪ قديس اليوم"],
        ["📅 إنجيل اليوم", "🙏 صلاة"],
        ["💭 سؤال روحي", "🔄 إعادة ضبط"]
    ],
    resize_keyboard=True
)

# ================== DATA ==================
VERSES = [
    "«تَعَالَوْا إِلَيَّ يَا جَمِيعَ الْمُتْعَبِينَ وَالثَّقِيلِي الأَحْمَالِ وَأَنَا أُرِيحُكُمْ» (متى 11:28)",
    "«الرَّبُّ قَرِيبٌ مِنَ الْمُنْكَسِرِي الْقُلُوبِ» (مزمور 34:18)"
]

SAINTS = [
    "✝️ القديس مارمرقس الرسول – كاروز الديار المصرية",
    "✝️ الأنبا أنطونيوس – أب جميع الرهبان",
    "✝️ الأنبا شنوده رئيس المتوحدين"
]

GOSPEL_TODAY = [
    "📖 إنجيل اليوم:\n«أَنَا هُوَ الطَّرِيقُ وَالْحَقُّ وَالْحَيَاةُ» (يوحنا 14:6)"
]

PRAYERS = [
    "🙏 يا رب يسوع المسيح، ارحمني أنا الخاطئ، واملأ قلبي سلامًا.",
    "🙏 ربنا يسوع، سلّم قلبي بين إيديك، وعلّمني أمشي في طريقك."
]

QUESTIONS = [
    "💭 هل علاقتك بربنا فيها صلاة حقيقية ولا مجرد عادة؟",
    "💭 إمتى آخر مرة اعترفت من قلبك؟"
]

# ================== MEMORY ==================
user_sessions = {}

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✝️ أهلاً بيك يا حبيب قلبي\n\n"
        "أنا أب كنسي ومعلم أرثوذكسي،\n"
        "موجود أسمعك وأرشدك بمحبة.\n\n"
        "⛪ اسأل براحتك، وخد وقتك.\n"
        "ربنا معاك 🤍\n\n"
        "🛠️ تم تطويري بواسطة: جرجس رضا",
        reply_markup=keyboard
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_sessions.clear()
    await update.message.reply_text(
        "🔄 ابتدينا من جديد… ربنا يجدّد قلبك ✝️",
        reply_markup=keyboard
    )

# ================== BUTTON HANDLERS ==================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📖 آية":
        await update.message.reply_text(random.choice(VERSES))
    elif text == "⛪ قديس اليوم":
        await update.message.reply_text(random.choice(SAINTS))
    elif text == "📅 إنجيل اليوم":
        await update.message.reply_text(random.choice(GOSPEL_TODAY))
    elif text == "🙏 صلاة":
        await update.message.reply_text(random.choice(PRAYERS))
    elif text == "💭 سؤال روحي":
        await update.message.reply_text(random.choice(QUESTIONS))
    elif text == "🔄 إعادة ضبط":
        await reset(update, context)
    else:
        await chat(update, context)

# ================== CHAT ==================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_sessions:
        user_sessions[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    user_sessions[user_id].append({"role": "user", "content": text})

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=user_sessions[user_id],
            temperature=0.3
        )

        reply = response.choices[0].message.content
        user_sessions[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)

    except Exception:
        await update.message.reply_text(
            "ربنا يدّيك سلام… خلّينا نكمّل بهدوء 🙏"
        )

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, buttons)
    )

    print("✝️ Orthodox Confessor Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
