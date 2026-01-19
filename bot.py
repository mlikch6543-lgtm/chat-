import os
import random
import datetime
import openai
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("Missing ENV variables")

openai.api_key = OPENAI_API_KEY

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = """
أنت أب كاهن قبطي أرثوذكسي رسمي.
تجيب فقط على الأسئلة الخاصة بالإيمان المسيحي الأرثوذكسي.

طريقة الإجابة:
1- آية أو مرجع كتابي
2- شرح حسب تعليم الكنيسة القبطية
3- توجيه رعوي عملي

أسلوبك أبوي وكنسي مصري.
"""

# ================== USERS ==================
users = set()

# ================== KEYBOARD ==================
keyboard = ReplyKeyboardMarkup(
    [
        ["📖 آية", "🙏 صلاة"],
        ["⛪ قديس اليوم", "📅 قراءات اليوم"],
        ["🔄 إعادة ضبط"]
    ],
    resize_keyboard=True
)

# ================== CONTENT ==================
VERSES = [
    "«الرب نوري وخلاصي ممن أخاف» (مزمور 27)",
    "«بدوني لا تقدرون أن تفعلوا شيئًا» (يوحنا 15:5)",
    "«قريب هو الرب من المنسحقين القلوب» (مزمور 34)"
]

MORNING_MSGS = [
    "☀️ صباح الخير مع ربنا\n«هذا هو اليوم الذي صنعه الرب» (مزمور 118)"
]

EVENING_MSGS = [
    "🌙 قبل ما تنام\nراجع يومك قدام ربنا واطلب سلامه."
]

FEASTS = {
    "01-07": "🎄 صوم الميلاد – استعد لمجيء المخلص",
    "01-19": "💧 عيد الغطاس المجيد",
    "04-28": "✝️ عيد القيامة المجيد"
}

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_user.id)
    await update.message.reply_text(
        "✝️ أهلاً بيك\n"
        "أنا بوت كنسي أرثوذكسي للإرشاد الروحي.\n"
        "🛠️ تطوير: جرجس رضا",
        reply_markup=keyboard
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.discard(update.effective_user.id)
    await update.message.reply_text("🔄 تم إعادة الضبط", reply_markup=keyboard)

# ================== BUTTONS ==================
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📖 آية":
        await update.message.reply_text(random.choice(VERSES))
    elif text == "🙏 صلاة":
        await update.message.reply_text("يا رب يسوع المسيح ارحمنا وبارك يومنا.")
    elif text == "🔄 إعادة ضبط":
        await reset(update, context)
    else:
        await chat(update, context)

# ================== CHAT ==================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text}
    ]

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2
        )
        await update.message.reply_text(response.choices[0].message.content)
    except:
        await update.message.reply_text(
            "السؤال ده خارج تعليم الكنيسة الأرثوذكسية.\nخلّينا نركّز على خلاص النفس ✝️"
        )

# ================== JOBS ==================
async def morning_job(context):
    msg = random.choice(MORNING_MSGS)
    for u in users:
        await context.bot.send_message(u, msg)

async def evening_job(context):
    msg = random.choice(EVENING_MSGS)
    for u in users:
        await context.bot.send_message(u, msg)

async def feast_job(context):
    today = datetime.datetime.utcnow().strftime("%m-%d")
    if today in FEASTS:
        for u in users:
            await context.bot.send_message(u, FEASTS[today])

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    app.job_queue.run_daily(morning_job, time=datetime.time(8, 0))
    app.job_queue.run_daily(evening_job, time=datetime.time(21, 0))
    app.job_queue.run_daily(feast_job, time=datetime.time(7, 30))

    print("✝️ Orthodox Full Service Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
