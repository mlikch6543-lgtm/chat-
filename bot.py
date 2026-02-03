import os
from datetime import datetime
import google.generativeai as genai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")          # Telegram Bot Token
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")# Gemini API Key
ADMIN_ID = int(os.getenv("ADMIN_ID"))       # Your Telegram ID

# ================== GEMINI ==================
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config={
        "temperature": 0.0,
        "top_p": 1,
        "top_k": 1
    }
)

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = """
أنت أب كاهن قبطي أرثوذكسي.
تُجيب على أي سؤال يخص الإيمان المسيحي القبطي الأرثوذكسي فقط.

❌ لا تتكلم عن أي عقائد أخرى.
❌ لا تعتذر عن أسئلة مسيحية.

📌 قواعد لاهوتية صارمة:
- الله واحد في الجوهر، مثلث الأقانيم (ليس ثلاثة أشخاص).
- الاسم الصحيح: يونان النبي (وليس يونس).
- استخدم مصطلحات الكنيسة القبطية فقط.

📌 التزم دائمًا بنفس ترتيب الإجابة:

✝️ الإجابة المباشرة:
📖 الشرح الكنسي:
📜 آية كتابية:
🙏 نصيحة رعوية:

📌 نفس السؤال = نفس الإجابة (ثبات كامل).
الأسلوب: أب كاهن هادئ، واضح، رعوي، دقيق.
"""

# ================== STORAGE (IN-MEMORY) ==================
users_db = {}     # user_id -> info
sessions = {}     # user_id -> system prompt

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
                "🆕 مستخدم جديد دخل البوت\n\n"
                f"👤 الاسم: {user.full_name}\n"
                f"🔗 اليوزر: @{user.username}\n"
                f"🆔 ID: {uid}\n"
                f"📊 العدد الكلي: {len(users_db)}"
            ),
        )

    sessions[uid] = SYSTEM_PROMPT

    await update.message.reply_text(
        "✝️ بسم الآب والابن والروح القدس، الإله الواحد، آمين.\n\n"
        "ابني الحبيب،\n"
        "هذا البوت خُصِّص ليكون خدمة كنسية أرثوذكسية نقية،\n"
        "تُقدَّم فيها الإجابة بعقل الكنيسة وقلب الأب الكاهن.\n\n"
        "اسأل في أي أمر يخص الإيمان المسيحي القبطي الأرثوذكسي،\n"
        "وستجد إجابة واضحة، مرتبة، وراعوية.\n\n"
        "🛠️ تطوير: جرجس رضا"
    )

# ================== CHAT ==================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in sessions:
        sessions[uid] = SYSTEM_PROMPT

    users_db[uid]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    question = update.message.text.strip()

    prompt = (
        sessions[uid]
        + "\n\n"
        + "سؤال المستخدم:\n"
        + question
    )

    response = model.generate_content(prompt)
    reply = response.text.strip()

    await update.message.reply_text(reply)

# ================== ADMIN COMMANDS ==================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        f"📊 عدد المستخدمين الحالي: {len(users_db)}"
    )

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not users_db:
        await update.message.reply_text("لا يوجد مستخدمون بعد.")
        return

    text = "👥 المستخدمون:\n\n"
    for u in users_db.values():
        text += (
            f"👤 {u['name']}\n"
            f"🆔 {u['id']}\n"
            f"🔗 @{u['username']}\n"
            f"⏰ آخر ظهور: {u['last_seen']}\n"
            "----------------------\n"
        )

    await update.message.reply_text(text)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("اكتب الرسالة بعد الأمر.")
        return

    message = " ".join(context.args)
    count = 0

    for uid in users_db:
        try:
            await context.bot.send_message(uid, message)
            count += 1
        except:
            pass

    await update.message.reply_text(f"✅ تم إرسال الرسالة إلى {count} مستخدم.")

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✝️ Orthodox Coptic Bot Running | Developed by Gerges Reda ✝️")
    app.run_polling()

if __name__ == "__main__":
    main()
