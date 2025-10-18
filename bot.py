import logging
import os  # <-- အသစ်ထည့်သည်
import PIL.Image # <-- အသစ်ထည့်သည်
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

# *** Model အဆင့်မြှင့်တင်ခြင်း ***
# 'gemini-pro' (text-only) အစား 'gemini-1.5-flash' (text + image) ကိုသုံးပါမည်။
# အကယ်၍ 1.5-flash က 404 error ပြန်ဖြစ်နေသေးရင် 'gemini-pro-vision' ကို ပြောင်းစမ်းကြည့်နိုင်ပါတယ်။
model = genai.GenerativeModel('gemini-1.5-flash')


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
        
        # Gemini AI (text-only input) ဆီကို မေးခွန်းပို့ခြင်း
        response = model.generate_content(user_text)
        
        # Gemini က ပြန်ဖြေတာကို user ဆီ ပြန်ပို့ခြင်း
        await update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Error processing text message: {e}")
        await update.message.reply_text("တောင်းပန်ပါတယ်။ စာသား message ကို လုပ်ဆောင်ရာမှာ အမှားအယွင်းတစ်ခု ဖြစ်သွားလို့ပါ။")

# -------------------------------------------------
# *** Function အသစ်: ပုံတွေ လက်ခံရရှိရင် အလုပ်လုပ်မည် ***
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

        # Gemini AI ကို ပုံနဲ့အတူ မေးခွန်းပါ တစ်ခါတည်းပို့မယ်
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

        # Gemini AI (multimodal input) ဆီကို ပုံနဲ့စာ ပို့ခြင်း
        response = model.generate_content(prompt_parts)
        
        # Gemini က ပြန်ဖြေတာကို user ဆီ ပြန်ပို့ခြင်း
        await update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await update.message.reply_text("တောင်းပန်ပါတယ်။ ပုံကို လုပ်ဆောင်ရာမှာ အမှားအယွင်းတစ်ခု ဖြစ်သွားလို့ပါ။")
    
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
    
    # *** Handler အသစ်: ပုံတွေ (Photo) ကို လက်ခံမယ့် handler ***
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Bot ကို စတင် run ခြင်း
    logger.info("Bot is starting polling... (Now supports text and photos!)")
    application.run_polling()

if __name__ == "__main__":
    main()
