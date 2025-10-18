import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging (Error တွေကို ကြည့်ဖို့)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- သင့် BOT TOKEN ကို ဒီမှာထည့်ပါ ---
TELEGRAM_TOKEN = "8256277265:AAGkyWGaeNtSOKV678v7ixJkoNZKUMvq44A" 
# -----------------------------------

TRACE_MOE_API_URL = "https://api.trace.moe/search"

# /start command ကို ဖြေကြားမယ့် function
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User က /start လို့ရိုက်ထည့်ရင် message ပို့မယ်။"""
    user = update.effective_user
    await update.message.reply_html(
        f"မင်္ဂလာပါ {user.mention_html()}! 👋\n\n"
        f"ကျွန်တော်က ပုံထဲက Anime ကာရိုက်တာတွေကို ရှာပေးနိုင်ပါတယ်။ \n"
        f"ကျွန်တော့်ကို ပုံတစ်ပုံ ပို့ပေးကြည့်ပါ။"
    )

# ပုံ လက်ခံရရှိရင် အလုပ်လုပ်မယ့် function
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User ပို့လိုက်တဲ့ ပုံကို လက်ခံပြီး trace.moe API ကိုပို့မယ်။"""
    
    # User ကို "ရှာနေတယ်" လို့ အရင် အကြောင်းပြန်ထားမယ်
    await update.message.reply_text("ပုံကို လက်ခံရရှိပါတယ်။ ခဏလေးစောင့်ပြီး ရှာဖွေပေးပါမယ်...")

    try:
        # ပို့လိုက်တဲ့ ပုံတွေထဲက resolution အများဆုံးပုံကို ယူမယ်
        photo_file = await update.message.photo[-1].get_file()
        
        # ပုံကို download လုပ်ပြီး memory ထဲမှာ byte array အနေနဲ့ သိမ်းထားမယ်
        file_bytes = await photo_file.download_as_bytearray()
        
        # trace.moe API ကို ပုံ ပို့ပြီး ရှာခိုင်းမယ်
        response = requests.post(TRACE_MOE_API_URL, files={"image": file_bytes})
        
        # HTTP error (4xx, 5xx) တွေရှိမရှိ စစ်ဆေးမယ်
        response.raise_for_status() 
        
        data = response.json()
        
        # API ကနေ အဖြေပြန်ရပြီး ရလဒ်ရှိ၊ မရှိ စစ်ဆေးမယ်
        if data['result'] and len(data['result']) > 0:
            # တူညီမှု အများဆုံး ရလဒ် (ပထမဆုံးတစ်ခု) ကို ယူမယ်
            result = data['result'][0]
            
            # Anilist ကနေ အချက်အလက်တွေ ယူမယ်
            title_romaji = result['anilist']['title']['romaji']
            title_native = result['anilist']['title']['native']
            similarity = result['similarity'] * 100 # % အနေနဲ့ပြမယ်
            episode = result['episode']
            
            # အဖြေကို စာသားအနေနဲ့ ပြင်ဆင်မယ်
            reply_text = (
                f"ရှာတွေ့ပါပြီ! 🎉\n\n"
                f"<b>Anime (Romaji):</b> {title_romaji}\n"
                f"<b>Anime (Native):</b> {title_native}\n"
                f"<b>Episode:</b> {episode}\n"
                f"<b>တူညီမှု (Similarity):</b> {similarity:.2f}%\n"
            )
        else:
            reply_text = "တောင်းပန်ပါတယ်။ ဒီပုံနဲ့ ကိုက်ညီတဲ့ ရလဒ်ကို ရှာမတွေ့ပါဘူး။ 😥"
            
    except requests.RequestException as e:
        logger.error(f"API Error: {e}")
        reply_text = "API ကို ခေါ်ဆိုရာမှာ အမှားအယွင်း ဖြစ်သွားပါတယ်။ ခဏနေမှ ထပ်ကြိုးစားကြည့်ပါ။"
    except Exception as e:
        logger.error(f"Unknown Error: {e}")
        reply_text = f"တစ်ခုခု အမှားအယွင်း ဖြစ်သွားပါတယ်: {e}"

    # User ကို အဖြေ ပြန်ပို့မယ်
    await update.message.reply_text(reply_text, parse_mode='HTML')

def main() -> None:
    """Bot ကို စတင် run မယ်။"""
    # Application ကို တည်ဆောက်မယ်
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Command တွေကို မှတ်ပုံတင်မယ်
    application.add_handler(CommandHandler("start", start))

    # ပုံတွေ (Photo) ကို လက်ခံရရှိရင် handle_image function ကို ခေါ်ခိုင်းမယ်
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Bot ကို စတင် run မယ် (Telegram ကနေ update တွေကို စောင့်နားထောင်မယ်)
    print("Bot is running... (Press Ctrl+C to stop)")
    application.run_polling()

if __name__ == "__main__":
    main()
