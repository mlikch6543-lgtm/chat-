import os
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("Missing environment variables")

openai.api_key = OPENAI_API_KEY

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = """
أنت أب كاهن قبطي أرثوذكسي.
تجيب فقط على الأسئلة الخاصة بالإيمان المسيحي الأرثوذكسي.

طريقة الإجابة:
- إجابة واضحة ومنظمة
- لغة بسيطة ومفهومة
- تعليم كنسي سليم
- لمسة رعوية أبوية

مصادرك:
- الكتاب المقدس
- تعليم الكنيسة القبطية الأرثوذكسية
- الفهم الكنسي العام للآباء

ممنوع تمامًا:
- المقارنة بين الأديان
- الفلسفة
- العلم التجريبي
- السياسة
- أي عقيدة غير أرثوذكسية

لو السؤال خارج الإيمان الأرثوذكسي:
ارفض الإجابة بمحبة ووضوح،
وقل إننا نركز على التعليم الأرثوذكسي وخلاص النفس.
"""

# ================== MEMORY ==================
user_sessions = {}

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_sessions[update.effective_user.id] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    await update.message.reply_text(
        "✝️ أهلاً بيك\n\n"
        "أنا بوت كنسي مسيحي قبطي أرثوذكسي.\n\n"
        "مهمتي أجاوب على أي سؤال يخص:\n"
        "• الإيمان المسيحي الأرثوذكسي\n"
        "• الكتاب المقدس\n"
        "• التعليم الكنسي\n"
        "• الحياة الروحية\n\n"
        "الإجابات بتكون:\n"
        "✔️ واضحة\n"
        "✔️ مرتبة\n"
        "✔️ حسب تعليم الكنيسة\n\n"
        "❗ أي سؤال خارج الإيمان الأرثوذكسي لن يتم الرد عليه.\n\n"
        "🛠️ تم تطويري بواسطة: جرجس رضا\n\n"
        "اتفضل اسأل بكل بساطة 🙏"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_sessions.pop(update.effective_user.id, None)
    await update.message.reply_text("🔄 تم بدء محادثة جديدة.\nاتفضل اسأل ✝️")

# ================== CHAT ==================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if uid not in user_sessions:
        user_sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    user_sessions[uid].append({"role": "user", "content": text})

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=user_sessions[uid],
            temperature=0.2
        )

        reply = response.choices[0].message.content
        user_sessions[uid].append({"role": "assistant", "content": reply})

        await update.message.reply_text(reply)

    except Exception:
        await update.message.reply_text(
            "يا حبيبي، السؤال ده خارج نطاق التعليم الأرثوذكسي.\n"
            "خلّينا نركّز على الإيمان وخلاص النفس ✝️"
        )

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✝️ Orthodox Christian Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
