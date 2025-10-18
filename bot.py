import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- ဒီနေရာတွေမှာ သင့် Key တွေကို အစားထိုးပါ ---
TELEGRAM_TOKEN = "8256277265:AAGkyWGaeNtSOKV678v7ixJkoNZKUMvq44A"  # @BotFather က ရတဲ့ Token
GEMINI_API_KEY = "AIzaSyBS4l0RUNfromJXWAWE1x6-R2oxNEHeqgw"    # Google AI Studio က ရတဲ့ Key
# ----------------------------------------------

# Gemini API ကို Configure လုပ်ခြင်း
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash') # 'gemini-pro' သို့မဟုတ် 'gemini-1.5-flash' သုံးနိုင်
    chat = model.start_chat(history=[]) # Conversation history အတွက်
    logging.info("Gemini AI Model ကို အောင်မြင်စွာ စတင်လိုက်ပါပြီ။")
except Exception as e:
    logging.error(f"Gemini API ကို စတင်ရာတွင် ပြဿနာဖြစ်နေပါသည်: {e}")
    exit() # API Key မှားနေရင် ဆက်မလုပ်တော့ဘူး

# Log တွေပြဖို့အတွက် Logging ကို setup လုပ်ခြင်း
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# /start command အတွက် function
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User က /start လို့ရိုက်လိုက်ရင် ဒီစာကိုပို့မယ်။"""
    user_name = update.effective_user.first_name
    await update.message.reply_html(
        f"မင်္ဂလာပါ {user_name}။\n\nကျွန်တော်က Gemini AI နဲ့ ချိတ်ဆက်ထားတဲ့ Bot ပါ။"
        f" သင်မေးချင်တာရှိရင် မေးနိုင်ပါတယ်။"
    )


# /clear command အတွက် (chat history ရှင်းဖို့)
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Chat history ကို ရှင်းလင်းပေးမယ်။"""
    global chat
    chat = model.start_chat(history=[]) # chat object အသစ်ပြန်ဆောက်
    await update.message.reply_text("စကားပြောမှတ်တမ်း (Chat History) ကို ရှင်းလင်းပြီးပါပြီ။")


# စာပို့လိုက်တိုင်း အလုပ်လုပ်မယ့် function
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User ပို့လိုက်တဲ့ စာကို Gemini AI ဆီပို့ပြီး အဖြေပြန်တောင်းမယ်။"""
    user_text = update.message.text
    chat_id = update.message.chat_id

    try:
        # "Typing..." ဆိုပြီး user ကိုပြထားမယ်
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # Gemini AI ဆီကို စာပို့ပြီး အဖြေတောင်းမယ်
        response = chat.send_message(user_text)
        
        # Gemini ကပြန်လာတဲ့ အဖြေကို User ဆီပြန်ပို့မယ်
        await update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Gemini AI မှ အဖြေတောင်းရာတွင် Error ဖြစ်ပါသည်: {e}")
        await update.message.reply_text("တောင်းပန်ပါတယ်။ အခုချိန်မှာ အဖြေပေးလို့မရသေးပါဘူး။")


def main() -> None:
    """Bot ကို စတင် Run မယ်။"""
    # Application ကို Token နဲ့ တည်ဆောက်မယ်
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Command တွေကို သတ်မှတ်မယ်
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear))

    # စာပို့တာတွေကို လက်ခံဖို့ MessageHandler ကို သတ်မှတ်မယ်
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Bot ကို စတင်မေးမြန်းမှုတွေ လက်ခံဖို့ (Polling) စတင်မယ်
    logger.info("Bot is starting...")
    application.run_polling()


if __name__ == "__main__":
    main()
