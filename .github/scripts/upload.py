#!/usr/bin/env python3
import asyncio
import glob
import html
import os
import re
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import FloodWaitError, RPCError
from telethon.sessions import StringSession

PARALLEL_UPLOADS = max(1, int(os.getenv("PARALLEL_UPLOADS", "2")))
RETRIES = max(1, int(os.getenv("UPLOAD_RETRIES", "5")))
RETRY_DELAY = max(1, int(os.getenv("UPLOAD_RETRY_DELAY", "8")))
DEDUP_SCAN_LIMIT = max(0, int(os.getenv("DEDUP_SCAN_LIMIT", "500")))
MAX_CAPTION = 1024

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session = os.environ["SESSION"]
bot_token = os.environ.get("TELEGRAM_TOKEN", "")
chat_id = os.environ["TELEGRAM_CHAT_ID"]
chat = int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id


def normalize_name(name: str) -> str:
    base = re.split(r"_v|-v", Path(name).name, maxsplit=1)[0]
    return re.sub(r"[^a-z0-9]+", "", base.lower())


def load_captions():
    captions = {}
    path = Path("captions.txt")
    if not path.exists():
        return captions

    text = path.read_text(encoding="utf-8")
    for block in re.split(r"\n\s*-{4,}\s*\n", text):
        block = block.strip()
        if not block:
            continue
        match = re.search(r"File name</b>\s*[–-]\s*([^\n]+)", block)
        if not match:
            continue
        filename = match.group(1).strip()
        telegram_caption = re.sub(
            r"^\s*📦\s*<b>File name</b>\s*[–-]\s*[^\n]*\n?",
            "",
            block,
            count=1,
            flags=re.MULTILINE,
        ).strip()
        captions[normalize_name(filename)] = telegram_caption[:MAX_CAPTION]
    return captions


captions = load_captions()


def find_caption(filename: str) -> str:
    norm = normalize_name(filename)
    if norm in captions:
        return captions[norm]
    for key, value in captions.items():
        if norm.startswith(key) or key.startswith(norm):
            return value
    return ""


def file_key(path: str) -> str:
    """Return a Telegram-compatible deduplication key.

    Telegram exposes the uploaded document's filename and size without
    downloading the message contents. Matching the same filename+size on
    both sides makes the local duplicate key comparable with history scans.
    Release assets already contain the version in their filename, so this is
    sufficient while avoiding an unnecessary full-file SHA-256 pass.
    """
    return f"{Path(path).name}:{os.path.getsize(path)}"


files = sorted(glob.glob("dl/*.apk") + glob.glob("dl/*.exe"))
if not files:
    print("No files to upload.")
    raise SystemExit(0)

print(f"Found {len(files)} file(s) to deliver.")


async def send_with_retry(client, filepath, already_sent):
    name = Path(filepath).name
    key = file_key(filepath)
    if name in already_sent or key in already_sent:
        print(f"SKIP duplicate: {name}")
        return True

    caption = find_caption(name)
    for attempt in range(1, RETRIES + 1):
        try:
            print(f"Uploading {name} ({attempt}/{RETRIES})")
            await client.send_file(
                chat,
                filepath,
                caption=caption,
                force_document=True,
                parse_mode="html",
                supports_streaming=False,
            )
            print(f"Uploaded: {name}")
            return True
        except FloodWaitError as exc:
            delay = max(exc.seconds, RETRY_DELAY)
            print(f"Telegram FloodWait for {delay}s: {name}")
            await asyncio.sleep(delay)
        except (RPCError, OSError, TimeoutError) as exc:
            print(f"Upload error for {name}: {exc}")
            if attempt < RETRIES:
                await asyncio.sleep(RETRY_DELAY * attempt)
        except Exception as exc:
            print(f"Unexpected upload error for {name}: {exc}")
            if attempt < RETRIES:
                await asyncio.sleep(RETRY_DELAY * attempt)

    print(f"FAILED after {RETRIES} attempts: {name}")
    return False


async def collect_recent_filenames(client):
    sent = set()
    if DEDUP_SCAN_LIMIT == 0:
        return sent

    print(f"Scanning up to {DEDUP_SCAN_LIMIT} recent Telegram messages for duplicates...")
    async for message in client.iter_messages(chat, limit=DEDUP_SCAN_LIMIT):
        if not message.file:
            continue
        filename = message.file.name
        if filename:
            sent.add(filename)
            try:
                sent.add(f"{filename}:{message.file.size}")
            except Exception:
                pass
    print(f"Found {len(sent)} existing filename/size marker(s).")
    return sent


async def main():
    if not session:
        raise RuntimeError("TELEGRAM_SESSION is empty")

    async with TelegramClient(StringSession(session), api_id, api_hash) as client:
        already_sent = await collect_recent_filenames(client)
        sem = asyncio.Semaphore(PARALLEL_UPLOADS)

        async def worker(path):
            async with sem:
                return await send_with_retry(client, path, already_sent)

        results = await asyncio.gather(*(worker(path) for path in files))

    failed = [str(path) for path, ok in zip(files, results) if not ok]
    if failed:
        print("Failed files:")
        for path in failed:
            print(f" - {path}")
        raise SystemExit(1)

    print("All files delivered successfully.")


if __name__ == "__main__":
    asyncio.run(main())
