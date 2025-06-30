import os, json, datetime as dt
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

# ─── Константы ─────────────────────────────
TZ = pytz.timezone("Europe/Moscow")
BOT_TOKEN         = os.environ["BOT_TOKEN"]
SHEET_ID          = os.environ["SHEET_ID"]
USER_IDS          = [int(x) for x in os.environ["USER_IDS"].split(",")]
SA_CREDENTIALS    = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])

# ─── Google Sheets ─────────────────────────
def open_sheet():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(SA_CREDENTIALS, scope)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID).sheet1

def birthdays_to_remind(today: dt.date):
    sheet = open_sheet()
    records = sheet.get_all_records()
    upcoming = []
    for row in records:
        name, date_str = row["ФИО"], row["Дата рождения"]
        day, month = map(int, date_str.split("."))
        year = today.year
        bday = dt.date(year, month, day)
        if bday < today:
            bday = dt.date(year + 1, month, day)
        reminder = bday - dt.timedelta(days=7)
        while reminder.weekday() >= 5:
            reminder -= dt.timedelta(days=1)
        if reminder == today:
            upcoming.append((name, bday))
    return upcoming

# ─── Handlers ──────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ваш Telegram ID: {update.effective_chat.id}")

async def daily_check(context: ContextTypes.DEFAULT_TYPE):
    today = dt.datetime.now(TZ).date()
    for name, bday in birthdays_to_remind(today):
        msg = (f"📅 Через неделю, {bday.strftime('%d.%m')}, "
               f"день рождения у {name}! 🎂")
        for uid in USER_IDS:
            await context.bot.send_message(chat_id=uid, text=msg)

# ─── main ──────────────────────────────────
def main():
    app = (ApplicationBuilder()
           .token(BOT_TOKEN)
           .timezone(TZ)
           .build())
    app.add_handler(CommandHandler("start", cmd_start))
    app.job_queue.run_daily(daily_check,
                            time=dt.time(hour=12, minute=0, tzinfo=TZ))
    app.run_polling()

if __name__ == "__main__":
    main()
