import telebot
from telebot import types
import os
import psycopg2
import firebase_admin
from firebase_admin import credentials, firestore
import json

# --- កំណត់ការកំណត់ (Configuration) ---
API_TOKEN = os.getenv('API_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
ADMIN_ID = 5663812084 
FIREBASE_CONFIG = os.getenv('FIREBASE_CONFIG')

bot = telebot.TeleBot(API_TOKEN)
GAME_URL = "https://cfplay.online/login"

# --- តភ្ជាប់ Google Firebase ---
if FIREBASE_CONFIG:
    cred_dict = json.loads(FIREBASE_CONFIG)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db_firebase = firestore.client()

# --- មុខងារ Database PostgreSQL (សម្រាប់ Bot ប្រើ) ---
def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id BIGINT PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            category TEXT DEFAULT 'Unknown',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    init_db()
    markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup_reply.add(types.KeyboardButton("🎮 ចូលលេងហ្គេម (Mini App)", web_app=types.WebAppInfo(GAME_URL)))

    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    markup_inline.add(
        types.InlineKeyboardButton("📩 ឆាតទៅ Admin", url="https://t.me/Cockstn03TT"),
        types.InlineKeyboardButton("💰 ដាក់លុយ (QR Code)", callback_data="deposit"),
        types.InlineKeyboardButton("🎁 គណនីសាកល្បង", callback_data="trial")
    )
    bot.send_message(message.chat.id, f"សួស្ដី {message.from_user.first_name}! សូមជ្រើសរើសសេវាកម្ម៖", reply_markup=markup_reply)
    bot.send_message(message.chat.id, "ជម្រើសបន្ថែម៖", reply_markup=markup_inline)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    name = call.from_user.first_name
    category = "Target (Deposit)" if call.data == "deposit" else "Non-Target (Trial)"
    
    # ១. រក្សាទុកក្នុង PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("INSERT INTO users (chat_id, username, full_name, category) VALUES (%s, %s, %s, %s) ON CONFLICT (chat_id) DO UPDATE SET category = EXCLUDED.category;", (user_id, call.from_user.username, name, category))
    conn.commit()
    cur.close()
    conn.close()

    # ២. ផ្ញើទៅ Google Firebase (សម្រាប់បង្ហាញលើ Dashboard វេបសាយ)
    user_data = {
        "name": name,
        "username": call.from_user.username,
        "category": category,
        "time": firestore.SERVER_TIMESTAMP
    }
    db_firebase.collection("customers").document(str(user_id)).set(user_data)

    # ផ្ញើដំណឹងទៅ Admin
    bot.send_message(ADMIN_ID, f"🔔 **អតិថិជនថ្មី!**\nឈ្មោះ: {name}\nប្រភេទ: {category}\n🔗 [ចុចឆាត](tg://user?id={user_id})", parse_mode="Markdown")
    
    bot.answer_callback_query(call.id, "ទិន្នន័យបានរក្សាទុកក្នុង Dashboard!")
    bot.send_message(call.message.chat.id, f"អរគុណ {name}! អ្នកបានជ្រើសរើស: {category}")

bot.infinity_polling()
