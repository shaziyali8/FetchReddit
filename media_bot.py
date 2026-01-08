import os
import asyncio
import logging
import re
import shutil
from pyrogram import Client
from pyrogram.errors import FloodWait
import yt_dlp

# Load environment variables (if using python-dotenv, otherwise assume set)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

# Validate Config
if not all([API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID]):
    print("Error: Missing env variables. Check .env.example")
    exit(1)

# Try to convert CHANNEL_ID to int if possible
try:
    CHANNEL_ID = int(CHANNEL_ID)
except ValueError:
    pass

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Client
app = Client(
    "reddit_media_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def download_media(url, output_dir="downloads"):
    """
    Downloads media using yt-dlp. Returns list of file paths.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 2000 * 1024 * 1024, # 2GB
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            if 'entries' in info:
                # Playlist or gallery
                files = []
                for entry in info['entries']:
                    filename = ydl.prepare_filename(entry)
                    files.append(filename)
                return files
            else:
                filename = ydl.prepare_filename(info)
                return [filename]
        except Exception as e:
            logger.error(f"yt-dlp error for {url}: {e}")
            return []

async def process_history():
    logger.info("Checking for new links...")
    async with app:
        # Get last 10 messages from channel
        try:
            async for message in app.get_chat_history(CHANNEL_ID, limit=10):
                # Filter: Text message, contains "New Saved Posts", not marked processed
                if not message.text:
                    continue

                if "New Saved Posts:" in message.text and "✅" not in message.text:
                    logger.info(f"Processing Message {message.id}...")

                    # Extract URLs
                    urls = re.findall(r'(https?://(?:www\.)?(?:reddit\.com|redd\.it)/[^\s]+)', message.text)

                    if not urls:
                        continue

                    # Mark as In Progress immediately to avoid double processing (if slow)
                    # We append a clock or similar, but the main loop is serial so it's okay.

                    files_to_upload = []

                    for url in urls:
                        logger.info(f"Downloading: {url}")
                        files = await asyncio.to_thread(download_media, url)
                        files_to_upload.extend(files)

                    # Upload Files
                    if files_to_upload:
                        for file_path in files_to_upload:
                            if not os.path.exists(file_path):
                                continue

                            try:
                                logger.info(f"Uploading: {file_path}")
                                ext = os.path.splitext(file_path)[1].lower()

                                if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                                    await app.send_photo(CHANNEL_ID, photo=file_path)
                                elif ext in ['.mp4', '.mkv', '.webm', '.gif']:
                                    await app.send_video(CHANNEL_ID, video=file_path)
                                else:
                                    await app.send_document(CHANNEL_ID, document=file_path)

                                # Cleanup
                                os.remove(file_path)
                                await asyncio.sleep(2) # Rate limit

                            except FloodWait as e:
                                logger.warning(f"FloodWait: sleeping {e.value}s")
                                await asyncio.sleep(e.value)
                            except Exception as e:
                                logger.error(f"Upload failed: {e}")

                    # Cleanup dir
                    if os.path.exists("downloads") and not os.listdir("downloads"):
                        os.rmdir("downloads")

                    # Mark original message as processed
                    new_text = message.text + "\n\n✅ Processed & Downloaded"
                    try:
                        await message.edit_text(new_text, disable_web_page_preview=True)
                        logger.info(f"Message {message.id} marked as processed.")
                    except Exception as e:
                        logger.error(f"Failed to edit message: {e}")

        except Exception as e:
            logger.error(f"Error fetching history: {e}")

async def main():
    while True:
        try:
            await process_history()
        except Exception as e:
            logger.error(f"Main loop error: {e}")

        # Poll every 15 seconds
        await asyncio.sleep(15)

if __name__ == '__main__':
    print("Starting Media Downloader Bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped.")
