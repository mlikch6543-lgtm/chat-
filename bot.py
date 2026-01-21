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
أنت أب كاهن قبطي أرثوذكسي.
تُجيب على أي سؤال مسيحي (عقيدة، كتاب، تفسير، طقس، تاريخ كنسي، حياة روحية)
لكن دائمًا من منظور الكنيسة القبطية الأرثوذكسية فقط.

✝️ مبدأ أساسي:
- أجب على كل سؤال مسيحي يُطرح عليك
- لا ترفض ولا تعتذر إلا إذا كان السؤال:
  1) غير مسيحي صريح
  2) أو فيه سخرية أو هجوم

━━━━━━━━━━
📌 شكل الإجابة (ثابت دائمًا):
✝️ الإجابة:
📖 الشرح الكنسي:
📜 آية كتابية:
🙏 نصيحة رعوية:

━━━━━━━━━━
📌 قواعد عقائدية صارمة:
1) استخدم المصطلحات الأرثوذكسية فقط
   - ثلاثة أقانيم ❌ ليس ثلاثة أشخاص
   - طبيعة واحدة متجسدة
2) الأسماء الكتابية:
   - يونان (وليس يونس)
   - إيليا (وليس إلياس)
   - داود (وليس داوود)
3) لا تقارن مع ديانات أخرى
4) لا تستخدم مراجع غير مسيحية
5) نفس السؤال = نفس الإجابة

━━━━━━━━━━
📌 التوسيع:
- لو قيل: (اشرح أكتر – مثال تاني – وسّع)
  ➜ كمل الشرح
  ➜ لا تعتذر
  ➜ لا تغيّر الهيكل

━━━━━━━━━━
📌 الأسلوب:
- لغة كنسية واضحة
- نبرة أب كاهن محب
- تعليم + رعاية
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
            "last_seen": now
        }

        await context.bot.send_message(
            ADMIN_ID,
            f"🆕 مستخدم جديد\n"
            f"👤 {user.full_name}\n"
            f"🆔 {uid}\n"
            f"📊 العدد: {len(users_db)}"
        )

    sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    await update.message.reply_text(
        "✝️ بسم الآب والابن والروح القدس، الإله الواحد، آمين.\n\n"
        "ابني الحبيب،\n"
        "هذا البوت الكنسي وُضع لخدمة التعليم المسيحي\n"
        "والإجابة على الأسئلة الإيمانية والروحية\n"
        "بفكر الكنيسة القبطية الأرثوذكسية.\n\n"
        "كل إجابة ستشمل:\n"
        "✝️ جوابًا واضحًا\n"
        "📖 شرحًا كنسيًا\n"
        "📜 آية كتابية\n"
        "🙏 توجيهًا رعويًا\n\n"
        "🛠️ تطوير: جرجس رضا\n\n"
        "اسأل بثقة، والرب يرشد قلبك 🙏"
    )

# ================== CHAT ==================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users_db[uid]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if uid not in sessions:
        sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    sessions[uid].append({"role": "user", "content": update.message.text})

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=sessions[uid],
        temperature=0.0
    )

    reply = response.choices[0].message.content
    sessions[uid].append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply)

# ================== ADMIN ==================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(f"📊 عدد المستخدمين: {len(users_db)}")

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✝️ Orthodox Christian Bot Running | Developed by Gerges Reda ✝️")
    app.run_polling()

if __name__ == "__main__":
    main()
