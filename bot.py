from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from PIL import Image, ImageDraw, ImageFont
import os
import random
import re

# توکن ربات تلگرام شما
TOKEN = "TOKEN_BOT"

# دایرکتوری ذخیره فونت‌ها
FONTS_DIR = "fonts/"
USER_FONTS_DIR = "user_fonts/"

# ایجاد پوشه‌های مورد نیاز اگر وجود ندارند
os.makedirs(FONTS_DIR, exist_ok=True)
os.makedirs(USER_FONTS_DIR, exist_ok=True)

# لیست فونت‌های پیش‌فرض
AVAILABLE_FONTS = {
    "Arial": "arial.ttf",
    "Times New Roman": "times.ttf",
    "Courier New": "cour.ttf",
}

# لیست رنگ‌ها
COLORS = {
    "قرمز": "#FF0000",
    "سبز": "#00FF00",
    "آبی": "#0000FF",
    "سفید": "#FFFFFF",
    "سیاه": "#000000",
}

# لیست سایزهای تصویر
IMAGE_SIZES = {
    "کوچک (400x200)": (400, 200),
    "متوسط (800x400)": (800, 400),
    "بزرگ (1200x600)": (1200, 600),
}

# لیست اندازه‌های فونت
FONT_SIZES = {
    "کوچک (20)": 20,
    "متوسط (40)": 40,
    "بزرگ (60)": 60,
}

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "✨ **به ربات تبدیل متن به تصویر خوش آمدید!** ✨\n\n"
        "متن خود را ارسال کنید تا آن را با فونت و رنگ‌های انتخابی به تصویر تبدیل کنم.\n\n"
        "⚠️ **نکته:** می‌توانید فونت دلخواه خود را هم ارسال کنید (فایل `.ttf`)."
    )

def ask_for_options(update: Update, context: CallbackContext):
    text = update.message.text
    context.user_data['text'] = text
    
    # اگر کاربر فایل فرستاد (فونت دلخواه)
    if update.message.document:
        file = update.message.document
        if file.file_name.endswith('.ttf'):
            file_id = file.file_id
            new_file = context.bot.get_file(file_id)
            file_path = os.path.join(USER_FONTS_DIR, file.file_name)
            new_file.download(file_path)
            
            context.user_data['custom_font'] = file.file_name
            update.message.reply_text(
                f"✅ فونت **{file.file_name}** با موفقیت ذخیره شد!\n"
                "لطفاً رنگ متن را انتخاب کنید:",
                reply_markup=get_color_keyboard("textcolor_")
            )
            return
        else:
            update.message.reply_text("⚠️ لطفاً فقط فایل فونت با پسوند `.ttf` ارسال کنید!")
            return
    
    # در غیر این صورت از او فونت را بپرس
    keyboard = [
        [InlineKeyboardButton(font, callback_data=f"font_{font}")] 
        for font in AVAILABLE_FONTS.keys()
    ]
    keyboard.append([InlineKeyboardButton("📤 فونت دلخواه من", callback_data="custom_font")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "لطفاً یک فونت انتخاب کنید یا فونت خود را آپلود نمایید:",
        reply_markup=reply_markup
    )

def ask_for_text_color(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data.startswith("font_"):
        font_name = query.data.split("_")[1]
        context.user_data['font'] = font_name
    elif query.data == "custom_font":
        query.edit_message_text("لطفاً فایل فونت (`.ttf`) را ارسال کنید:")
        return
    
    query.edit_message_text(
        f"فونت انتخاب شده: {context.user_data.get('font', 'فونت دلخواه')}\n"
        "لطفاً رنگ متن را انتخاب کنید:",
        reply_markup=get_color_keyboard("textcolor_")
    )

def ask_for_bg_color(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    text_color_name = query.data.split("_")[1]
    context.user_data['text_color'] = COLORS[text_color_name]
    
    query.edit_message_text(
        f"رنگ متن: {text_color_name}\n"
        "لطفاً رنگ پس‌زمینه را انتخاب کنید:",
        reply_markup=get_color_keyboard("bgcolor_")
    )

def ask_for_image_size(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    bg_color_name = query.data.split("_")[1]
    context.user_data['bg_color'] = COLORS[bg_color_name]
    
    keyboard = [
        [InlineKeyboardButton(size, callback_data=f"imgsize_{size}")] 
        for size in IMAGE_SIZES.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        f"رنگ پس‌زمینه: {bg_color_name}\n"
        "لطفاً سایز تصویر را انتخاب کنید:",
        reply_markup=reply_markup
    )

def ask_for_font_size(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    img_size_name = query.data.split("_")[1]
    context.user_data['image_size'] = IMAGE_SIZES[img_size_name]
    
    keyboard = [
        [InlineKeyboardButton(size, callback_data=f"fontsize_{size}")] 
        for size in FONT_SIZES.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        f"سایز تصویر: {img_size_name}\n"
        "لطفاً اندازه فونت را انتخاب کنید:",
        reply_markup=reply_markup
    )

def generate_image(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    font_size_name = query.data.split("_")[1]
    font_size = FONT_SIZES[font_size_name]
    context.user_data['font_size'] = font_size
    
    # دریافت اطلاعات از کاربر
    user_data = context.user_data
    text = user_data['text']
    text_color = user_data['text_color']
    bg_color = user_data['bg_color']
    image_width, image_height = user_data['image_size']
    
    # تعیین فونت (پیش‌فرض یا دلخواه کاربر)
    if 'custom_font' in user_data:
        font_path = os.path.join(USER_FONTS_DIR, user_data['custom_font'])
        font_name = user_data['custom_font']
    else:
        font_name = user_data['font']
        font_path = os.path.join(FONTS_DIR, AVAILABLE_FONTS[font_name])
    
    try:
        # ایجاد تصویر
        image = Image.new("RGB", (image_width, image_height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # بارگذاری فونت
        font = ImageFont.truetype(font_path, font_size)
        
        # محاسبه موقعیت متن (وسط تصویر)
        text_width, text_height = draw.textsize(text, font=font)
        x = (image_width - text_width) / 2
        y = (image_height - text_height) / 2
        
        # اضافه کردن متن به تصویر
        draw.text((x, y), text, fill=text_color, font=font)
        
        # ذخیره تصویر
        image_path = f"output_{random.randint(1, 10000)}.png"
        image.save(image_path)
        
        # ارسال تصویر به کاربر
        with open(image_path, 'rb') as photo:
            query.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=photo,
                caption=(
                    f"✅ تصویر شما آماده شد!\n\n"
                    f"📝 **متن:** {text}\n"
                    f"🔤 **فونت:** {font_name}\n"
                    f"🎨 **رنگ متن:** {text_color}\n"
                    f"🖌 **رنگ پس‌زمینه:** {bg_color}\n"
                    f"📏 **سایز تصویر:** {image_width}x{image_height}\n"
                    f"🔠 **اندازه فونت:** {font_size}"
                )
            )
        
        # حذف فایل موقت
        os.remove(image_path)
        
    except Exception as e:
        query.edit_message_text(f"❌ خطا در تولید تصویر: {str(e)}")

# تابع کمکی برای ساخت کیبورد رنگ‌ها
def get_color_keyboard(prefix):
    keyboard = [
        [InlineKeyboardButton(color, callback_data=f"{prefix}{color}")] 
        for color in COLORS.keys()
    ]
    return InlineKeyboardMarkup(keyboard)

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text | Filters.document, ask_for_options))
    dispatcher.add_handler(CallbackQueryHandler(ask_for_text_color, pattern="^font_"))
    dispatcher.add_handler(CallbackQueryHandler(ask_for_text_color, pattern="^custom_font"))
    dispatcher.add_handler(CallbackQueryHandler(ask_for_bg_color, pattern="^textcolor_"))
    dispatcher.add_handler(CallbackQueryHandler(ask_for_image_size, pattern="^bgcolor_"))
    dispatcher.add_handler(CallbackQueryHandler(ask_for_font_size, pattern="^imgsize_"))
    dispatcher.add_handler(CallbackQueryHandler(generate_image, pattern="^fontsize_"))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
