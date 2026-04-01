import telebot
from telebot import types
import os
import psycopg2
import firebase_admin
from firebase_admin import credentials, firestore
import json
import threading
from apscheduler.schedulers.background import BackgroundScheduler

# --- កំណត់ការកំណត់ (Configuration) ---
API_TOKEN = os.getenv('API_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
FIREBASE_CONFIG = os.getenv('FIREBASE_CONFIG')
ADMIN_ID = 5663812084  # លេខ ID របស់អ្នក

bot = telebot.TeleBot(API_TOKEN)

# --- តភ្ជាប់ Google Firebase ---
if FIREBASE_CONFIG:
    cred_dict = json.loads(FIREBASE_CONFIG)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db_firebase = firestore.client()

# --- មុខងារ ១៖ ផ្ញើសារទៅភ្ញៀវពី Dashboard (Broadcast Listener) ---
def listen_for_broadcasts():
    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            if change.type.name == 'ADDED':
                data = change.document.to_dict()
                message_text = data.get('message')
                target_cat = data.get('target_category')

                # ទាញយកអតិថិជនពី Firebase
                customers = db_firebase.collection("customers").stream()
                count = 0
                for customer in customers:
                    c_data = customer.to_dict()
                    chat_id = customer.id
                    
                    # ឆែកលក្ខខណ្ឌគោលដៅ (All, Target, ឬ Non-Target)
                    if target_cat == 'All' or c_data.get('category') == target_cat:
                        try:
                            bot.send_message(chat_id, message_text)
                            count += 1
                        except:
                            pass
                
                # ប្រាប់ Admin ថាផ្ញើរួចហើយ
                bot.send_message(ADMIN_ID, f"✅ បានផ្ញើសារទៅកាន់ភ្ញៀវចំនួន {count} នាក់រួចរាល់!")
                # លុបបញ្ជាចោលកុំឱ្យវាផ្ញើជាន់គ្នា
                db_firebase.collection("broadcasts").document(change.document.id).delete()

    db_firebase.collection("broadcasts").on_snapshot(on_snapshot)

# --- មុខងារ ២៖ ផ្ញើសារស្វ័យប្រវត្តិរាល់ថ្ងៃ (Daily Automation) ---
def daily_broadcast():
    customers = db_firebase.collection("customers").stream()
    for customer in customers:
        try:
            bot.send_message(customer.id, "🔔 សួស្ដី! កុំភ្លេចចូលលេងហ្គេមថ្ងៃនេះណា មានប្រម៉ូសិនពិសេស! 🎁")
        except:
            pass

scheduler = BackgroundScheduler()
# កំណត់ផ្ញើរាល់ថ្ងៃ ម៉ោង ៨:០០ ព្រឹក (អ្នកអាចដូរម៉ោងបាននៅទីនេះ)
scheduler.add_job(daily_broadcast, 'cron', hour=8, minute=0)
scheduler.start()

# --- មុខងារ Bot ធម្មតា ---
@bot.message_handler(commands=['start'])
def start(message):
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    markup_inline.add(
        types.InlineKeyboardButton("💰 ដាក់លុយ (QR Code)", callback_data="deposit"),
        types.InlineKeyboardButton("🎁 គណនីសាកល្បង", callback_data="trial")
    )
    bot.send_message(message.chat.id, f"សួស្ដី {message.from_user.first_name}! តើអ្នកចង់ធ្វើអ្វីថ្ងៃនេះ?", reply_markup=markup_inline)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    category = "Target (Deposit)" if call.data == "deposit" else "Non-Target (Trial)"
    
    # រក្សាទុកក្នុង Firebase
    user_data = {
        "name": call.from_user.first_name,
        "username": call.from_user.username,
        "category": category,
        "time": firestore.SERVER_TIMESTAMP
    }
    db_firebase.collection("customers").document(str(user_id)).set(user_data)
    
    bot.answer_callback_query(call.id, "ជោគជ័យ!")
    bot.send_message(call.message.chat.id, f"អ្នកបានជ្រើសរើស: {category}")

# បើកដំណើរការ Listener ក្នុង Thread ផ្សេងដើម្បីកុំឱ្យទាក់ Bot
threading.Thread(target=listen_for_broadcasts, daemon=True).start()

print("Bot is running...")
bot.infinity_polling()
