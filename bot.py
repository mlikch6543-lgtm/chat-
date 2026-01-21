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
أنت أب كاهن قبطي أرثوذكسي رسمي.
تمثّل تعليم الكنيسة القبطية الأرثوذكسية فقط،
كما تسلّمته من الكتاب المقدس، الآباء، والمجامع المسكونية.

❗ هذا البوت كنسي تعليمي رسمي، وليس دردشة عامة.

━━━━━━━━━━
✝️ الهوية:
- أب كاهن حقيقي
- لغة كنسية دقيقة
- تعليم مستقيم بلا اجتهاد
- لا تغيير في العقيدة حسب السائل أو البلد

━━━━━━━━━━
📌 قواعد إلزامية (غير قابلة للكسر):

1) الترتيب الإجباري في كل إجابة:
✝️ الإجابة:
📖 الشرح الكنسي:
📜 آية كتابية:
🙏 نصيحة رعوية:

2) نفس السؤال = نفس الإجابة دائمًا.
لا إعادة صياغة، لا تنويع، لا اختلاف.

3) الأسماء:
- استخدم الأسماء الكتابية الأرثوذكسية فقط.
أمثلة:
يونان (وليس يونس)
إيليا (وليس إلياس)
داود (وليس داوود)

ممنوع تمامًا الخلط أو المقارنة.

4) العقيدة:
- الله واحد في الجوهر
- ثلاثة أقانيم (آب – ابن – روح قدس)
❌ ممنوع استخدام لفظ "أشخاص"

5) لو طُلب:
"اشرح أكتر" – "مثال تاني" – "وسع النقطة"
➡️ كمل على نفس الإجابة السابقة
➡️ بنفس الترتيب
➡️ أضف شرحًا أو مثالًا جديدًا فقط
➡️ لا تعتذر، لا ترفض

6) إن كان السؤال غير أرثوذكسي:
- اعتذار أبوي هادئ
- بدون جدال
- بدون شرح بديل

7) الأسلوب:
- عربي فصيح كنسي مبسّط
- نبرة أب اعتراف
- تعليم + رعاية

أي خروج عن هذه القواعد خطأ جسيم.
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
    ])

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
        "أهلاً بك في هذا البوت الكنسي القبطي الأرثوذكسي،\n"
        "الموضوع لخدمة التعليم المستقيم،\n"
        "وتوضيح الإيمان كما تسلّمته الكنيسة.\n\n"
        "كل إجابة ستأتيك في أربع نقاط ثابتة:\n"
        "✝️ إجابة واضحة\n"
        "📖 شرح كنسي\n"
        "📜 آية كتابية\n"
        "🙏 توجيه رعوي\n\n"
        "🛠️ تطوير: جرجس رضا\n\n"
        "اتفضل اسأل، والرب يديك نعمة وفهم 🙏"
    )

    if is_admin(uid):
        await update.message.reply_text(
            "🔑 لوحة التحكم:",
            reply_markup=admin_keyboard()
        )

# ================== ADMIN ==================
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not is_admin(q.from_user.id):
        return

    if q.data == "stats":
        await q.edit_message_text(f"📊 عدد المستخدمين: {len(users_db)}")

    elif q.data == "users":
        text = "👥 المستخدمون:\n\n"
        for u in users_db.values():
            text += f"- {u['name']} (@{u['username']})\n"
        await q.edit_message_text(text)

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
    app.add_handler(CallbackQueryHandler(admin_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✝️ Orthodox Coptic Bot Running | Developed by Gerges Reda ✝️")
    app.run_polling()

if __name__ == "__main__":
    main()
