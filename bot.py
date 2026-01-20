import os
import openai
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

openai.api_key = OPENAI_API_KEY

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = """
أنت أب كاهن قبطي أرثوذكسي حقيقي.

التزم بما يلي بدقة:
- أجب فقط بحسب تعليم الكنيسة القبطية الأرثوذكسية.
- لا ترفض أي سؤال مسيحي أرثوذكسي صحيح.
- لو السؤال عددي (كم عدد – كم – عدد):
  • اذكر العدد بوضوح
  • عدّد النقاط 1، 2، 3...
  • اشرح كل نقطة باختصار واضح
- لو السؤال تعليمي أو روحي:
  • اشرح بأسلوب رعوي أبوي هادئ
- لو السؤال خارج الإيمان الأرثوذكسي:
  • اعتذر بلطف ووجّه للموضوع الصحيح

أسلوبك:
واضح – عميق – دقيق – بلا حشو – كأب اعتراف.
"""

# ================== STORAGE ==================
sessions = {}
users = set()

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    # إشعار أدمن بمستخدم جديد
    if uid not in users:
        users.add(uid)
        count = len(users)
        lang = user.language_code or "غير معروف"

        admin_text = (
            "🆕 مستخدم جديد للبوت\n\n"
            f"👤 الاسم: {user.full_name}\n"
            f"🆔 ID: {uid}\n"
            f"🌍 اللغة: {lang}\n"
            f"👥 عدد المستخدمين: {count}\n"
            f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)

    sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    intro = (
        "✝️ بسم الآب والابن والروح القدس، الإله الواحد، آمين ✝️\n\n"
        "أهلاً بك يا ابني الحبيب في هذا المكان الروحي،\n"
        "حيث نلتقي معًا في نور الإنجيل وتعليم الكنيسة القبطية الأرثوذكسية.\n\n"
        "أنا هنا لأخدمك كأب كاهن:\n"
        "• إجابة واضحة ودقيقة\n"
        "• شرح مرتب ومنظم\n"
        "• تعداد عند الأسئلة العددية\n"
        "• إرشاد روحي عملي للحياة\n\n"
        "هذا البوت يخدم الإيمان الأرثوذكسي فقط،\n"
        "وبروح المحبة والحق.\n\n"
        "🛠️ تم تطوير هذا البوت بواسطة: جرجس رضا\n\n"
        "تفضل واسأل بكل ثقة 🙏"
    )

    await update.message.reply_text(intro)

# ================== RESET ==================
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sessions.pop(update.effective_user.id, None)
    await update.message.reply_text("🔄 بدأت محادثة جديدة، تفضل بالسؤال ✝️")

# ================== CHAT ==================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if uid not in sessions:
        sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    sessions[uid].append({"role": "user", "content": text})

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=sessions[uid],
        temperature=0.15
    )

    reply = response.choices[0].message.content
    sessions[uid].append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply)

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✝️ Orthodox Father Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
