import telebot
from telebot import types
import os
import firebase_admin
from firebase_admin import credentials, firestore
import json
import threading
import time
import random  # ថែមបណ្ណាល័យនេះដើម្បី Random គណនីសាកល្បង
from apscheduler.schedulers.background import BackgroundScheduler

# --- កំណត់ការកំណត់ ---
API_TOKEN = os.getenv('API_TOKEN')
FIREBASE_CONFIG = os.getenv('FIREBASE_CONFIG')
ADMIN_ID = 5663812084  

bot = telebot.TeleBot(API_TOKEN)

if FIREBASE_CONFIG:
    cred_dict = json.loads(FIREBASE_CONFIG)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db_firebase = firestore.client()

# --- បញ្ជីគណនីសាកល្បងទាំង ១០ (អ្នកអាចដូរ Username/Password ទីនេះបាន) ---
TRIAL_ACCOUNTS = [
    "👉 Username: test01 \n🔑 Password: aA123456()",
    "👉 Username: test02 \n🔑 Password: aA123456()",
    "👉 Username: test03 \n🔑 Password: aA123456()",
    "👉 Username: test04 \n🔑 Password: aA123456()",
    "👉 Username: test05 \n🔑 Password: aA123456()",
    "👉 Username: test06 \n🔑 Password: aA123456()",
    "👉 Username: test07 \n🔑 Password: aA123456()",
    "👉 Username: test08 \n🔑 Password: aA123456()",
    "👉 Username: test09 \n🔑 Password: aA123456()",
    "👉 Username: test10 \n🔑 Password: aA123456()"
]

# --- មុខងារផ្ញើសារបណ្ដាក់គ្នាម្ដងម្នាក់ៗ (Drip/Anti-Spam) ---
def process_staggered_broadcast(message_text, target_cat, media_url, media_type, delay_seconds):
    customers = db_firebase.collection("customers").stream()
    count = 0
    for customer in customers:
        c_data = customer.to_dict()
        chat_id = customer.id
        
        if target_cat == 'All' or c_data.get('category') == target_cat:
            try:
                if media_type == 'photo' and media_url:
                    bot.send_photo(chat_id, media_url, caption=message_text)
                elif media_type == 'video' and media_url:
                    bot.send_video(chat_id, media_url, caption=message_text)
                elif media_type == 'audio' and media_url:
                    bot.send_audio(chat_id, media_url, caption=message_text)
                else:
                    bot.send_message(chat_id, message_text)
                count += 1
                if delay_seconds > 0:
                    time.sleep(delay_seconds)
            except:
                pass
    bot.send_message(ADMIN_ID, f"✅ បានផ្ញើសារបណ្ដាក់គ្នាទៅភ្ញៀវ {count} នាក់រួចរាល់!")

def listen_for_broadcasts():
    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            if change.type.name == 'ADDED':
                data = change.document.to_dict()
                msg = data.get('message', '')
                cat = data.get('target_category', 'All')
                m_url = data.get('media_url', '')
                m_type = data.get('media_type', 'none')
                delay = int(data.get('delay_seconds', 0))

                threading.Thread(target=process_staggered_broadcast, args=(msg, cat, m_url, m_type, delay), daemon=True).start()
                db_firebase.collection("broadcasts").document(change.document.id).delete()
    db_firebase.collection("broadcasts").on_snapshot(on_snapshot)

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


# ==========================================
# ផ្នែកកែប្រែថ្មី (ចាប់ពីត្រង់នេះទៅក្រោម)
# ==========================================

@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    
    # ១. បង្កើត Menu ខាងក្រោម (Reply Keyboard)
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_play = types.KeyboardButton("🔲 ចូលលេង")
    reply_markup.add(btn_play)
    
    # ២. បង្កើតប៊ូតុងជាប់សារ (Inline Keyboard)
    inline_markup = types.InlineKeyboardMarkup(row_width=2)
    
    # ⚠️ កុំភ្លេចដូរ YOUR_ADMIN_USERNAME ទៅជា Username របស់ Admin ផ្ទាល់ ឧ. STN_Admin
    btn_admin = types.InlineKeyboardButton("✉️ ឆាតទៅ Admin ↗️", url="https://t.me/Cockstn03TT")
    btn_deposit = types.InlineKeyboardButton("💰 ដាក់លុយ (QR Code)", callback_data="deposit")
    btn_trial = types.InlineKeyboardButton("🎁 គណនីសាកល្បង", callback_data="trial")
    
    # រៀបចំប៊ូតុង (ឆាត និង ដាក់លុយ នៅជួរទី១), (សាកល្បង នៅជួរទី២ លាតពេញ)
    inline_markup.row(btn_admin, btn_deposit)
    inline_markup.row(btn_trial)

    # ៣. ផ្ញើសារស្វាគមន៍
    welcome_msg = f"សួស្ដី {user_name}! 👋\nសូមស្វាគមន៍មកកាន់ STN Play ផ្លូវការ!\n\n🕹 ហ្គេមអនឡាញដែលមានទំនុកចិត្តខ្ពស់!\n👉 ចុចប៊ូតុងខាងក្រោមដើម្បីចាប់ផ្តើម៖"
    
    bot.send_message(message.chat.id, welcome_msg, reply_markup=reply_markup)
    bot.send_message(message.chat.id, "សូមជ្រើសរើសសេវាកម្មខាងក្រោម៖", reply_markup=inline_markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name
    category = ""
    
    bot.answer_callback_query(call.id) # បិទសញ្ញាវិលៗពេលចុចប៊ូតុង
    
    # បើភ្ញៀវចុច "ដាក់លុយ"
    if call.data == "deposit":
        category = "Target (Deposit)"
        reply_msg = f"🏦 សម្រាប់ការដាក់ប្រាក់តាម QR Code (ABA/Bakong):\n\nសូមផ្ញើសារទៅកាន់ Admin ដើម្បីទទួលរូបភាព QR ផ្លូវការ រួចផ្ញើវិក្កយបត្រមកវិញដើម្បីបញ្ចូលលុយ។\n\nអរគុណ {first_name}! អ្នកបានជ្រើសរើស: ដាក់លុយ\nក្រុមការងារនឹងទាក់ទងទៅលោកអ្នកក្នុងពេលឆាប់ៗ។"
        bot.send_message(call.message.chat.id, reply_msg)
        
    # បើភ្ញៀវចុច "គណនីសាកល្បង"
    elif call.data == "trial":
        category = "Non-Target (Trial)"
        # ចាប់យកគណនី ១ ក្នុងចំណោម ១០ មកផ្ញើឱ្យភ្ញៀវ
        random_account = random.choice(TRIAL_ACCOUNTS)
        reply_msg = f"🎁 នេះគឺជាគណនីសាកល្បងរបស់អ្នក៖\n\n{random_account}\n\nសូមរីករាយក្នុងការកម្សាន្តលេងហ្គេម!"
        bot.send_message(call.message.chat.id, reply_msg)

    # រក្សាទុកទិន្នន័យចូល Firebase ដូចធម្មតា
    user_data = {
        "name": first_name,
        "username": call.from_user.username,
        "category": category,
        "time": firestore.SERVER_TIMESTAMP
    }
    db_firebase.collection("customers").document(str(user_id)).set(user_data)

# មុខងារពេលចុចប៊ូតុង "ចូលលេង" ខាងក្រោម
@bot.message_handler(func=lambda message: message.text == "🔲 ចូលលេង")
def handle_play_button(message):
    bot.send_message(message.chat.id, "🌐 លីងចូលលេងហ្គេមផ្លូវការ: https://www.yourwebsite.com")

threading.Thread(target=listen_for_broadcasts, daemon=True).start()
bot.infinity_polling()
