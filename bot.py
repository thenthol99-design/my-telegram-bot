import telebot
from telebot import types
import os

# ទាញយក Token ពី Railway
API_TOKEN = os.getenv('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# លីងវេបសាយហ្គេមរបស់អ្នក
GAME_URL = "https://cfplay.online/login"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # ១. បង្កើតប៊ូតុងធំនៅខាងក្រោម (Reply Keyboard) ដើម្បីបើកហ្គេម
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    web_app = types.WebAppInfo(GAME_URL)
    btn_play = types.KeyboardButton("🎮 ចូលលេងហ្គេម (Mini App)", web_app=web_app)
    markup.add(btn_play)

    # ២. បង្កើតប៊ូតុងជាប់សារ (Inline Keyboard) សម្រាប់ Admin និងការដាក់លុយ
    inline_markup = types.InlineKeyboardMarkup(row_width=2)
    btn_admin = types.InlineKeyboardButton("📩 ឆាតទៅ Admin", url="https://t.me/your_admin_username") # ដាក់ Username របស់អ្នក
    btn_deposit = types.InlineKeyboardButton("💰 ដាក់លុយ (QR Code)", callback_data="deposit")
    btn_trial = types.InlineKeyboardButton("🎁 គណនីសាកល្បង", callback_data="trial")
    inline_markup.add(btn_admin, btn_deposit, btn_trial)

    welcome_text = (
        f"សួស្ដី {message.from_user.first_name}! 👋\n"
        "សូមស្វាគមន៍មកកាន់ AGCF Play ផ្លូវការ។\n\n"
        "🕹 ហ្គេមអនឡាញដែលមានទំនុកចិត្តខ្ពស់!\n"
        "👉 ចុចប៊ូតុងខាងក្រោមដើម្បីចាប់ផ្ដើម៖"
    )
    
    # ផ្ញើសារស្វាគមន៍ជាមួយប៊ូតុង
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    bot.send_message(message.chat.id, "សូមជ្រើសរើសសេវាកម្មខាងក្រោម៖", reply_markup=inline_markup)

# កូដសម្រាប់ឆ្លើយតបពេលចុចប៊ូតុង Deposit ឬ Trial
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "deposit":
        text = "🏦 សម្រាប់ការដាក់ប្រាក់តាម QR Code (ABA/Bakong):\n\nសូមផ្ញើសារទៅកាន់ Admin ដើម្បីទទួលរូបភាព QR ផ្លូវការ រួចផ្ញើវិក្កយបត្រមកវិញដើម្បីបញ្ចូលលុយ។"
        bot.send_message(call.message.chat.id, text)
    elif call.data == "trial":
        text = "🎁 គណនីសាកល្បង (Demo Account):\n\nអ្នកអាចចូលទៅកាន់ហ្គេម រួចជ្រើសរើសយក 'Trial Mode' ឬប្រើ User: guest / Pass: 123456 (ឧទាហរណ៍)។\n\n*បញ្ជាក់៖ សម្រាប់ការបង្កើតគណនីពិត សូមទាក់ទង Admin។*"
        bot.send_message(call.message.chat.id, text)
    bot.answer_callback_query(call.id)

bot.infinity_polling()
