import os
import asyncio
import logging
import shutil
import itertools
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import praw
import yt_dlp

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize Pyrogram Client (Bot)
app = Client(
    "reddit_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Initialize Reddit Client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    username=REDDIT_USERNAME,
    password=REDDIT_PASSWORD,
    user_agent=REDDIT_USER_AGENT
)

# Owner Filter
def is_owner(_, __, message: Message):
    return message.from_user and message.from_user.id == OWNER_ID

owner_filter = filters.create(is_owner)

@app.on_message(filters.command("start") & owner_filter)
async def start_handler(client, message):
    await message.reply_text(
        "**Reddit Saved Posts Bot (Pyrogram)**\n\n"
        "Commands:\n"
        "`/info` - Check status\n"
        "`/post from=START to=END` - Post saved items (max 20)"
    )

@app.on_message(filters.command("info") & owner_filter)
async def info_handler(client, message):
    try:
        me = await asyncio.to_thread(lambda: reddit.user.me())
        username = me.name if me else "Unknown"
        await message.reply_text(
            f"**Bot Status**: Online\n"
            f"**Reddit User**: `/u/{username}`\n"
            f"**Target Channel**: `{TELEGRAM_CHANNEL_ID}`\n"
            f"**Backend**: Pyrogram (Supports large files)"
        )
    except Exception as e:
        await message.reply_text(f"Error connecting to Reddit: {e}")

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
            logging.warning(f"yt-dlp error for {url}: {e}")
            return []

@app.on_message(filters.command("post") & owner_filter)
async def post_handler(client, message: Message):
    # Parse arguments: /post from=0 to=10
    args = message.text.split()[1:] # Skip command
    start_idx = 0
    end_idx = 10

    try:
        for arg in args:
            if arg.startswith("from="):
                start_idx = int(arg.split("=")[1])
            elif arg.startswith("to="):
                end_idx = int(arg.split("=")[1])
    except ValueError:
        await message.reply_text("Invalid arguments. Use `from=START to=END`")
        return

    count = end_idx - start_idx
    if count <= 0 or count > 20:
        await message.reply_text("Range must be positive and max 20 items.")
        return

    status_msg = await message.reply_text(f"Fetching {count} posts (from {start_idx} to {end_idx})...")

    try:
        # Fetch posts
        def fetch_posts():
            saved = reddit.user.me().saved(limit=None)
            return list(itertools.islice(saved, start_idx, end_idx))

        posts = await asyncio.to_thread(fetch_posts)

        if not posts:
            await status_msg.edit_text("No posts found in this range.")
            return

        success_count = 0

        for post in posts:
            await asyncio.sleep(2) # Rate limit

            try:
                # Basic check for Submission vs Comment
                if not getattr(post, 'title', None):
                    continue

                title = post.title
                url = post.url
                subreddit = post.subreddit.display_name
                permalink = f"https://reddit.com{post.permalink}"
                caption = f"**{title}**\n/r/{subreddit}\n[Reddit Link]({permalink})"

                # Resolve target chat
                try:
                    # If channel ID is an integer string, convert it
                    target_chat = int(TELEGRAM_CHANNEL_ID)
                except ValueError:
                    target_chat = TELEGRAM_CHANNEL_ID

                sent = False
                files = []

                # Attempt download first (robust for large videos/images)
                # If it's a simple text post, skip download
                if not getattr(post, 'is_self', False):
                    files = await asyncio.to_thread(download_media, url)

                if files:
                    for file_path in files:
                        if not os.path.exists(file_path):
                            continue

                        try:
                            ext = os.path.splitext(file_path)[1].lower()
                            if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                                await client.send_photo(target_chat, photo=file_path, caption=caption)
                            elif ext in ['.mp4', '.mkv', '.webm', '.gif']:
                                await client.send_video(target_chat, video=file_path, caption=caption)
                            else:
                                await client.send_document(target_chat, document=file_path, caption=caption)

                            sent = True
                            success_count += 1
                        except FloodWait as e:
                            await asyncio.sleep(e.value)
                            # Retry logic could go here
                        except Exception as e:
                            logging.error(f"Upload failed: {e}")
                        finally:
                            # Cleanup
                            if os.path.exists(file_path):
                                os.remove(file_path)

                if not sent:
                    # Fallback to text/link
                    if post.is_self:
                        text = post.selftext[:500] + "..." if len(post.selftext) > 500 else post.selftext
                        msg = f"{caption}\n\n{text}"
                        await client.send_message(target_chat, msg, disable_web_page_preview=True)
                    else:
                        msg = f"{caption}\nLink: {url}"
                        await client.send_message(target_chat, msg)
                    success_count += 1

            except Exception as e:
                logging.error(f"Error processing post {post.id}: {e}")

        await status_msg.edit_text(f"Done. Processed {success_count}/{len(posts)} items.")

        # Final cleanup
        if os.path.exists("downloads") and not os.listdir("downloads"):
             os.rmdir("downloads")

    except Exception as e:
        await status_msg.edit_text(f"Error: {e}")

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not set.")
        exit(1)

    print("Starting Pyrogram Bot...")
    app.run()
