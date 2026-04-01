import telebot
from telebot import types
import os
import psycopg2

# --- កំណត់ការកំណត់ (Configuration) ---
API_TOKEN = os.getenv('API_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
ADMIN_ID = 5663812084  # ID របស់អ្នក

bot = telebot.TeleBot(API_TOKEN)
GAME_URL = "https://cfplay.online/login"

# --- មុខងារ Database ---
def init_db():
    try:
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
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database Error: {e}")

# --- បញ្ជា /start ---
@bot.message_handler(commands=['start'])
def start(message):
    init_db() # បង្កើតតារាង
    
    # ១. ប៊ូតុងធំខាងក្រោម (Reply Keyboard)
    markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
    web_app = types.WebAppInfo(GAME_URL)
    btn_play = types.KeyboardButton("🎮 ចូលលេងហ្គេម (Mini App)", web_app=web_app)
    markup_reply.add(btn_play)

    # ២. ប៊ូតុងជាប់សារ (Inline Keyboard)
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    btn_admin = types.InlineKeyboardButton("📩 ឆាតទៅ Admin", url="https://t.me/Cockstn03TT") 
    btn_deposit = types.InlineKeyboardButton("💰 ដាក់លុយ (QR Code)", callback_data="deposit")
    btn_trial = types.InlineKeyboardButton("🎁 គណនីសាកល្បង", callback_data="trial")
    markup_inline.add(btn_admin, btn_deposit, btn_trial)

    welcome_text = (
        f"សួស្ដី {message.from_user.first_name}! 👋\n\n"
        "សូមស្វាគមន៍មកកាន់ប្រព័ន្ធហ្គេមអាជីព។\n"
        "សូមជ្រើសរើសជម្រើសខាងក្រោមដើម្បីចាប់ផ្ដើម៖"
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup_reply)
    bot.send_message(message.chat.id, "សូមជ្រើសរើសសេវាកម្មខាងក្រោម៖", reply_markup=markup_inline)

# --- គ្រប់គ្រងការចុចប៊ូតុង (Callback Query) តែមួយគត់ ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    name = call.from_user.first_name
    username = call.from_user.username
    
    # ១. ករណីចុច "ដាក់លុយ"
    if call.data == "deposit":
        category = "Target (Deposit)"
        response_text = "🏦 សម្រាប់ការដាក់ប្រាក់តាម QR Code (ABA/Bakong):\n\nសូមផ្ញើសារទៅកាន់ Admin ដើម្បីទទួលរូបភាព QR ផ្លូវការ រួចផ្ញើវិក្កយបត្រមកវិញ។"
        
    # ២. ករណីចុច "គណនីសាកល្បង"
    elif call.data == "trial":
        category = "Non-Target (Trial)"
        response_text = "🎁 គណនីសាកល្បង (Demo Account):\n\nអ្នកអាចចូលទៅកាន់ហ្គេម រួចជ្រើសរើសយក 'Trial Mode'។\n\n*បញ្ជាក់៖ សម្រាប់ការបង្កើតគណនីពិត សូមទាក់ទង Admin។*"

    # រក្សាទុកទិន្នន័យទៅ Database
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (chat_id, username, full_name, category) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (chat_id) DO UPDATE SET category = EXCLUDED.category;
        """, (user_id, username, name, category))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Update Error: {e}")

    # ផ្ញើដំណឹងទៅ Admin (អ្នក)
    user_link = f"tg://user?id={user_id}"
    admin_text = (
        f"🔔 **មានអតិថិជនថ្មី!**\n\n"
        f"👤 ឈ្មោះ: {name}\n"
        f"🏷️ ប្រភេទ: {category}\n"
        f"🔗 ឆាតទៅវិញ: [ចុចទីនេះដើម្បីឆាត]({user_link})"
    )
    bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")

    # បង្ហាញសារទៅអតិថិជន
    bot.send_message(call.message.chat.id, response_text, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# --- ចាប់ផ្តើម Bot ---
print("Bot is running...")
bot.infinity_polling()
