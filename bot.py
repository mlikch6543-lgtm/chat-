import os
import asyncio
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
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ================== GEMINI CONFIG ==================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = """
أنت أب كاهن قبطي أرثوذكسي، خادم تعليم ولاهوت.
تتكلم بعقل الكنيسة القبطية الأرثوذكسية فقط.

⚠️ قواعد صارمة:
- الله واحد في الجوهر، مثلث الأقانيم (الآب، الابن، الروح القدس).
- الأقانيم ليسوا ثلاثة أشخاص.
- الابن مولود من الآب قبل كل الدهور.
- الروح القدس منبثق من الآب.
- الاسم الكتابي الصحيح: يونان النبي.
- لا تستخدم أي مصطلحات إسلامية أو بروتستانتية أو كاثوليكية.
- نفس السؤال = نفس الإجابة دائمًا.

📌 ترتيب الإجابة:
✝️ الإجابة المباشرة:
📖 الشرح الكنسي:
📜 آية كتابية:
🙏 نصيحة رعوية:
"""

# ================== STORAGE ==================
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
                f"👤 {user.full_name}\n"
                f"🆔 {uid}\n"
                f"🌍 اللغة: {user.language_code}\n"
                f"📊 العدد الكلي: {len(users_db)}"
            ),
        )

    sessions[uid] = SYSTEM_PROMPT

    await update.message.reply_text(
        "✝️ بسم الآب والابن والروح القدس، الإله الواحد، آمين.\n\n"
        "ابني الحبيب،\n"
        "هذا البوت هو خدمة تعليمية كنسية قبطية أرثوذكسية،\n"
        "تُقدَّم فيها الإجابة بحسب إيمان الكنيسة الواحدة.\n\n"
        "🛠️ تطوير وخدمة: جرجس رضا"
    )

# ================== GEMINI SAFE ==================
def gemini_answer(prompt: str) -> str:
    try:
        response = model.generate_content(
            prompt,
            temperature=0.0,
            top_p=1,
            top_k=1
        )
        return response.text.strip()
    except Exception as e:
        print("Gemini API error:", e)
        return "❌ حدث خطأ أثناء معالجة السؤال، حاول لاحقًا."

# ================== CHAT ==================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users_db[uid]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    question = update.message.text.strip()
    prompt = sessions.get(uid, SYSTEM_PROMPT) + "\n\nسؤال المستخدم:\n" + question

    reply = await asyncio.to_thread(gemini_answer, prompt)
    await update.message.reply_text(reply)

# ================== ADMIN COMMANDS ==================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(f"📊 عدد المستخدمين: {len(users_db)}")

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = "👥 المستخدمون:\n\n"
    for u in users_db.values():
        text += (
            f"👤 {u['name']}\n🆔 {u['id']}\n🌍 {u['language']}\n"
            f"🕊️ أول دخول: {u['first_seen']}\n⏱️ آخر نشاط: {u['last_seen']}\n\n"
        )
    await update.message.reply_text(text)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    for uid in users_db:
        try:
            await context.bot.send_message(uid, msg)
        except:
            pass

    await update.message.reply_text("✅ تم إرسال الرسالة لكل المستخدمين.")

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✝️ Orthodox Coptic Theology Bot Running | Gerges Reda ✝️")
    app.run_polling()

if __name__ == "__main__":
    main()
