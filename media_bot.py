import os
import re
import asyncio
import logging
from dotenv import load_dotenv
from pyrogram import Client, enums
import yt_dlp

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

# Ensure configuration exists
if not all([API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID]):
    print("Error: Missing configuration in .env file.")
    exit(1)

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Pyrogram Client
# Using in-memory session to ensure it acts as a Bot and not a User
app = Client(
    "media_bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

def get_channel_id(channel_id_str):
    """
    Resolves the channel ID.
    Pyrogram handles strings (@channel) and integers (-100...) natively,
    but we ensure integers are cast correctly.
    """
    if channel_id_str.lstrip('-').isdigit():
        return int(channel_id_str)
    return channel_id_str

async def download_media(url):
    """Downloads media from the given URL using yt-dlp."""
    output_dir = 'downloads'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Use a specific template to control filenames
    output_template = os.path.join(output_dir, '%(id)s.%(ext)s')

    ydl_opts = {
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 2000 * 1024 * 1024, # 2GB
        # 'noplaylist': True, # Default behavior
    }

    try:
        logger.info(f"Downloading: {url}")
        # Run yt-dlp in a separate thread to avoid blocking the async loop
        def run_yt_dlp():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info

        loop = asyncio.get_event_loop()
        # Using executor for blocking call
        await loop.run_in_executor(None, run_yt_dlp)

        # Return list of files in output_dir
        # Since we clean up, any file here is new
        return [os.path.join(output_dir, f) for f in os.listdir(output_dir)]

    except Exception as e:
        logger.error(f"Download error for {url}: {e}")
        return []

async def process_messages():
    """Poller to process messages."""

    channel_target = get_channel_id(CHANNEL_ID)
    logger.info(f"Monitoring channel: {CHANNEL_ID}")

    async with app:
        while True:
            try:
                # Fetch history (last 10 messages)
                # Pyrogram's get_chat_history is async generator
                history = app.get_chat_history(channel_target, limit=10)

                async for message in history:
                    if not message.text:
                        continue

                    # Check criteria: "New Saved Posts:" and not "✅"
                    if "New Saved Posts:" in message.text and "✅" not in message.text:
                        logger.info(f"Processing message {message.id}...")

                        # Extract URLs
                        # Regex modified to handle Markdown links [Title](URL) or plain URL
                        # Captures URL inside () or standalone
                        url_regex = r"https?://(?:www\.)?(?:reddit\.com|redd\.it)/[^\s\)]+"
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
                                    # Pyrogram supports uploading files directly
                                    # We try to determine type, or just send_document/video
                                    # Reddit media is usually video or image.
                                    # send_document is safest for "file", send_video/photo for stream.
                                    # User mentioned "stream it". send_video/send_photo renders it in stream.
                                    ext = os.path.splitext(file_path)[1].lower()
                                    if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                                        await app.send_photo(channel_target, file_path)
                                    elif ext in ['.mp4', '.mkv', '.webm', '.gif']:
                                        await app.send_video(channel_target, file_path)
                                    else:
                                        await app.send_document(channel_target, file_path)

                                    uploaded_count += 1
                                except Exception as err:
                                    logger.error(f"Upload failed for {file_path}: {err}")
                                finally:
                                    # Delete immediately after upload attempt
                                    if os.path.exists(file_path):
                                        os.remove(file_path)

                        # Mark as processed
                        # We append to the message.
                        new_text = message.text + "\n\n✅ Processed & Downloaded"
                        try:
                            # Keep the formatting of the original message (Markdown)
                            await app.edit_message_text(channel_target, message.id, new_text, disable_web_page_preview=True)
                            logger.info("Message marked as processed.")
                        except Exception as err:
                            logger.error(f"Failed to edit message: {err}")

                        # Final Cleanup of downloads dir (if any leftovers)
                        output_dir = 'downloads'
                        if os.path.exists(output_dir):
                            for f in os.listdir(output_dir):
                                p = os.path.join(output_dir, f)
                                if os.path.exists(p):
                                    os.remove(p)
                            os.rmdir(output_dir)

            except Exception as e:
                logger.error(f"Error in loop: {e}")
                # Wait a bit before retrying if error
                await asyncio.sleep(5)

            # Sleep 15s before next poll
            await asyncio.sleep(15)

if __name__ == '__main__':
    # Run the poller
    try:
        asyncio.run(process_messages())
    except KeyboardInterrupt:
        print("Stopped.")
