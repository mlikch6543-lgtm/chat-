import os
import openai
from datetime import datetime
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
أنت أب كاهن قبطي أرثوذكسي رسمي.
هذا البوت كنسي أرثوذكسي فقط، يجيب وفق الإيمان الأرثوذكسي القوطي.
ممنوع تمامًا أي خلط مع ديانات أو مذاهب أخرى.

⚠️ قواعد صارمة:
1) كل سؤال كنسي → الإجابة تكون:
   ✝️ الإجابة
   📖 الشرح الكنسي
   📜 الآية الكتابية
   🙏 النصيحة الرعوية

2) نفس السؤال = نفس الإجابة دائمًا، بدون أي تنويع.

3) الأسماء:
- استخدم الأسماء الأرثوذكسية فقط
- مثال: يونان (وليس يونس)، إيليا (وليس إلياس)، داود (وليس داوود)

4) أي سؤال خارج الإيمان الأرثوذكسي → اعتذار مختصر أبوي، بدون جدال، بدون شرح بديل.

5) درجة الحرارة = 0.0 لتوحيد الردود.
"""

# ================== STORAGE ==================
users_db = {}
sessions = {}

# ================== HELPERS ==================
def is_admin(uid):
    return uid == ADMIN_ID

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # تسجيل المستخدم
    if uid not in users_db:
        users_db[uid] = {
            "id": uid,
            "name": user.full_name,
            "username": user.username,
            "language": user.language_code,
            "first_seen": now,
            "last_seen": now
        }

    # إنشاء جلسة جديدة
    sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # رسالة ترحيبية
    await update.message.reply_text(
        "✝️ بسم الآب والابن والروح القدس، الإله الواحد، آمين.\n\n"
        "أهلاً بك في هذا البوت الكنسي الأرثوذكسي القبطي.\n"
        "كل إجابة ستأتيك في أربع نقاط ثابتة:\n"
        "✝️ إجابة\n"
        "📖 شرح كنسي\n"
        "📜 آية كتابية\n"
        "🙏 نصيحة رعوية\n\n"
        "🛠️ تطوير: جرجس رضا\n\n"
        "اسأل بحرية، والرب يباركك."
    )

# ================== CHAT ==================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users_db[uid]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if uid not in sessions:
        sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    sessions[uid].append({"role": "user", "content": update.message.text})

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=sessions[uid],
            temperature=0.0
        )
        reply = response.choices[0].message.content
        sessions[uid].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("❌ حصل خطأ أثناء الرد")
        print(e)

# ================== ADMIN ==================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        await update.message.reply_text(f"📊 عدد المستخدمين: {len(users_db)}")

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        text = "👥 المستخدمون:\n"
        for u in users_db.values():
            text += f"- {u['name']} (@{u['username']})\n"
        await update.message.reply_text(text)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("✉️ اكتب الرسالة بعد /broadcast")
        return
    message = " ".join(context.args)
    for uid in users_db.keys():
        try:
            await context.bot.send_message(uid, f"📢 رسالة من المسؤول:\n\n{message}")
        except:
            continue
    await update.message.reply_text("✅ تم إرسال الرسالة لكل المستخدمين.")

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # أوامر المستخدم
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # أوامر الإدارة
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("broadcast", broadcast))

    print("✝️ Orthodox Coptic Bot Running | Developed by Gerges Reda ✝️")
    app.run_polling()

if __name__ == "__main__":
    main()
