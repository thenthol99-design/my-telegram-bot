import telebot
from telebot import types
import os
import firebase_admin
from firebase_admin import credentials, firestore, storage as firebase_storage
import json
import threading
import time
import random
import uuid
from apscheduler.schedulers.background import BackgroundScheduler

# --- កំណត់ការកំណត់ ---
API_TOKEN = os.getenv('API_TOKEN')
FIREBASE_CONFIG = os.getenv('FIREBASE_CONFIG')
ADMIN_ID = 5663812084  

bot = telebot.TeleBot(API_TOKEN)

# --- តភ្ជាប់ Google Firebase ---
if FIREBASE_CONFIG:
    config_data = json.loads(FIREBASE_CONFIG)
    cred = credentials.Certificate(config_data)
    
    # កូដថ្មីសម្រាប់ភ្ជាប់ Storage Bucket (ដើម្បីឱ្យមើលឃើញរូបភាព/វីដេអូ)
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'my-telegram-bot-46df4.firebasestorage.app'
    })
    
    db_firebase = firestore.client()
    bucket = firebase_storage.bucket()

# --- បញ្ជីគណនីសាកល្បង ---
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

# --- មុខងារ Upload Media ពី Telegram ទៅ Firebase Storage ---
def upload_telegram_file(message, file_type):
    try:
        if file_type == 'photo': file_id = message.photo[-1].file_id
        elif file_type == 'video': file_id = message.video.file_id
        elif file_type == 'voice': file_id = message.voice.file_id
        else: return None, "none"

        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        ext = 'jpg' if file_type == 'photo' else 'mp4' if file_type == 'video' else 'ogg'
        file_name = f"chat_media/{uuid.uuid4()}.{ext}"
        blob = bucket.blob(file_name)
        
        content_type = "image/jpeg" if file_type == 'photo' else "video/mp4" if file_type == 'video' else "audio/ogg"
        blob.upload_from_string(downloaded_file, content_type=content_type)
        blob.make_public()
        return blob.public_url, file_type
    except Exception as e:
        print(f"Upload Error: {e}")
        return None, "none"

# --- មុខងារផ្ញើសារបណ្ដាក់គ្នា (Anti-Spam) ---
def process_staggered_broadcast(message_text, target_cat, media_url, media_type, delay_seconds):
    customers = db_firebase.collection("customers").stream()
    count = 0
    for customer in customers:
        c_data = customer.to_dict()
        chat_id = customer.id
        if target_cat == 'All' or c_data.get('category') == target_cat:
            try:
                if media_type == 'photo' and media_url: bot.send_photo(chat_id, media_url, caption=message_text)
                elif media_type == 'video' and media_url: bot.send_video(chat_id, media_url, caption=message_text)
                else: bot.send_message(chat_id, message_text)
                count += 1
                if delay_seconds > 0: time.sleep(delay_seconds)
            except: pass
    bot.send_message(ADMIN_ID, f"✅ ការផ្ញើបណ្ដាក់គ្នាទៅភ្ញៀវ {count} នាក់ ចប់សព្វគ្រប់!")

# --- មុខងារ Listen សម្រាប់ Admin ឆ្លើយតបពី Dashboard ---
def listen_for_admin_replies():
    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            if change.type.name == 'ADDED':
                data = change.document.to_dict()
                chat_id = data.get('chat_id')
                text = data.get('text', '')
                m_url = data.get('media_url', '')
                m_type = data.get('media_type', 'none')

                try:
                    if m_type == 'photo' and m_url: bot.send_photo(chat_id, m_url, caption=text)
                    elif m_type == 'video' and m_url: bot.send_video(chat_id, m_url, caption=text)
                    elif text: bot.send_message(chat_id, text)
                except: pass
                db_firebase.collection("admin_replies").document(change.document.id).delete()
    db_firebase.collection("admin_replies").on_snapshot(on_snapshot)

# --- មុខងារ Start & Callback ---
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

    bot.send_message(message.chat.id, f"សួស្ដី {user_name}! 👋\nសូមស្វាគមន៍មកកាន់ STN Play!", reply_markup=reply_markup)
    bot.send_message(message.chat.id, "សូមជ្រើសរើសសេវាកម្ម៖", reply_markup=inline_markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = str(call.from_user.id)
    first_name = call.from_user.first_name
    category = "Target (Deposit)" if call.data == "deposit" else "Non-Target (Trial)"
    
    bot.answer_callback_query(call.id)
    if call.data == "deposit":
        bot.send_message(call.message.chat.id, "🏦 សូមផ្ញើសារទៅ Admin ដើម្បីទទួល QR Code ផ្លូវការ។")
    elif call.data == "trial":
        bot.send_message(call.message.chat.id, f"🎁 គណនីសាកល្បង៖\n{random.choice(TRIAL_ACCOUNTS)}")

    db_firebase.collection("customers").document(user_id).set({
        "name": first_name, "username": call.from_user.username, "category": category, "time": firestore.SERVER_TIMESTAMP
    })
    bot.send_message(ADMIN_ID, f"🔔 *អតិថិជនថ្មី!*\nឈ្មោះ: {first_name}\nប្រភេទ: {category}\n🔗 [ឆាត](tg://user?id={user_id})", parse_mode="Markdown")

# --- មុខងារកត់ត្រាគ្រប់សារ (Text, Photo, Video, Voice) ទៅ Dashboard ---
@bot.message_handler(content_types=['text', 'photo', 'video', 'voice'])
def log_messages(message):
    user_id = str(message.chat.id)
    name = message.from_user.first_name
    text = message.text or message.caption or ""
    m_url, m_type = None, "none"

    if message.content_type in ['photo', 'video', 'voice']:
        m_url, m_type = upload_telegram_file(message, message.content_type)

    db_firebase.collection("chats").add({
        "chat_id": user_id, "name": name, "text": text,
        "media_url": m_url, "media_type": m_type,
        "sender": "user", "timestamp": firestore.SERVER_TIMESTAMP
    })

# --- បើក Listener ទាំងអស់ ---
def listen_broadcasts():
    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            if change.type.name == 'ADDED':
                d = change.document.to_dict()
                threading.Thread(target=process_staggered_broadcast, args=(d.get('message',''), d.get('target_category','All'), d.get('media_url',''), d.get('media_type','none'), int(d.get('delay_seconds',0))), daemon=True).start()
                db_firebase.collection("broadcasts").document(change.document.id).delete()
    db_firebase.collection("broadcasts").on_snapshot(on_snapshot)

threading.Thread(target=listen_broadcasts, daemon=True).start()
threading.Thread(target=listen_for_admin_replies, daemon=True).start()
bot.infinity_polling()
