import os
import openai
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
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
أنت أب كاهن قبطي أرثوذكسي ملتزم بتعليم الكنيسة القبطية الأرثوذكسية فقط.

⚠️ قواعد صارمة لا تُخالف:
1) لا تجتهد ولا تستنتج ولا تخمّن.
2) لا تغيّر الإجابة من مرة لأخرى.
3) نفس السؤال = نفس الإجابة دائمًا.
4) اعتمد فقط على:
   - الكتاب المقدس
   - تعليم الآباء
   - العقيدة الأرثوذكسية القبطية

5) لو السؤال فيه (كم – عدد – أول – ثاني – ترتيب – من هو):
   ابدأ الإجابة فورًا بجواب مباشر واضح.
   مثال:
   "الإجابة: القديس إستفانوس هو أول الشهداء."
   ثم الشرح.

6) لو السؤال يحتاج تعداد:
   استخدم ترقيم ثابت (1، 2، 3).

7) لو السؤال خارج الإيمان الأرثوذكسي:
   اعتذر بمحبة ووضوح بدون شرح إضافي.

الأسلوب:
- أبوي
- هادئ
- تعليمي
- ثابت
"""

# ================== STORAGE ==================
users_db = {}
sessions = {}

# ================== HELPERS ==================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 عدد المستخدمين", callback_data="stats")],
        [InlineKeyboardButton("👥 آخر المستخدمين", callback_data="users")],
        [InlineKeyboardButton("📢 رسالة جماعية", callback_data="broadcast")]
    ])

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # تسجيل كل معلومات المستخدم المتاحة
    if uid not in users_db:
        users_db[uid] = {
            "id": uid,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "username": user.username,
            "language": user.language_code,
            "is_bot": user.is_bot,
            "first_seen": now,
            "last_seen": now,
        }

        # إشعار الأدمن
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🆕 مستخدم جديد دخل البوت\n\n"
                f"🆔 ID: {uid}\n"
                f"👤 الاسم: {user.full_name}\n"
                f"🔗 Username: @{user.username}\n"
                f"🌍 Language: {user.language_code}\n"
                f"⏰ First Seen: {now}\n"
                f"📊 العدد الكلي: {len(users_db)}"
            )
        )
    else:
        users_db[uid]["last_seen"] = now

    sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    await update.message.reply_text(
        "✝️ بسم الآب والابن والروح القدس ✝️\n\n"
        "أهلاً بك يا ابني الحبيب.\n"
        "أنا هنا كأب كاهن قبطي أرثوذكسي،\n"
        "أجيب عن أسئلتك بإجابات دقيقة وثابتة\n"
        "حسب تعليم الكنيسة القبطية الأرثوذكسية.\n\n"
        "🛠️ تطوير: جرجس رضا\n\n"
        "اتفضل اسأل بكل ثقة 🙏"
    )

    if is_admin(uid):
        await update.message.reply_text(
            "🔑 لوحة التحكم الخاصة بك:",
            reply_markup=admin_keyboard()
        )

# ================== ADMIN CALLBACK ==================
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not is_admin(q.from_user.id):
        return

    if q.data == "stats":
        await q.edit_message_text(f"📊 عدد المستخدمين: {len(users_db)}")

    elif q.data == "users":
        text = "👥 آخر المستخدمين:\n\n"
        for u in list(users_db.values())[-10:]:
            text += (
                f"- {u['full_name']} (@{u['username']})\n"
                f"  🆔 {u['id']} | 🌍 {u['language']}\n"
                f"  ⏰ Last seen: {u['last_seen']}\n\n"
            )
        await q.edit_message_text(text)

    elif q.data == "broadcast":
        await q.edit_message_text("📢 استخدم:\n/broadcast نص_الرسالة")

# ================== BROADCAST ==================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    msg = " ".join(context.args)
    if not msg:
        return

    sent = 0
    for uid in users_db:
        try:
            await context.bot.send_message(uid, msg)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ تم الإرسال إلى {sent} مستخدم")

# ================== CHAT ==================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if uid in users_db:
        users_db[uid]["last_seen"] = now

    if uid not in sessions:
        sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    sessions[uid].append({"role": "user", "content": text})

    try:
        res = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=sessions[uid],
            temperature=0.0,
            top_p=1.0
        )

        reply = res.choices[0].message.content
        sessions[uid].append({"role": "assistant", "content": reply})

        await update.message.reply_text(reply)

    except:
        await update.message.reply_text("❌ حدث خطأ مؤقت، حاول لاحقًا")

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(admin_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✝️ Orthodox Stable Bot Running | Developed by Gerges Reda ✝️")
    app.run_polling()

if __name__ == "__main__":
    main()
