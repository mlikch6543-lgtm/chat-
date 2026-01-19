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
أنت أب كاهن قبطي أرثوذكسي حقيقي. 
تتحدث دائمًا بأسلوب هادئ، محب، ومؤثر روحياً.
تجيب على أي سؤال متعلق بالإيمان المسيحي الأرثوذكسي، الكتاب المقدس، الصلاة، الحياة الروحية، وتعاليم الكنيسة القبطية الأرثوذكسية.

طريقة الإجابة:
- مقدمة روحانية صغيرة تعطي طمأنينة
- آية أو مرجع كتابي
- شرح كنسي واضح، مرتب ومنظم
- نصيحة رعوية عملية

ممنوع رفض أي سؤال مسيحي أرثوذكسي.  
إذا كان السؤال خارج الإيمان الأرثوذكسي، ارفض بلطف مع رسالة محبة.

أسلوبك يشبه أب كاهن يرعى المؤمنين، ويعطي إجابات مليئة بالمحبة والإرشاد الروحي.
"""

# ================== MEMORY ==================
user_sessions = {}

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_sessions[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]

    intro_message = (
        "✝️ أهلاً بك يا ابنى / ابنتى الحبيب ✝️\n\n"
        "أنا هنا لأكون بمثابة أب روحي لك، لأجيب على أي سؤال يخص:\n"
        "• الإيمان المسيحي الأرثوذكسي\n"
        "• الكتاب المقدس\n"
        "• الصلاة والحياة الروحية\n"
        "• تعاليم الكنيسة القبطية الأرثوذكسية\n\n"
        "🌿 يمكنك أن تسأل بكل حرية، وسأجيبك بإجابات دقيقة، نموذجية، وأبويه.\n"
        "💛 البوت مصمم ليكون رفيقك الروحي، يوجهك بمحبة، ويقودك نحو النور.\n\n"
        "🛠️ تم تطوير هذا البوت بواسطة: جرجس رضا\n\n"
        "الآن، اتفضل ابدأ بسؤالك 🙏"
    )

    await update.message.reply_text(intro_message)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_sessions.pop(uid, None)
    await update.message.reply_text(
        "🔄 تم بدء محادثة جديدة.\nيمكنك الآن طرح أسئلتك مرة أخرى ✝️"
    )

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
            temperature=0.1  # منخفض لضمان دقة ووضوح
        )

        reply = response.choices[0].message.content
        user_sessions[uid].append({"role": "assistant", "content": reply})

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(
            "❌ حدث خطأ أثناء الرد، حاول مرة أخرى لاحقًا."
        )
        print(e)

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✝️ Orthodox Christian Bot (Fatherly Style) Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
