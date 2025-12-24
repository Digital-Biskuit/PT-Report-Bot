import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = '8341745520:AAEPcNTWEIASN_y5lOwhdeQfbYSUKNsFR7s' # Revoke this after testing!
SHEET_NAME = "Dinglong Part Timer Bot" # Updated to match your screenshot
JSON_KEYFILE = "credentials.json"

# --- GOOGLE SHEETS CONNECTION ---
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
    client = gspread.authorize(creds)
    return client.open(Dinglong Part Timer Bot).sheet1

# --- FORMAT VALIDATION ---
def parse_format(text):
    required_keys = ["客户姓名", "客户地区", "平台", "客户WS", "P1 编号", "P2 编号", "部门名字"]
    extracted_data = {}
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
            str(msg_id)
        ]
        sheet.append_row(row)

        keyboard = [[InlineKeyboardButton("🗑️ Delete This Record", callback_data=f"del_{user.id}_{msg_id}")]]
        await update.message.reply_text("✅ Saved to Dinglong Sheet!", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await update.message.reply_text(f"⚠️ Sheet Error: {e}")

async def delete_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, original_user_id, msg_id = query.data.split('_')

    if str(query.from_user.id) != original_user_id:
        await query.answer("🚫 You cannot delete this!", show_alert=True)
        return

    try:
        sheet = get_sheet()
        cell = sheet.find(str(msg_id), in_column=10)
        if cell:
            sheet.delete_rows(cell.row)
            await query.edit_message_text("🗑️ Deleted from sheet.")
        else:
            await query.answer("Record not found.", show_alert=True)
    except Exception as e:
        await query.edit_message_text(f"❌ Delete failed: {e}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(delete_button_handler))
    application.run_polling()

if __name__ == '__main__':
    main()
