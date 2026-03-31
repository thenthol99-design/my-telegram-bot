import telebot
from telebot import types
import os
import psycopg2

API_TOKEN = os.getenv('API_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
# 👇 កន្លែងដែលអ្នកត្រូវដូរដាក់លេខ ID របស់អ្នក
ADMIN_ID = 5663812084 

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
    
# មុខងារ Database
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
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_admin = types.InlineKeyboardButton("📩 ឆាតទៅ Admin", url="https://t.me/your_admin_username") # ដាក់ Username របស់អ្នក
    btn1 = types.InlineKeyboardButton("💰 ចង់ដាក់ប្រាក់លេង (Target)", callback_data="target")
    btn2 = types.InlineKeyboardButton("🎁 សាកល្បងគណនី Free", callback_data="trial")
    markup.add(btn1, btn2)

    welcome_text = f"សួស្ដី {message.from_user.first_name}! សូមជ្រើសរើសជម្រើសរបស់អ្នក៖"
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_choice(call):
    user_id = call.from_user.id
    name = call.from_user.first_name
    category = "Target" if call.data == "target" else "Non-Target"
    
    # រក្សាទុកក្នុង Database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (chat_id, username, full_name, category) 
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (chat_id) DO UPDATE SET category = EXCLUDED.category;
    """, (user_id, call.from_user.username, name, category))
    conn.commit()
    cur.close()
    conn.close()

    # ផ្ញើដំណឹងទៅ Admin
    user_link = f"tg://user?id={user_id}"
    admin_text = (
        f"🔔 **មានអតិថិជនថ្មី!**\n\n"
        f"👤 ឈ្មោះ: {name}\n"
        f"🏷️ ប្រភេទ: {category}\n"
        f"🔗 ឆាតទៅវិញ: [ចុចទីនេះដើម្បីឆាត]({user_link})"
    )
    bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")

    bot.edit_message_text(f"អរគុណ {name}! អ្នកបានជ្រើសរើស: {category}\nក្រុមការងារនឹងទាក់ទងទៅអ្នក។", 
                          call.message.chat.id, call.message.message_id)

bot.infinity_polling()
