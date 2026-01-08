import os
import re
import asyncio
import logging
import shutil
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Message
import yt_dlp

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
SESSION_FILE = 'session'

# Ensure configuration exists
if not all([API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID]):
    print("Error: Missing configuration in .env file.")
    exit(1)

API_ID = int(API_ID)

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Telegram Client
client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

async def download_media(url):
    """Downloads media from the given URL using yt-dlp."""
    output_dir = 'downloads'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_template = os.path.join(output_dir, '%(id)s.%(ext)s')

    ydl_opts = {
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 2000 * 1024 * 1024, # 2GB
        # 'noplaylist': True, # Default behavior usually fine
    }

    downloaded_files = []

    try:
        logger.info(f"Downloading: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'entries' in info:
                # It's a playlist or gallery
                for entry in info['entries']:
                    if entry:
                        filename = ydl.prepare_filename(entry)
                        downloaded_files.append(filename)
            else:
                filename = ydl.prepare_filename(info)
                downloaded_files.append(filename)

        # Verify files exist (yt-dlp might change extension)
        final_files = []
        for f in downloaded_files:
             # Sometimes prepare_filename result doesn't match exactly if yt-dlp merges formats
             # But usually it is correct. If not, we might need to scan the dir.
             # However, let's assume it works or we scan the dir for created files.
             if os.path.exists(f):
                 final_files.append(f)
             else:
                 # Fallback: check directory for similar files?
                 # For now, let's just list the dir if the specific file isn't found?
                 # Actually, commonly yt-dlp merges video+audio into .mkv or .mp4
                 # prepare_filename might return .mp4 but it wrote .mkv if configured so.
                 # Let's simple scan the directory for files modified recently?
                 # Or just list all files in downloads since we clean it up.
                 pass

        # Simpler approach: return all files in downloads folder since we clean it up after every message
        return [os.path.join(output_dir, f) for f in os.listdir(output_dir)]

    except Exception as e:
        logger.error(f"Download error for {url}: {e}")
        return []

async def main():
    logger.info("Starting Telegram Bot...")

    # Start the client
    # If BOT_TOKEN is provided, we can use it to log in as a bot.
    await client.start(bot_token=BOT_TOKEN)

    logger.info("Bot connected.")

    # Resolve Channel ID
    try:
        if CHANNEL_ID.lstrip('-').isdigit():
            entity = await client.get_entity(int(CHANNEL_ID))
        else:
            entity = await client.get_entity(CHANNEL_ID)
        logger.info(f"Monitoring {getattr(entity, 'title', entity.id)}...")
    except Exception as e:
        logger.error(f"Could not find channel: {e}")
        return

    while True:
        try:
            # Get last 10 messages
            # Note: iter_messages is asynchronous generator
            messages = await client.get_messages(entity, limit=10)

            for message in messages:
                if not message.text:
                    continue

                # Check criteria: "New Saved Posts" and not "✅"
                if "New Saved Posts:" in message.text and "✅" not in message.text:
                    logger.info(f"Processing message {message.id}...")

                    # Extract URLs
                    # Regex to match URLs
                    url_regex = r"(https?://(?:www\.)?(?:reddit\.com|redd\.it)/[^\s]+)"
                    urls = re.findall(url_regex, message.text)

                    if not urls:
                        continue

                    files_to_upload = []

                    for url in urls:
                        files = await download_media(url)
                        files_to_upload.extend(files)

                    # Upload
                    uploaded_count = 0
                    for file_path in files_to_upload:
                        if os.path.exists(file_path):
                            logger.info(f"Uploading {file_path}...")
                            try:
                                await client.send_file(entity, file_path)
                                os.remove(file_path) # Delete after upload
                                uploaded_count += 1
                            except Exception as err:
                                logger.error(f"Upload failed for {file_path}: {err}")

                    # Mark as processed
                    if uploaded_count > 0 or not files_to_upload:
                        # Even if download failed, maybe we should mark it?
                        # The original JS marked it if "urls" were found.
                        # We append to the message.
                        new_text = message.text + "\n\n✅ Processed & Downloaded"
                        try:
                            await client.edit_message(entity, message.id, text=new_text, link_preview=False)
                            logger.info("Message marked as processed.")
                        except Exception as err:
                            logger.error(f"Failed to edit message: {err}")

                    # Cleanup downloads dir
                    output_dir = 'downloads'
                    if os.path.exists(output_dir):
                        # Remove any remaining files
                        for f in os.listdir(output_dir):
                            os.remove(os.path.join(output_dir, f))
                        os.rmdir(output_dir)

        except Exception as e:
            logger.error(f"Error in loop: {e}")

        # Sleep 15s
        await asyncio.sleep(15)

if __name__ == '__main__':
    # Telethon's client.run_until_disconnected() is usually for event loops.
    # But here we have a custom loop.
    with client:
        client.loop.run_until_complete(main())
