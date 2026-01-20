import os
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

أسلوبك:
- أبوي، هادئ، عميق، ومليء بالمحبة
- إجاباتك دقيقة، نموذجية، ومبنية على تعليم الكنيسة القبطية الأرثوذكسية

قواعد مهمة جدًا:
1) لو السؤال فيه (كم – عدد – أول – ثاني – ترتيب – من هو):
   - ابدأ الإجابة مباشرة بتحديد العدد أو الاسم بوضوح
   - مثال:
     "الإجابة: القديس إستفانوس"
     ثم أكمل الشرح الروحي طبيعي

2) لو السؤال يتطلب تعداد:
   - استخدم ترقيم واضح (1، 2، 3…)

3) أجب فقط على الأسئلة المسيحية الأرثوذكسية
4) أي سؤال خارج الإيمان الأرثوذكسي → اعتذار لطيف ومحبة

دائمًا:
- آية كتابية إن أمكن
- شرح كنسي
- نصيحة رعوية
"""

# ================== STORAGE ==================
users_db = {}
sessions = {}

# ================== HELPERS ==================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    # تسجيل المستخدم
    if uid not in users_db:
        users_db[uid] = {
            "name": user.full_name,
            "username": user.username,
            "language": user.language_code,
        }

        # إشعار للأدمن
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🆕 مستخدم جديد دخل البوت\n\n"
                f"👤 الاسم: {user.full_name}\n"
                f"🔗 username: @{user.username}\n"
                f"🌍 اللغة: {user.language_code}\n"
                f"📊 العدد الكلي: {len(users_db)}"
            ),
        )

    sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    intro = (
        "✝️ بسم الآب والابن والروح القدس ✝️\n\n"
        "أهلاً بك يا ابني الحبيب في هذا الموضع الروحي.\n\n"
        "أنا هنا لأكون معك كأب كاهن:\n"
        "• أجيب عن أسئلتك الإيمانية\n"
        "• أشرح الكتاب المقدس\n"
        "• أرافقك في حياتك الروحية\n\n"
        "🛠️ تطوير: جرجس رضا\n\n"
        "اتفضل اسأل بكل حرية 🙏"
    )

    await update.message.reply_text(intro)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sessions.pop(update.effective_user.id, None)
    await update.message.reply_text("🔄 تم بدء محادثة جديدة ✝️")

# ================== ADMIN ==================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    await update.message.reply_text(
        f"📊 عدد مستخدمي البوت: {len(users_db)}"
    )

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
    text = update.message.text

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
        await update.message.reply_text(
            "❌ حدث خطأ، حاول مرة أخرى لاحقًا"
        )

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))

    # Admin
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✝️ Orthodox Father Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
