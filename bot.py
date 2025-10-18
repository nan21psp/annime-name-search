import logging
import os
import PIL.Image
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# --- ဒီနေရာတွေမှာ သင့် Key တွေကို အစားထိုးထည့်ပါ ---
TELEGRAM_TOKEN = "8256277265:AAGkyWGaeNtSOKV678v7ixJkoNZKUMvq44A"
GEMINI_API_KEY = "AIzaSyD8XsDShWpSB64QwIBHlds48TqOaOyNeiI"
# ----------------------------------------------------

# Logging (Error တွေကြည့်ဖို့)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Gemini AI ကို Configure လုပ်ခြင်း
genai.configure(api_key=GEMINI_API_KEY)

# *** Error Fix: Model နာမည်တွေကို full path ('models/...') နဲ့ ပြောင်းသုံးပါမည် ***
try:
    text_model = genai.GenerativeModel('models/gemini-pro')
    vision_model = genai.GenerativeModel('models/gemini-pro-vision')
    logger.info("Gemini Models ('models/gemini-pro' and 'models/gemini-pro-vision') loaded successfully.")
except Exception as e:
    logger.critical(f"Failed to load Gemini models: {e}")
    exit()


# /start command အတွက် function
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("မင်္ဂလာပါ! ကျွန်တော်က Gemini AI bot ပါ။ မေးခွန်းတွေမေးနိုင်သလို၊ ပုံပို့ပြီး ဒါဘယ်သူလဲလို့လည်း မေးနိုင်ပါပြီ။")

# စာသား message တွေကို လက်ခံရရှိရင် အလုပ်လုပ်မယ့် function
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    logger.info(f"User (ChatID: {chat_id}) sent text: {user_text}")

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # 'text_model' (models/gemini-pro) ကို အသုံးပြုပါမည်
        response = text_model.generate_content(user_text)
        
        await update.message.reply_text(response.text)

    except Exception as e:
        # Error အစစ်အမှန်ကို log မှာ အသေးစိတ် ပြခိုင်းခြင်း
        logger.error(f"Error processing text message: {e}", exc_info=True)
        await update.message.reply_text("တောင်းပန်ပါတယ်။ စာသား message ကို လုပ်ဆောင်ရာမှာ အမှားအယွင်းတစ်ခု ဖြစ်သွားလို့ပါ။")

# -------------------------------------------------
# ပုံတွေ လက်ခံရရှိရင် အလုပ်လုပ်မယ့် function
# -------------------------------------------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    logger.info(f"User (ChatID: {chat_id}) sent a photo.")
    
    temp_file_path = f"temp_image_{chat_id}.jpg"

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(temp_file_path)

        logger.info(f"Photo downloaded to {temp_file_path}")

        img = PIL.Image.open(temp_file_path)

        user_caption = update.message.caption
        
        prompt_parts = [
            img, 
        ]

        if user_caption:
            prompt_parts.append(f"User က မေးခွန်းမေးထားပါတယ်: '{user_caption}'")
        else:
            prompt_parts.append("ဒီပုံထဲမှာရှိတဲ့ ကာရိုက်တာ (သို့) လူပုဂ္ဂိုလ်ရဲ့ နာမည်ကို အတိအကျ ပြောပြပါ။ သူတို့ဟာ ဘယ်ကလာသလဲ (ဥပမာ- ရုပ်ရှင်၊ anime၊ ဂိမ်း) ဆိုတာပါ ရှင်းပြပါ။")

        # 'vision_model' (models/gemini-pro-vision) ကို အသုံးပြုပါမည်
        response = vision_model.generate_content(prompt_parts)
        
        await update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Error processing photo: {e}", exc_info=True)
        await update.message.reply_text("တောင်းပန်ပါတယ်။ ပုံကို လုပ်ဆောင်ရာမှာ အမှားအယွင်းတစ်ခု ဖြစ်သွားလို့ပါ။ (Error log ကို စစ်ဆေးပါ)")
    
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"Cleaned up {temp_file_path}")


def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("Bot is starting polling... (Using full model paths)")
    application.run_polling()

if __name__ == "__main__":
    main()
