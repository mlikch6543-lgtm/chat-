import os
import datetime
import random
import openai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

openai.api_key = OPENAI_API_KEY

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = """
أنت أب كاهن قبطي أرثوذكسي حقيقي.
- أبوي، هادئ، محب، روحاني
- إجابات دقيقة، نموذجية، وكنسية
- تبدأ الإجابة مباشرة بالنتيجة لو السؤال مباشر
- أجب فقط على الأسئلة المسيحية الأرثوذكسية
- أي سؤال خارج الإيمان: اعتذر بمحبة
"""

# ================== STORAGE ==================
users_db = {}
sessions = {}

# ================== DATA ==================
# مثال لتقويم قبطي مبسط (يمكن توسعته لكل أيام السنة)
COPTIC_CALENDAR = {
    (1, 1): {"saint": "القديس مارمرقس", "gospel": "متى 1:1-17"},
    (1, 2): {"saint": "القديس إستفانوس", "gospel": "يوحنا 1:1-14"},
    (1, 3): {"saint": "القديسة مريم العذراء", "gospel": "لوقا 2:1-20"},
    # أضف باقي الأيام هنا...
}

BIBLE_VERSES = [
    "الرب نوري وخلاصي ممن أخاف؟ – مزمور 27",
    "أحبوا أعداءكم وصلوا لأجل الذين يضطهدونكم – متى 5:44",
    "كل شيء قادر على الله – متى 19:26",
]

# ================== HELPERS ==================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def get_today_coptic():
    today = datetime.datetime.now()
    month = today.month  # بالشهر الميلادي مؤقت
    day = today.day
    return COPTIC_CALENDAR.get((month, day), None)

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    if uid not in users_db:
        users_db[uid] = {
            "name": user.full_name,
            "username": user.username,
            "language": user.language_code,
            "level": "مبتدئ",
        }
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"🆕 مستخدم جديد\n"
                f"👤 {user.full_name} (@{user.username})\n"
                f"📊 العدد الكلي: {len(users_db)}"
            ),
        )

    sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    intro = (
        "✝️ بسم الآب والابن والروح القدس ✝️\n\n"
        "أهلاً بك في البوت الأرثوذكسي.\n"
        "أنا هنا كأب كاهن:\n"
        "• أجيب عن أسئلتك الروحية\n"
        "• أشرح الإنجيل والقداسات اليومية\n"
        "• أرافقك في حياتك الروحية\n\n"
        "🛠️ تطوير: جرجس رضا\n"
        "ابدأ بسؤالك 🙏"
    )
    await update.message.reply_text(intro)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sessions.pop(update.effective_user.id, None)
    await update.message.reply_text("🔄 تم بدء محادثة جديدة ✝️")

# ================== ADMIN ==================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(f"📊 عدد مستخدمي البوت: {len(users_db)}")

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = "👥 آخر المستخدمين:\n\n"
    for uid, u in list(users_db.items())[-10:]:
        text += f"- {u['name']} (@{u['username']})\n"
    await update.message.reply_text(text)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("اكتب الرسالة بعد الأمر")
        return
    sent = 0
    for uid in users_db:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ تم الإرسال إلى {sent} مستخدم")

# ================== CHAT ==================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.lower()

    # أوضاع المستخدم
    if "كطفل" in text:
        users_db[uid]["level"] = "طفل"
    elif "كشاب" in text:
        users_db[uid]["level"] = "شاب"
    elif "كخادم" in text:
        users_db[uid]["level"] = "خادم"

    # اعتراف
    if any(word in text for word in ["أبونا", "اعترف", "أنا تعبان"]):
        reply = (
            "🙏 يا ابني، ابدأ بالتوبة والصلاة. "
            "تذكر أن الله يحبك ويرشدك دائمًا.\n"
            "يمكنك الذهاب لأب الاعتراف لمزيد من الإرشاد."
        )
        await update.message.reply_text(reply)
        return

    # قديس اليوم + إنجيل اليوم
    today = get_today_coptic()
    if today:
        if "قديس اليوم" in text:
            await update.message.reply_text(f"🕊️ قديس اليوم: {today['saint']}")
            return
        if "إنجيل اليوم" in text:
            await update.message.reply_text(f"📖 إنجيل اليوم: {today['gospel']}")
            return

    # آية اليوم
    if "آية اليوم" in text:
        verse = random.choice(BIBLE_VERSES)
        await update.message.reply_text(f"📜 آية اليوم: {verse}")
        return

    if uid not in sessions:
        sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    sessions[uid].append({"role": "user", "content": text})

    try:
        res = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=sessions[uid],
            temperature=0.1,
        )
        reply = res.choices[0].message.content
        sessions[uid].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)

    except Exception:
        await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى لاحقًا")

# ================== DAILY NOTIFICATIONS ==================
async def daily_notifications(context: ContextTypes.DEFAULT_TYPE):
    today = get_today_coptic()
    for uid in users_db:
        try:
            # إشعار صباحي
            verse = random.choice(BIBLE_VERSES)
            morning_text = f"☀️ صباح الخير! آية اليوم: {verse}"
            if today:
                morning_text += f"\n🕊️ قديس اليوم: {today['saint']}\n📖 إنجيل اليوم: {today['gospel']}"
            await context.bot.send_message(uid, morning_text)

            # إشعار مسائي
            await context.bot.send_message(uid, "🌙 مساء الخير! تذكر الصلاة اليومية والمحبة الإلهية ✝️")
        except:
            pass

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Chat
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Daily notifications example
    # تحتاج تثبيت job-queue في PTB: pip install "python-telegram-bot[job-queue]"
    # app.job_queue.run_daily(daily_notifications, time=datetime.time(hour=8, minute=0))

    print("✝️ Orthodox Father Bot with Full Coptic Calendar Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
