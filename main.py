import logging
import gspread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from datetime import datetime

# --- CONFIGURATION ---
# IMPORTANT: Replace this with your NEW token from @BotFather
TOKEN = 'YOUR_NEW_TELEGRAM_BOT_TOKEN' 
SHEET_NAME = "Dinglong Part Timer Bot"
JSON_KEYFILE = "credentials.json"

# --- GOOGLE SHEETS CONNECTION ---
def get_sheet():
    try:
        # Modern way to connect using gspread
        client = gspread.service_account(filename=JSON_KEYFILE)
        return client.open(SHEET_NAME).sheet1
    except Exception as e:
        print(f"Failed to connect to Google Sheets: {e}")
        raise

# --- FORMAT VALIDATION ---
def parse_format(text):
    required_keys = ["客户姓名", "客户地区", "平台", "客户WS", "P1 编号", "P2 编号", "部门名字"]
    extracted_data = {}
    
    # Handling both "Key-Value" and "Key - Value" formats
    lines = text.strip().split('\n')
    for line in lines:
        if '-' in line:
            parts = line.split('-', 1)
            key = parts[0].strip()
            val = parts[1].strip()
            extracted_data[key] = val

    errors = [key for key in required_keys if not extracted_data.get(key)]
    return extracted_data, errors

# --- HANDLERS ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user = update.message.from_user
    msg_id = update.message.message_id
    
    data, missing_fields = parse_format(user_text)

    if missing_fields:
        error_msg = "❌ **Invalid Information!**\nMissing fields:\n" + "\n".join([f"- {f}" for f in missing_fields])
        await update.message.reply_text(error_msg, parse_mode='Markdown')
        return

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
            str(msg_id) # Stored in Column J (10) for deletion lookup
        ]
        sheet.append_row(row)

        keyboard = [[InlineKeyboardButton("🗑️ Delete This Record", callback_data=f"del_{user.id}_{msg_id}")]]
        await update.message.reply_text("✅ Saved to Dinglong Sheet!", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await update.message.reply_text(f"⚠️ Sheet Error: {e}")

async def delete_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # Extract original user and message ID from callback data
    _, original_user_id, msg_id = query.data.split('_')

    if str(query.from_user.id) != original_user_id:
        await query.answer("🚫 You cannot delete this!", show_alert=True)
        return

    try:
        sheet = get_sheet()
        # Look for the message ID in column 10 (J)
        cell = sheet.find(str(msg_id), in_column=10)
        if cell:
            sheet.delete_rows(cell.row)
            await query.edit_message_text("🗑️ Record deleted from sheet.")
        else:
            await query.answer("Record not found in sheet.", show_alert=True)
    except Exception as e:
        await query.edit_message_text(f"❌ Delete failed: {e}")

def main():
    # Initialize the Application
    application = Application.builder().token(TOKEN).build()
    
    # Add Handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(delete_button_handler))
    
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
