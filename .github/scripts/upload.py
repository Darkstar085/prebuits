#!/usr/bin/env python3
import os
import glob
import re
import asyncio
import subprocess
from asyncio import Semaphore
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError

# ---------- SETTINGS ----------
CHUNK_SIZE = 1024 * 1024
PARALLEL_UPLOADS = 4
RETRIES = 5
RETRY_DELAY = 15
# ------------------------------

api_id = int(os.environ['API_ID'])
api_hash = os.environ['API_HASH']
session = os.environ['SESSION']
bot_token = os.environ['TELEGRAM_TOKEN']
chat_id = os.environ['TELEGRAM_CHAT_ID']

chat = int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id


# ---------- Caption Handling ----------
def normalize_name(name):
    base = re.split(r'_v|-v', name, maxsplit=1)[0]
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
            match = re.search(r"File name</b> – ([^\n]+)", lines[0])
            if match:
                filename = match.group(1)
                cap = "\n".join(lines[1:])
                captions[normalize_name(filename)] = cap


def find_caption(filename: str) -> str:
    norm = normalize_name(filename)
    if norm in captions:
        return captions[norm]

    for key in captions:
        if norm.startswith(key) or key.startswith(norm):
            return captions[key]

    return ""


# ---------- Collect Files ----------
files = sorted(glob.glob("dl/*.apk") + glob.glob("dl/*.exe"))
if not files:
    print("No files found for upload.")
    raise SystemExit(0)

small_files = [f for f in files if os.path.getsize(f) <= 48 * 1024 * 1024]
large_files = [f for f in files if os.path.getsize(f) > 48 * 1024 * 1024]


# ---------- Upload Small Files via Bot API ----------
for f in small_files:
    base = os.path.basename(f)
    cap = find_caption(base)

    print(f"Uploading SMALL file via Bot API: {base}")

    subprocess.run(
        [
            "curl",
            "-s",
            "-X",
            "POST",
            f"https://api.telegram.org/bot{bot_token}/sendDocument",
            "-F",
            f"chat_id={chat}",
            "-F",
            f"document=@{f}",
            "-F",
            f"caption={cap}",
            "-F",
            "parse_mode=HTML",
        ],
        check=False,
    )


# ---------- Pyrogram Progress Callback ----------
def progress(current: int, total: int, filename: str):
    percent = (current / total) * 100 if total else 0
    print(f"[+] Uploading {filename}: {percent:.2f}% ({current}/{total})")


# ---------- Upload Large Files ----------
async def upload_large(app: Client, file_path: str, sem: Semaphore):
    async with sem:
        name = os.path.basename(file_path)
        caption = find_caption(name)[:1024]

        for attempt in range(1, RETRIES + 1):
            try:
                print(f"\nUploading LARGE file: {name} (Attempt {attempt}/{RETRIES})")
                await app.send_document(
                    chat,
                    document=file_path,
                    caption=caption,
                    file_name=name,
                    force_document=True,
                    progress=progress,
                    progress_args=(name,),
                )
                print(f"Completed: {name}")
                return

            except FloodWait as e:
                print(f"FloodWait {e.value}s on {name}")
                await asyncio.sleep(e.value)

            except (RPCError, Exception) as e:
                print(f"Error on {name}: {e}")
                await asyncio.sleep(RETRY_DELAY)

        print(f"FAILED after {RETRIES} attempts: {name}")


async def main():
    if not large_files:
        print("No large files to upload.")
        return

    sem = Semaphore(PARALLEL_UPLOADS)

    async with Client(
        "tg_session",
        api_id=api_id,
        api_hash=api_hash,
        session_string=session,
        workers=16,
    ) as app:
        await asyncio.gather(*(upload_large(app, f, sem) for f in large_files))


if __name__ == "__main__":
    asyncio.run(main())