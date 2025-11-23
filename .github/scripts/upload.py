#!/usr/bin/env python3
import os
import glob
import re
import asyncio
import subprocess
from asyncio import Semaphore
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# ----- SETTINGS -----
PARALLEL_UPLOADS = 3
RETRIES = 5
RETRY_DELAY = 5
# ---------------------

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session = os.environ["SESSION"]
bot_token = os.environ["TELEGRAM_TOKEN"]
chat_id = os.environ["TELEGRAM_CHAT_ID"]

chat = int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id


# -------- CAPTIONS --------
def normalize_name(name):
    base = re.split(r"_v|-v", name, maxsplit=1)[0]
    return re.sub(r"[ .-]+", "", base.lower())

captions = {}

if os.path.exists("captions.txt"):
    with open("captions.txt", encoding="utf-8") as f:
        blocks = f.read().strip().split("----")
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            lines = block.splitlines()
            m = re.search(r"File name</b> – ([^\n]+)", lines[0])
            if m:
                fname = m.group(1)
                caption = "\n".join(lines[1:])
                captions[normalize_name(fname)] = caption


def find_caption(filename):
    norm = normalize_name(filename)
    if norm in captions:
        return captions[norm]
    for key in captions:
        if norm.startswith(key) or key.startswith(norm):
            return captions[key]
    return ""


# -------- FILES --------
files = sorted(glob.glob("dl/*.apk") + glob.glob("dl/*.exe"))
if not files:
    print("No files to upload.")
    raise SystemExit(0)

small_files = [f for f in files if os.path.getsize(f) <= 48 * 1024 * 1024]
large_files = [f for f in files if os.path.getsize(f) > 48 * 1024 * 1024]


# -------- SMALL FILES via Bot API --------
for f in small_files:
    base = os.path.basename(f)
    cap = find_caption(base)
    print(f"Uploading SMALL file via Bot API: {base}")

    subprocess.run([
        "curl", "-s", "-X", "POST",
        f"https://api.telegram.org/bot{bot_token}/sendDocument",
        "-F", f"chat_id={chat}",
        "-F", f"document=@{f}",
        "-F", f"caption={cap}",
        "-F", "parse_mode=HTML"
    ], check=False)


# -------- LARGE FILES via TELETHON --------
async def upload_large(client, filepath, sem):
    async with sem:
        name = os.path.basename(filepath)
        caption = find_caption(name)[:1024]

        for attempt in range(1, RETRIES + 1):
            try:
                print(f"Uploading LARGE file: {name} (Attempt {attempt}/{RETRIES})")
                await client.send_file(chat, filepath, caption=caption, force_document=True)
                print(f"Uploaded: {name}")
                return

            except FloodWaitError as e:
                print(f"FloodWait {e.seconds}s")
                await asyncio.sleep(e.seconds)

            except Exception as e:
                print(f"Error uploading {name}: {e}")
                await asyncio.sleep(RETRY_DELAY)

        print(f"FAILED after retries: {name}")


async def main():
    if not large_files:
        return

    sem = Semaphore(PARALLEL_UPLOADS)

    async with TelegramClient(StringSession(session), api_id, api_hash) as client:
        await asyncio.gather(*(upload_large(client, f, sem) for f in large_files))


if __name__ == "__main__":
    asyncio.run(main())
