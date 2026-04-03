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
import urllib.request
from io import BytesIO
 
# --- កំណត់ការកំណត់ ---
API_TOKEN = os.getenv('API_TOKEN')
FIREBASE_CONFIG = os.getenv('FIREBASE_CONFIG')
ADMIN_ID = 5663812084  

bot = telebot.TeleBot(API_TOKEN)

# --- តភ្ជាប់ Google Firebase ---
if FIREBASE_CONFIG:
    config_data = json.loads(FIREBASE_CONFIG)
    cred = credentials.Certificate(config_data)
    
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'my-telegram-bot-46df4.firebasestorage.app'
    })
    
    db_firebase = firestore.client()
    bucket = firebase_storage.bucket()

# --- បញ្ជីគណនីសាកល្បង ---
TRIAL_ACCOUNTS = [
    "👉 Username: cfrmlltt001 \n🔑 Password: 123456",
    "👉 Username: cfrmlltt002 \n🔑 Password: 123457",
    "👉 Username: cfrmlltt003 \n🔑 Password: 123458",
    "👉 Username: cfrmlltt004 \n🔑 Password: 123459",
    "👉 Username: cfrmlltt005 \n🔑 Password: 1234510",
    "👉 Username: cfrmlltt006 \n🔑 Password: 1234511",
    "👉 Username: cfrmlltt007 \n🔑 Password: 1234512",
    "👉 Username: cfrmlltt008 \n🔑 Password: 1234513",
    "👉 Username: cfrmlltt009 \n🔑 Password: 1234514",
    "👉 Username: cfrmlltt010 \n🔑 Password: 1234515"
]

# --- មុខងារ Upload Media ---
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

# --- មុខងារផ្ញើសារបណ្ដាក់គ្នា ---
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
                elif (media_type == 'voice' or media_type == 'audio') and media_url: 
                    bot.send_voice(chat_id, media_url, caption=message_text)
                else: 
                    bot.send_message(chat_id, message_text)
                
                count += 1
                if delay_seconds > 0: time.sleep(delay_seconds)
            except: pass
    bot.send_message(ADMIN_ID, f"✅ ការផ្ញើបណ្ដាក់គ្នាទៅភ្ញៀវ {count} នាក់ ចប់សព្វគ្រប់!")

# --- មុខងារ Listen សម្រាប់ Admin ---
# --- មុខងារ Listen សម្រាប់ Admin ---
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
                    if m_type == 'photo' and m_url: 
                        bot.send_photo(chat_id, m_url, caption=text)
                    elif m_type == 'video' and m_url: 
                        bot.send_video(chat_id, m_url, caption=text)
                    elif (m_type == 'voice' or m_type == 'audio') and m_url:
                        # ១. ទាញយកឯកសារសំឡេងពី Firebase URL មកកាន់ Memory
                        req = urllib.request.Request(m_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req) as response:
                            voice_data = response.read()
                            
                        # ២. បង្កើតជា File និម្មិត និងដាក់កន្ទុយ .ogg ដើម្បីឱ្យ Telegram ស្គាល់ជា Voice
                        voice_file = BytesIO(voice_data)
                        voice_file.name = "voice.ogg" 
                        
                        # ៣. ផ្ញើទៅកាន់អតិថិជន
                        bot.send_voice(chat_id, voice_file, caption=text)
                        
                    elif text: 
                        bot.send_message(chat_id, text)
                except Exception as e: 
                    print(f"Error sending reply: {e}")
                    
                db_firebase.collection("admin_replies").document(change.document.id).delete()
    db_firebase.collection("admin_replies").on_snapshot(on_snapshot)

# ==========================================
# មុខងារ Start (មានទាំងប៊ូតុងខាងក្រោម និងប៊ូតុងជាប់សារ)
# ==========================================

@bot.message_handler(commands=['clear'])
def clear_keyboard(message):
    remove_board = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "🧹 បានបោសសម្អាតប៊ូតុងចេញរៀបរយហើយ!", reply_markup=remove_board)

# --- មុខងារទាញរូបប្រូហ្វាលភ្ញៀវ ---
def get_user_profile_photo(user_id):
    try:
        photos = bot.get_user_profile_photos(user_id)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id # រូបចុងក្រោយគេ (ច្បាស់ជាងគេ)
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Upload ទៅ Firebase Storage
            file_name = f"profile_photos/{user_id}.jpg"
            blob = bucket.blob(file_name)
            blob.upload_from_string(downloaded_file, content_type="image/jpeg")
            blob.make_public()
            return blob.public_url
    except Exception as e:
        print(f"Error getting profile photo: {e}")
    return None

# --- មុខងារ Start ពេញលេញ (ទាញរូប + បង្ហាញប៊ូតុង) ---
@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = str(message.chat.id)
        user_name = message.from_user.first_name
        username = message.from_user.username
        
        # ១. ទាញរូបប្រូហ្វាល និងរក្សាទុកទិន្នន័យទៅ Firebase
        profile_url = get_user_profile_photo(message.from_user.id)
        
        db_firebase.collection("customers").document(user_id).set({
            "name": user_name,
            "username": username,
            "profile_url": profile_url, # លីងរូបភាពភ្ញៀវ
            "category": "New Customer",
            "time": firestore.SERVER_TIMESTAMP
        }, merge=True)

        # ២. បង្កើតផ្ទាំងប៊ូតុងខាងក្រោម (Reply Keyboard)
        reply_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn_deposit_reply = types.KeyboardButton("💰 ដាក់លុយ")
        btn_admin_reply = types.KeyboardButton("✉️ ឆាតទៅ Admin")
        btn_trial_reply = types.KeyboardButton("🎁 គណនីសាកល្បង")
        reply_keyboard.add(btn_deposit_reply, btn_admin_reply)
        reply_keyboard.add(btn_trial_reply)

        # ៣. បង្កើតប៊ូតុងជាប់សារ (Inline Keyboard)
        inline_markup = types.InlineKeyboardMarkup(row_width=2)
        btn_admin_inline = types.InlineKeyboardButton("✉️ ឆាតទៅ Admin ↗️", url="https://t.me/Cockstn03TT")
        btn_deposit_inline = types.InlineKeyboardButton("💰 ដាក់លុយ (QR Code)", callback_data="deposit")
        btn_trial_inline = types.InlineKeyboardButton("🎁 គណនីសាកល្បង", callback_data="trial")
        inline_markup.row(btn_admin_inline, btn_deposit_inline)
        inline_markup.row(btn_trial_inline)

        # ៤. ផ្ញើសារស្វាគមន៍ (បង្ហាញប៊ូតុងខាងក្រោម)
        bot.send_message(
            message.chat.id, 
            f"សួស្ដី {user_name}! 👋\nសូមស្វាគមន៍មកកាន់ STN Play!", 
            reply_markup=reply_keyboard
        )

        # ៥. ផ្ញើសារជ្រើសរើសសេវាកម្ម (បង្ហាញប៊ូតុងជាប់សារ)
        bot.send_message(
            message.chat.id, 
            "សូមជ្រើសរើសសេវាកម្ម៖", 
            reply_markup=inline_markup
        )
        
    except Exception as e:
        print(f"Error in start command: {e}")
# --- មុខងារចាប់ពាក្យពេលភ្ញៀវចុច "ប៊ូតុងជាប់សារ" (Inline Buttons) ---
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
    bot.send_message(ADMIN_ID, f"🔔 *អតិថិជនថ្មី (ចុចប៊ូតុងជាប់សារ)!*\nឈ្មោះ: {first_name}\nប្រភេទ: {category}\n🔗 [ឆាត](tg://user?id={user_id})", parse_mode="Markdown")

# --- មុខងារចាប់ពាក្យពេលភ្ញៀវចុច "ប៊ូតុងខាងក្រោម" (Reply Buttons) ---
@bot.message_handler(func=lambda message: message.text in ["💰 ដាក់លុយ", "✉️ ឆាតទៅ Admin", "🎁 គណនីសាកល្បង"])
def handle_bottom_buttons(message):
    user_id = str(message.chat.id)
    first_name = message.from_user.first_name
    text = message.text

    if text == "✉️ ឆាតទៅ Admin":
        bot.send_message(message.chat.id, "✉️ សូមទាក់ទងមកកាន់ Admin តាមរយៈលីងនេះ៖\n👉 @Cockstn03TT")
        return # មិនបាច់ Save ចូល Database ទេសម្រាប់អ្នកគ្រាន់តែសួរ

    category = "Target (Deposit)" if text == "💰 ដាក់លុយ" else "Non-Target (Trial)"

    if text == "💰 ដាក់លុយ":
        bot.send_message(message.chat.id, "🏦 សូមផ្ញើសារទៅ Admin ដើម្បីទទួល QR Code ផ្លូវការ។")
    elif text == "🎁 គណនីសាកល្បង":
        bot.send_message(message.chat.id, f"🎁 គណនីសាកល្បង៖\n{random.choice(TRIAL_ACCOUNTS)}")

    db_firebase.collection("customers").document(user_id).set({
        "name": first_name, "username": message.from_user.username, "category": category, "time": firestore.SERVER_TIMESTAMP
    })
    bot.send_message(ADMIN_ID, f"🔔 *អតិថិជនចុចប៊ូតុងខាងក្រោម!*\nឈ្មោះ: {first_name}\nសេវាកម្ម: {text}\n🔗 [ឆាត](tg://user?id={user_id})", parse_mode="Markdown")

# --- មុខងារកត់ត្រាសារចូល Dashboard ---
@bot.message_handler(content_types=['text', 'photo', 'video', 'voice'])
def log_messages(message):
    if message.text in ["💰 ដាក់លុយ", "✉️ ឆាតទៅ Admin", "🎁 គណនីសាកល្បង"]:
        return

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

print("🤖 Bot is running...")
bot.infinity_polling()
