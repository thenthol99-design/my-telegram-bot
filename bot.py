import telebot
from telebot import types
import os
import firebase_admin
from firebase_admin import credentials, firestore
import json
import threading
import time  # បន្ថែមសម្រាប់ការពន្យារពេល
from apscheduler.schedulers.background import BackgroundScheduler

# --- កំណត់ការកំណត់ ---
API_TOKEN = os.getenv('API_TOKEN')
FIREBASE_CONFIG = os.getenv('FIREBASE_CONFIG')
ADMIN_ID = 5663812084  # លេខ ID របស់អ្នក

bot = telebot.TeleBot(API_TOKEN)

# --- តភ្ជាប់ Google Firebase ---
if FIREBASE_CONFIG:
    cred_dict = json.loads(FIREBASE_CONFIG)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db_firebase = firestore.client()

# --- មុខងារផ្ញើសារបណ្ដាក់គ្នាម្ដងម្នាក់ៗ (Drip/Anti-Spam) ---
def process_staggered_broadcast(message_text, target_cat, media_url, media_type, delay_seconds):
    customers = db_firebase.collection("customers").stream()
    count = 0
    for customer in customers:
        c_data = customer.to_dict()
        chat_id = customer.id
        
        if target_cat == 'All' or c_data.get('category') == target_cat:
            try:
                # ផ្ញើតាមប្រភេទ Media
                if media_type == 'photo' and media_url:
                    bot.send_photo(chat_id, media_url, caption=message_text)
                elif media_type == 'video' and media_url:
                    bot.send_video(chat_id, media_url, caption=message_text)
                elif media_type == 'audio' and media_url:
                    bot.send_audio(chat_id, media_url, caption=message_text)
                else:
                    bot.send_message(chat_id, message_text)
                
                count += 1
                # បើមានកំណត់វិនាទី ឱ្យវាសម្រាកសិនមុននឹងផ្ញើទៅម្នាក់ទៀត
                if delay_seconds > 0:
                    time.sleep(delay_seconds)
            except:
                pass
    
    bot.send_message(ADMIN_ID, f"✅ បានផ្ញើសារបណ្ដាក់គ្នាទៅភ្ញៀវ {count} នាក់រួចរាល់!")

# --- មុខងារ Listen ពី Dashboard ---
def listen_for_broadcasts():
    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            if change.type.name == 'ADDED':
                data = change.document.to_dict()
                msg = data.get('message', '')
                cat = data.get('target_category', 'All')
                m_url = data.get('media_url', '')
                m_type = data.get('media_type', 'none')
                delay = int(data.get('delay_seconds', 0)) # ទទួលវិនាទីពី Dashboard

                # បង្កើត Thread ថ្មីដើម្បីផ្ញើសារបណ្ដាក់គ្នា
                threading.Thread(target=process_staggered_broadcast, args=(msg, cat, m_url, m_type, delay), daemon=True).start()
                
                # លុបបញ្ជាចេញពី Firebase
                db_firebase.collection("broadcasts").document(change.document.id).delete()

    db_firebase.collection("broadcasts").on_snapshot(on_snapshot)

# --- មុខងារផ្ញើសារស្វ័យប្រវត្តិរាល់ព្រឹក ---
def daily_broadcast():
    customers = db_firebase.collection("customers").stream()
    for customer in customers:
        try:
            bot.send_message(customer.id, "🔔 សួស្ដី! កុំភ្លេចចូលលេងហ្គេមថ្ងៃនេះណា! 🎁")
        except:
            pass

scheduler = BackgroundScheduler()
scheduler.add_job(daily_broadcast, 'cron', hour=8, minute=0)
scheduler.start()

# --- មុខងារ Bot Start ---
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
    user_data = {
        "name": call.from_user.first_name,
        "username": call.from_user.username,
        "category": category,
        "time": firestore.SERVER_TIMESTAMP
    }
    db_firebase.collection("customers").document(str(user_id)).set(user_data)
    bot.answer_callback_query(call.id, "ជោគជ័យ!")
    bot.send_message(call.message.chat.id, f"អ្នកបានជ្រើសរើស: {category}")

# ចាប់ផ្ដើម Listener
threading.Thread(target=listen_for_broadcasts, daemon=True).start()
bot.infinity_polling()
