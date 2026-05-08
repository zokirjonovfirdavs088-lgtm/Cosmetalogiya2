import telebot
import os
from flask import Flask, request # Vercel uchun Flask qo'shildi
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

# --- SOZLAMALAR ---
TOKEN = os.getenv("TOKEN", "8493605038:AAGAUP6AKsR4GYECqocootjb6KBXCNlLTnQ")
ID = 276901319
bot = telebot.TeleBot(TOKEN, threaded=False)

# Flask ilovasi (Vercel talab qilgan 'app' obyekti)
app = Flask(__name__)

user_data = {}
owner_location = {}
days = {"mon": "Dushanba", "tue": "Seshanba", "wed": "Chorshanba", "thu": "Payshanba", "fri": "Juma"}
times = [f"{h}:00" for h in range(9, 18)]

# --- VERCEL WEBHOOK QISMI ---
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    # BU YERGA VERCEL-DAGI DOMENINGIZNI YOZING (masalan: https://vercel.app)
    # bot.set_webhook(url='https://SIZNING_DOMENINGIZ.vercel.app/' + TOKEN)
    return "Bot ishlamoqda...", 200

# --- SIZNING ASLIY KODINGIZ ---

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for key, day in days.items():
        keyboard.add(InlineKeyboardButton(text=day, callback_data=f"day_{key}"))
    bot.send_message(message.chat.id, "👋 Assalomu alaykum!\n📅 Iltimos, haftaning kunini tanlang:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("day_"))
def choose_day(call):
    day_name = days[call.data.split("_")[1]]
    user_data[call.from_user.id] = {"day": day_name}
    keyboard = InlineKeyboardMarkup(row_width=3)
    for t in times:
        keyboard.add(InlineKeyboardButton(text=t, callback_data=f"time_{t}"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                          text=f"📅 Kun: *{day_name}*\n⏰ Vaqtni tanlang:", reply_markup=keyboard, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def choose_time(call):
    time = call.data.split("_")[1]
    user_data[call.from_user.id]["time"] = time
    phone_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    phone_keyboard.add(KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True))
    bot.send_message(call.message.chat.id, f"⏰ Vaqt: *{time}*\n📞 Telefon raqamingizni yuboring:", 
                     reply_markup=phone_keyboard, parse_mode="Markdown")

@bot.message_handler(content_types=['location'])
def handle_location(message):
    if message.from_user.id == ID:
        owner_location["lat"] = message.location.latitude
        owner_location["lon"] = message.location.longitude
        bot.send_message(ID, "✅ Yangi lokatsiya saqlandi!")
    else:
        bot.send_message(message.chat.id, "Sizda bunday huquq yo'q.")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    user = message.from_user
    phone = message.contact.phone_number
    data = user_data.get(user.id, {})
    day = data.get("day", "Noma'lum")
    time = data.get("time", "Noma'lum")

    bot.send_message(ID, f"📥 *Yangi buyurtma!*\n\n👤 {user.first_name}\n📅 Kun: {day}\n⏰ Vaqt: {time}\n📞 {phone}", parse_mode="Markdown")
    bot.send_message(message.chat.id, "✅ Rahmat! Ma'lumotlar qabul qilindi.", reply_markup=telebot.types.ReplyKeyboardRemove())

    if "lat" in owner_location:
        bot.send_message(message.chat.id, "📍 Bizning manzil:")
        bot.send_location(message.chat.id, owner_location["lat"], owner_location["lon"])
    else:
        bot.send_message(message.chat.id, "📍 Manzil tez orada admin tomonidan yuboriladi.")
    user_data.pop(user.id, None)

# MUHIM: infinity_polling() olib tashlandi, o'rniga Flask ishlaydi
if __name__ == "__main__":
    app.run(debug=True)
