import telebot
import os

API_TOKEN = os.getenv('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "សួស្ដី! Bot នេះកំពុងដើរលើ Railway ២៤ ម៉ោង។")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

print("Bot is running...")
bot.infinity_polling()
