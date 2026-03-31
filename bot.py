import telebot
from telebot import types
import os
import psycopg2

API_TOKEN = os.getenv('API_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
# លេខ ID របស់អ្នក (ត្រឹមត្រូវហើយ)
ADMIN_ID = 5663812084 

bot = telebot.TeleBot(API_TOKEN)

# លីងវេបសាយហ្គេមរបស់អ្នក
GAME_URL = "https://cfplay.online/login"

# មុខងារ Database
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
    except Exception as e:
        print(f"Database Error: {e}")

# រួមបញ្ចូល Handler /start តែមួយឱ្យពេញលេញ
@bot.message_handler(commands=['start'])
def start(message):
    init_db() # បង្កើតតារាងក្នុង DB ភ្លាមពេលមានអ្នកឆាតចូល
    
    # --- ១. បង្កើតប៊ូតុងធំនៅខាងក្រោម (Reply Keyboard) សម្រាប់បើកហ្គេម ---
    markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
    web_app = types.WebAppInfo(GAME_URL)
    btn_play = types.KeyboardButton("🎮 ចូលលេងហ្គេម (Mini App)", web_app=web_app)
    markup_reply.add(btn_play)

    # --- ២. បង្កើតប៊ូតុងជាប់សារ (Inline Keyboard) សម្រាប់ជម្រើសផ្សេងៗ ---
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    # !!! កុំភ្លេចដូរ your_admin_username ទៅជា Username តេឡេក្រាមរបស់អ្នក
    btn_admin = types.InlineKeyboardButton("📩 ឆាតទៅ Admin", url="https://t.me/Cockstn03TT") 
    btn1 = types.InlineKeyboardButton("💰 ចង់ដាក់ប្រាក់លេង (Target)", callback_data="target")
    btn2 = types.InlineKeyboardButton("🎁 សាកល្បងគណនី Free", callback_data="trial")
    markup_inline.add(btn_admin, btn1, btn2)

    welcome_text = (
        f"សួស្ដី {message.from_user.first_name}! 👋\n\n"
        "សូមស្វាគមន៍មកកាន់ប្រព័ន្ធហ្គេមអាជីព។\n"
        "សូមជ្រើសរើសជម្រើសខាងក្រោមដើម្បីចាប់ផ្ដើម៖"
    )
    
    # ផ្ញើសារចេញទៅ (ភ្ជាប់ជាមួយប៊ូតុងទាំង ២ ប្រភេទ)
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup_reply)
    bot.send_message(message.chat.id, "សូមជ្រើសរើសសេវាកម្មខាងក្រោម៖", reply_markup=markup_inline)

@bot.callback_query_handler(func=lambda call: True)
def handle_choice(call):
    user_id = call.from_user.id
    name = call.from_user.first_name
    category = "Target" if call.data == "target" else "Non-Target"
    
    # បញ្ឈប់សញ្ញាវិលៗលើប៊ូតុង
    bot.answer_callback_query(call.id)
    
    try:
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

        # ផ្ញើដំណឹងទៅ Admin (អ្នក)
        user_link = f"tg://user?id={user_id}"
        admin_text = (
            f"🔔 **មានអតិថិជនថ្មី!**\n\n"
            f"👤 ឈ្មោះ: {name}\n"
            f"🏷️ ប្រភេទ: {category}\n"
            f"🔗 ឆាតទៅវិញ: [ចុចទីនេះដើម្បីឆាត]({user_link})"
        )
        bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")

        # ប្រាប់អតិថិជនវិញ
        bot.edit_message_text(
            f"អរគុណ {name}! អ្នកបានជ្រើសរើស: {category}\nក្រុមការងារនឹងទាក់ទងទៅលោកអ្នកក្នុងពេលឆាប់ៗ។", 
            call.message.chat.id, 
            call.message.message_id
        )
    except Exception as e:
        print(f"Error in callback: {e}")

print("Bot is running...")
bot.infinity_polling()
