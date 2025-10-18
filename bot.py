import logging
import os
import PIL.Image
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# --- ဒီနေရာတွေမှာ သင့် Key တွေကို အစားထိုးထည့်ပါ ---
TELEGRAM_TOKEN = "8256277265:AAGkyWGaeNtSOKV678v7ixJkoNZKUMvq44A"
GEMINI_API_KEY = "AIzaSyBS4l0RUNfromJXWAWE1x6-R2oxNEHeqgw"
# ----------------------------------------------------

# Logging (Error တွေကြည့်ဖို့)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Gemini AI ကို Configure လုပ်ခြင်း
genai.configure(api_key=GEMINI_API_KEY)

# *** Error Fix: Model (၂) မျိုး ခွဲသတ်မှတ်ခြင်း ***
# 404 error ရှင်းရန် 'gemini-1.5-flash' ကို မသုံးတော့ပါ။
try:
    text_model = genai.GenerativeModel('gemini-pro')
    vision_model = genai.GenerativeModel('gemini-pro-vision')
    logger.info("Gemini Models ('gemini-pro' and 'gemini-pro-vision') loaded successfully.")
except Exception as e:
    logger.critical(f"Failed to load Gemini models: {e}")
    # Models တွေမရရင် bot ကို ဆက် run လို့ အဓိပ္ပါယ်မရှိတော့ပါဘူး။
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
        # User ကို bot က စာရိုက်နေကြောင်း "Typing..." ပြသခြင်း
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # *** Fix: စာသားအတွက် 'text_model' (gemini-pro) ကို အသုံးပြုပါမည် ***
        response = text_model.generate_content(user_text)
        
        # Gemini က ပြန်ဖြေတာကို user ဆီ ပြန်ပို့ခြင်း
        await update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Error processing text message: {e}")
        await update.message.reply_text("တောင်းပန်ပါတယ်။ စာသား message ကို လုပ်ဆောင်ရာမှာ အမှားအယွင်းတစ်ခု ဖြစ်သွားလို့ပါ။")

# -------------------------------------------------
# ပုံတွေ လက်ခံရရှိရင် အလုပ်လုပ်မယ့် function
# -------------------------------------------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    logger.info(f"User (ChatID: {chat_id}) sent a photo.")
    
    # ယာယီသိမ်းမယ့် ပုံ file path
    temp_file_path = f"temp_image_{chat_id}.jpg"

    try:
        # User ကို "Uploading photo..." action ပြသခြင်း
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

        # Telegram က ပို့လာတဲ့ ပုံတွေထဲက resolution အများဆုံးပုံကို ယူမယ်
        photo_file = await update.message.photo[-1].get_file()
        
        # အဲ့ဒီပုံကို server (bot run နေတဲ့နေရာ) ပေါ်ကို ယာယီ download ဆွဲချမယ်
        await photo_file.download_to_drive(temp_file_path)

        logger.info(f"Photo downloaded to {temp_file_path}")

        # PIL (Pillow) library ကိုသုံးပြီး ပုံကိုဖွင့်မယ်
        img = PIL.Image.open(temp_file_path)

        # User က ပုံနဲ့အတူ စာ (caption) ရေးပို့ရင် အဲ့ဒီစာကိုပါ ထည့်မေးမယ်
        user_caption = update.message.caption
        
        prompt_parts = [
            img, # ပုံကို အရင်ထည့်
        ]

        if user_caption:
            # User က caption ထည့်ရေးထားရင် (ဥပမာ - "ဒီလူဘယ်သူလဲ")
            prompt_parts.append(f"User က မေးခွန်းမေးထားပါတယ်: '{user_caption}'")
        else:
            # Caption မပါရင်၊ default မေးခွန်းအနေနဲ့ ပုံထဲက ကာရိုက်တာ/လူ ကိုမေးမယ်
            prompt_parts.append("ဒီပုံထဲမှာရှိတဲ့ ကာရိုက်တာ (သို့) လူပုဂ္ဂိုလ်ရဲ့ နာမည်ကို အတိအကျ ပြောပြပါ။ သူတို့ဟာ ဘယ်ကလာသလဲ (ဥပမာ- ရုပ်ရှင်၊ anime၊ ဂိမ်း) ဆိုတာပါ ရှင်းပြပါ။")

        # *** Fix: ပုံတွေအတွက် 'vision_model' (gemini-pro-vision) ကို အသုံးပြုပါမည် ***
        response = vision_model.generate_content(prompt_parts)
        
        # Gemini က ပြန်ဖြေတာကို user ဆီ ပြန်ပို့ခြင်း
        await update.message.reply_text(response.text)

    except Exception as e:
        # Error အစစ်အမှန်ကို log မှာ အသေးစိတ် ပြခိုင်းခြင်း
        logger.error(f"Error processing photo: {e}", exc_info=True)
        await update.message.reply_text("တောင်းပန်ပါတယ်။ ပုံကို လုပ်ဆောင်ရာမှာ အမှားအယွင်းတစ်ခု ဖြစ်သွားလို့ပါ။ (Error log ကို စစ်ဆေးပါ)")
    
    finally:
        # ယာယီ download ဆွဲထားတဲ့ ပုံ file ကို ပြန်ဖျက်ခြင်း
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"Cleaned up {temp_file_path}")


def main() -> None:
    # Bot ကို စတင်ခြင်း
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commands တွေကို သတ်မှတ်ခြင်း
    application.add_handler(CommandHandler("start", start))
    
    # သာမန်စာသား message တွေကို လက်ခံမယ့် handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # ပုံတွေ (Photo) ကို လက်ခံမယ့် handler
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Bot ကို စတင် run ခြင်း
    logger.info("Bot is starting polling... (Using gemini-pro for text and gemini-pro-vision for photos)")
    application.run_polling()

if __name__ == "__main__":
    main()
