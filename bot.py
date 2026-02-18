import os
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set")

if not ADMIN_ID:
    raise ValueError("ADMIN_ID not set")

client = OpenAI(api_key=OPENAI_API_KEY)

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = """
أنت أب كاهن قبطي أرثوذكسي، خادم تعليم ولاهوت.

⚠️ قواعد لا تُكسر:
- الله واحد في الجوهر، مثلث الأقانيم (الآب، الابن، الروح القدس).
- الأقانيم ليسوا ثلاثة أشخاص.
- الابن مولود من الآب قبل كل الدهور.
- الروح القدس منبثق من الآب.
- الاسم الصحيح: يونان النبي.
- لا تستخدم مصطلحات غير أرثوذكسية.
- لا تعتذر عن الأسئلة المسيحية.
- نفس السؤال = نفس الإجابة دائمًا.

📌 ترتيب الإجابة إلزامي:

✝️ الإجابة العقائدية:
📖 الشرح الكنسي الأرثوذكسي:
📜 آية كتابية:
🙏 تطبيق رعوي:

الأسلوب: أبوي، لاهوتي، دقيق، ثابت.
"""

# ================== DATABASE MEMORY ==================
users_db = {}
sessions = {}

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if uid not in users_db:
        users_db[uid] = {
            "id": uid,
            "name": user.full_name,
            "username": user.username,
            "language": user.language_code,
            "first_seen": now,
            "last_seen": now,
        }

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"🆕 مستخدم جديد\n"
                f"👤 الاسم: {user.full_name}\n"
                f"🆔 ID: {uid}\n"
                f"🌍 اللغة: {user.language_code}\n"
                f"📊 العدد الكلي: {len(users_db)}"
            ),
        )

    sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    await update.message.reply_text(
        "✝️ بسم الآب والابن والروح القدس، الإله الواحد، آمين.\n\n"
        "هذا البوت خدمة تعليمية كنسية قبطية أرثوذكسية.\n"
        "يمكنك أن تسأل في أي موضوع مسيحي أرثوذكسي.\n\n"
        "🛠️ تطوير: جرجس رضا"
    )

# ================== CHAT ==================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if uid not in users_db:
        users_db[uid] = {
            "id": uid,
            "name": user.full_name,
            "username": user.username,
            "language": user.language_code,
            "first_seen": now,
            "last_seen": now,
        }

    users_db[uid]["last_seen"] = now

    if uid not in sessions:
        sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    question = update.message.text.strip()
    sessions[uid].append({"role": "user", "content": question})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=sessions[uid],
            temperature=0.0
        )

        reply = response.choices[0].message.content.strip()
        sessions[uid].append({"role": "assistant", "content": reply})

        await update.message.reply_text(reply)

    except Exception as e:
        print("OpenAI ERROR:", e)
        await update.message.reply_text(
            "❌ حدث خطأ تقني.\n"
            "تأكد من صحة المفتاح أو وجود رصيد في الحساب."
        )

# ================== ADMIN COMMANDS ==================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(f"📊 عدد المستخدمين: {len(users_db)}")

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = "👥 جميع المستخدمين:\n\n"
    for u in users_db.values():
        text += (
            f"👤 {u['name']}\n"
            f"🆔 {u['id']}\n"
            f"🌍 {u['language']}\n"
            f"🕊️ أول دخول: {u['first_seen']}\n"
            f"⏱️ آخر نشاط: {u['last_seen']}\n\n"
        )

    await update.message.reply_text(text)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("اكتب الرسالة بعد الأمر.")
        return

    msg = " ".join(context.args)

    sent = 0
    for uid in users_db:
        try:
            await context.bot.send_message(uid, msg)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ تم إرسال الرسالة إلى {sent} مستخدم.")

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✝️ Orthodox Coptic Bot Running ✝️")
    app.run_polling()

if __name__ == "__main__":
    main()
