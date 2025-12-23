import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = '8341745520:AAEOUih-Ro1GHEMmRvqgmlZT6y4Z_9m1YrA'
SHEET_NAME = "VictoryGroup_Records"
JSON_KEYFILE = "credentials.json"

# --- GOOGLE SHEETS CONNECTION ---
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

# --- VALIDATION LOGIC ---
def parse_format(text):
    """Checks if the message matches the required Chinese format."""
    required_keys = [
        "客户姓名", "客户地区", "平台", "客户WS", "P1 编号", "P2 编号", "部门名字"
    ]
    extracted_data = {}
    lines = text.strip().split('\n')
    
    for line in lines:
        if '-' in line:
            parts = line.split('-', 1)
            key = parts[0].strip()
            val = parts[1].strip()
            extracted_data[key] = val

    # Verify all keys exist and are not empty
    errors = [key for key in required_keys if not extracted_data.get(key)]
    return extracted_data, errors

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Victory Group Bot is online. Please send information in the correct format.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user = update.message.from_user
    msg_id = update.message.message_id
    
    data, missing_fields = parse_format(user_text)

    # Trigger if staff puts wrong information
    if missing_fields:
        error_msg = "❌ **Invalid Information!**\n\nThe following fields are missing or empty:\n"
        error_msg += "\n".join([f"- {field}" for field in missing_fields])
        error_msg += "\n\nPlease resend with the correct format."
        await update.message.reply_text(error_msg, parse_mode='Markdown')
        return

    # If valid, save to Google Sheet
    try:
        sheet = get_sheet()
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user.full_name,
            data.get("客户姓名"),
            data.get("客户地区"),
            data.get("平台"),
            data.get("客户WS"),
            data.get("P1 编号"),
            data.get("P2 编号"),
            data.get("部门名字"),
            str(msg_id) # Store message ID to find it later for deletion
        ]
        sheet.append_row(row)

        # Create Delete Button (Only for the user who sent it)
        keyboard = [[InlineKeyboardButton("🗑️ Delete This Record", callback_data=f"del_{user.id}_{msg_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("✅ Data saved to Google Sheets successfully!", reply_markup=reply_markup)

    except Exception as e:
        logging.error(f"Sheet Error: {e}")
        await update.message.reply_text(f"⚠️ Google Sheets Error: {e}")

async def delete_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Data format: del_UserID_MsgID
    _, original_user_id, msg_id = query.data.split('_')

    # Security check: Only the person who posted can delete
    if str(query.from_user.id) != original_user_id:
        await context.bot.send_message(
            chat_id=query.message.chat_id, 
            text=f"🚫 @{query.from_user.username}, you cannot delete someone else's record!"
        )
        return

    # Delete from Sheet
    try:
        sheet = get_sheet()
        cell = sheet.find(str(msg_id), in_column=10) # Search in the MsgID column
        if cell:
            sheet.delete_rows(cell.row)
            await query.edit_message_text("🗑️ Record has been deleted from the database.")
        else:
            await query.edit_message_text("⚠️ Record not found (it might have been deleted already).")
    except Exception as e:
        await query.edit_message_text(f"❌ Delete failed: {e}")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(delete_button_handler))

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
