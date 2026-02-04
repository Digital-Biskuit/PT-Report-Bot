from telegram.ext import Updater, MessageHandler, Filters, CommandHandler

# --- CONFIGURATION ---
# Replace with your actual Bot Token from @BotFather
TOKEN = '8341745520:AAEPcNTWEIASN_y5lOwhdeQfbYSUKNsFR7s'


# --- HANDLERS ---

def start(update, context):
    """Answers the /start command"""
    update.message.reply_text("Hello! The bot is ALIVE and running on your PC. 🤖")


def handle_message(update, context):
    """This will run whenever you send a normal text message"""
    user_text = update.message.text

    # Simple logic to show it's working
    if "hello" in user_text.lower():
        update.message.reply_text("Hi there! I can hear you loud and clear.")
    else:
        update.message.reply_text("I received your message: " + user_text)


# --- MAIN ENGINE ---

def main():
    # Updater is the 'engine' for version 13.15
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("Bot is starting... checking for messages...")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()