import telebot
from telebot import types
import os
import firebase_admin
from firebase_admin import credentials, firestore
import json
import threading
import time
import random 
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

# --- បញ្ជីគណនីសាកល្បងទាំង ១០ ---
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

# --- [ថែមថ្មី] មុខងារចាំស្ដាប់ការឆ្លើយតបពី Admin លើ Dashboard ---
def listen_for_admin_replies():
    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            if change.type.name == 'ADDED':
                data = change.document.to_dict()
                chat_id = data.get('chat_id')
                text = data.get('text')
                try:
                    bot.send_message(chat_id, text)
                    # កត់ត្រាសារដែល Admin ផ្ញើចេញ ចូលក្នុង Chat History ដែរ
                    db_firebase.collection("chats").add({
                        "chat_id": str(chat_id),
                        "name": "Admin",
                        "text": text,
                        "sender": "admin",
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                except: pass
                db_firebase.collection("admin_replies").document(change.document.id).delete()
    db_firebase.collection("admin_replies").on_snapshot(on_snapshot)

def daily_broadcast():
    customers = db_firebase.collection("customers").stream()
    for customer in customers:
        try:
            bot.send_message(customer.id, "🔔 សួស្ដី! កុំភ្លេចចូលលេងហ្គេមថ្ងៃនេះណា! 🎁")
        except: pass

scheduler = BackgroundScheduler()
scheduler.add_job(daily_broadcast, 'cron', hour=8, minute=0)
scheduler.start()

# --- មុខងារ Start (ទម្រង់ចាស់របស់អ្នក) ---
@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_markup.add(types.KeyboardButton("🔲 ចូលលេង"))
    
    inline_markup = types.InlineKeyboardMarkup(row_width=2)
    btn_admin = types.InlineKeyboardButton("✉️ ឆាតទៅ Admin ↗️", url="https://t.me/Cockstn03TT")
    btn_deposit = types.InlineKeyboardButton("💰 ដាក់លុយ (QR Code)", callback_data="deposit")
    btn_trial = types.InlineKeyboardButton("🎁 គណនីសាកល្បង", callback_data="trial")
    inline_markup.row(btn_admin, btn_deposit)
    inline_markup.row(btn_trial)

    welcome_msg = f"សួស្ដី {user_name}! 👋\nសូមស្វាគមន៍មកកាន់ STN Play ផ្លូវការ!\n\n🕹 ហ្គេមអនឡាញដែលមានទំនុកចិត្តខ្ពស់!\n👉 ចុចប៊ូតុងខាងក្រោមដើម្បីចាប់ផ្តើម៖"
    bot.send_message(message.chat.id, welcome_msg, reply_markup=reply_markup)
    bot.send_message(message.chat.id, "សូមជ្រើសរើសសេវាកម្មខាងក្រោម៖", reply_markup=inline_markup)

# --- មុខងារ Query (ទម្រង់ចាស់របស់អ្នក) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name
    category = ""
    bot.answer_callback_query(call.id)

    if call.data == "deposit":
        category = "Target (Deposit)"
        reply_msg = f"🏦 សម្រាប់ការដាក់ប្រាក់តាម QR Code (ABA/Bakong):\n\nសូមផ្ញើសារទៅកាន់ Admin ដើម្បីទទួលរូបភាព QR ផ្លូវការ រួចផ្ញើវិក្កយបត្រមកវិញដើម្បីបញ្ចូលលុយ។\n\nអរគុណ {first_name}! អ្នកបានជ្រើសរើស: ដាក់លុយ\nក្រុមការងារនឹងទាក់ទងទៅលោកអ្នកក្នុងពេលឆាប់ៗ។"
        bot.send_message(call.message.chat.id, reply_msg)
    elif call.data == "trial":
        category = "Non-Target (Trial)"
        random_account = random.choice(TRIAL_ACCOUNTS)
        reply_msg = f"🎁 នេះគឺជាគណនីសាកល្បងរបស់អ្នក៖\n\n{random_account}\n\nសូមរីករាយក្នុងការកម្សាន្តលេងហ្គេម!"
        bot.send_message(call.message.chat.id, reply_msg)

    user_data = {"name": first_name, "username": call.from_user.username, "category": category, "time": firestore.SERVER_TIMESTAMP}
    db_firebase.collection("customers").document(str(user_id)).set(user_data)

    admin_msg = f"🔔 *អតិថិជនថ្មី!*\n\n👤 ឈ្មោះ: {first_name}\n📂 ប្រភេទ: {category}\n🆔 ID: `{user_id}`\n\n🔗 [🔗 ចុចទីនេះដើម្បីឆាតទៅភ្ញៀវ](tg://user?id={user_id})"
    try: bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    except: pass

@bot.message_handler(func=lambda message: message.text == "🔲 ចូលលេង")
def handle_play_button(message):
    bot.send_message(message.chat.id, "🌐 លីងចូលលេងហ្គេមផ្លូវការ: https://www.yourwebsite.com")

# --- [ថែមថ្មី] មុខងារកត់ត្រាគ្រប់សារដែលភ្ញៀវផ្ញើមក (Chat History) ---
@bot.message_handler(func=lambda message: True)
def log_and_reply(message):
    user_id = str(message.chat.id)
    text = message.text
    name = message.from_user.first_name

    # កត់ត្រាចូល Firebase ដើម្បីឱ្យ Dashboard មើលឃើញ
    db_firebase.collection("chats").add({
        "chat_id": user_id,
        "name": name,
        "text": text,
        "sender": "user",
        "timestamp": firestore.SERVER_TIMESTAMP
    })

# ចាប់ផ្ដើម Thread ទាំងអស់
threading.Thread(target=listen_for_broadcasts, daemon=True).start()
threading.Thread(target=listen_for_admin_replies, daemon=True).start()
bot.infinity_polling()
