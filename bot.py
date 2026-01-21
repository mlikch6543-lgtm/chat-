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
أنت أب كاهن قبطي أرثوذكسي ملتزم تمامًا بتعليم الكنيسة القبطية الأرثوذكسية
كما تسلّمته من الكتاب المقدس، الآباء، والمجامع المسكونية.

✝️ شخصيتك:
- أب كاهن حقيقي: هادئ، واضح، تعليمي، رعوي
- لا فلسفة، لا تبسيط مخل، لا اجتهاد شخصي
- تستخدم المصطلحات اللاهوتية الدقيقة فقط

📌 قواعد صارمة للرد:
1) الترتيب ثابت لا يتغير أبدًا:

✝️ الإجابة:
📖 الشرح الكنسي:
📜 آية كتابية:
🙏 نصيحة رعوية:

2) الإجابة تكون:
- دقيقة لاهوتيًا
- واضحة
- غير متناقضة
- نفس السؤال = نفس الإجابة دائمًا

3) ممنوع استخدام:
- "ثلاثة أشخاص"
- أي تعبير غير أرثوذكسي
(استخدم فقط: ثلاثة أقانيم – جوهر واحد)

4) في حالة طلب:
- "اشرح أكتر"
- "عايز مثال تاني"
- "وضح النقطة دي"

➡️ كمل على نفس الإجابة السابقة
➡️ بنفس الترتيب
➡️ مع توسيع الشرح أو إضافة مثال جديد
➡️ بدون اعتذار أو رفض

5) لو السؤال خارج الإيمان الأرثوذكسي:
- اعتذار أبوي هادئ
- بدون هجوم أو جدال

6) اللغة:
- عربية فصحى كنسية مبسطة
- نبرة أب اعتراف محب
"""

# ================== STORAGE ==================
users_db = {}
sessions = {}

# ================== HELPERS ==================
def is_admin(uid):
    return uid == ADMIN_ID

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("👥 المستخدمين", callback_data="users")],
        [InlineKeyboardButton("📢 رسالة جماعية", callback_data="broadcast")]
    ])

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if uid not in users_db:
        users_db[uid] = {
            "id": uid,
            "full_name": user.full_name,
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
            f"📊 العدد الحالي: {len(users_db)}"
        )

    sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    await update.message.reply_text(
        "✝️ بسم الآب والابن والروح القدس، الإله الواحد، آمين.\n\n"
        "ابني الحبيب،\n"
        "أهلاً بك في هذا البوت الكنسي القبطي الأرثوذكسي،\n"
        "الموضوع بروح الكنيسة وتعليم الآباء،\n"
        "للإجابة على الأسئلة الإيمانية والعقائدية\n"
        "بفكر مستقيم، وتعليم واضح، ونصيحة رعوية أبوية.\n\n"
        "كل إجابة ستجد فيها:\n"
        "✝️ جوابًا مباشرًا\n"
        "📖 شرحًا كنسيًا أرثوذكسيًا\n"
        "📜 آية كتابية\n"
        "🙏 توجيهًا رعويًا للحياة الروحية\n\n"
        "🛠️ تطوير: جرجس رضا\n\n"
        "اتفضل اسأل يا ابني، والرب يديك نعمة وفهم 🙏"
    )

    if is_admin(uid):
        await update.message.reply_text(
            "🔑 لوحة التحكم:",
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
        buttons = [
            [InlineKeyboardButton(u["full_name"], callback_data=f"user_{u['id']}")]
            for u in users_db.values()
        ]
        await q.edit_message_text(
            f"👥 المستخدمون ({len(users_db)}):",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif q.data.startswith("user_"):
        uid = int(q.data.split("_")[1])
        u = users_db.get(uid)
        if u:
            await q.edit_message_text(
                f"👤 الاسم: {u['full_name']}\n"
                f"🆔 ID: {u['id']}\n"
                f"🔗 Username: @{u['username']}\n"
                f"🌍 اللغة: {u['language']}\n"
                f"⏰ أول ظهور: {u['first_seen']}\n"
                f"⏰ آخر تفاعل: {u['last_seen']}"
            )

    elif q.data == "broadcast":
        await q.edit_message_text("📢 استخدم الأمر:\n/broadcast نص الرسالة")

# ================== BROADCAST ==================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    msg = " ".join(context.args)
    for uid in users_db:
        try:
            await context.bot.send_message(uid, msg)
        except:
            pass

    await update.message.reply_text("✅ تم إرسال الرسالة للجميع")

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

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(admin_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✝️ Orthodox Coptic Bot Running | Developed by Gerges Reda ✝️")
    app.run_polling()

if __name__ == "__main__":
    main()
