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

client = OpenAI(api_key=OPENAI_API_KEY)

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = """
أنت أب كاهن قبطي أرثوذكسي.
تُجيب فقط بحسب تعليم الكنيسة القبطية الأرثوذكسية.

قواعد إيمانية لا تُكسر:
- الله واحد في الجوهر، مثلث الأقانيم (وليس ثلاثة أشخاص).
- الاسم الصحيح: يونان النبي (وليس يونس).
- لا تستخدم أي مصطلحات غير أرثوذكسية.
- لا تتأثر ببلد المستخدم أو ثقافته.
- نفس السؤال = نفس الإجابة دائمًا.

ترتيب الإجابة إلزامي:

✝️ الإجابة المباشرة:
📖 الشرح الكنسي:
📜 آية كتابية:
🙏 نصيحة رعوية:

الأسلوب: أبوي، هادئ، تعليمي، دقيق.
"""

# ================== STORAGE ==================
users_db = {}
sessions = {}

# ================== NAME FIXER ==================
def normalize_names(text: str) -> str:
    replacements = {
        "يونس": "يونان",
        "ثلاثة أشخاص": "ثلاثة أقانيم",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

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
                "🆕 مستخدم جديد\n"
                f"👤 {user.full_name}\n"
                f"🆔 {uid}\n"
                f"📊 العدد: {len(users_db)}"
            ),
        )

    sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    await update.message.reply_text(
        "✝️ بسم الآب والابن والروح القدس، الإله الواحد، آمين.\n\n"
        "ابني الحبيب،\n"
        "هذا البوت هو خدمة كنسية قبطية أرثوذكسية خالصة،\n"
        "تُقدَّم فيه الإجابة بعقل الكنيسة وقلب الأب،\n"
        "دون خلط أو اجتهاد خارج الإيمان المستقيم.\n\n"
        "🛠️ تطوير: جرجس رضا"
    )

# ================== CHAT ==================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = normalize_names(update.message.text.strip())

    users_db[uid]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if uid not in sessions:
        sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    sessions[uid].append({"role": "user", "content": text})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=sessions[uid],
            temperature=0.0,
        )
        reply = response.choices[0].message.content
        reply = normalize_names(reply)
        sessions[uid].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text("حدث خطأ تقني، حاول مرة أخرى.")

# ================== ADMIN ==================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(f"📊 عدد المستخدمين: {len(users_db)}")

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = "👥 المستخدمون:\n\n"
    for u in users_db.values():
        text += f"{u['name']} | {u['id']}\n"

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

    await update.message.reply_text("✅ تم الإرسال.")

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✝️ Orthodox Coptic Bot Running | Gerges Reda ✝️")
    app.run_polling()

if __name__ == "__main__":
    main()
