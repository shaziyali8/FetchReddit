import asyncio
import os
import shutil
import itertools
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import praw
import yt_dlp
from config import (
    API_ID, API_HASH, BOT_TOKEN, OWNER_ID, SESSION_NAME,
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME,
    REDDIT_PASSWORD, REDDIT_USER_AGENT
)

# Initialize the Client (Bot)
app = Client(
    SESSION_NAME,
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

# Filter for the owner
def is_owner(_, __, message: Message):
    return message.from_user and message.from_user.id == OWNER_ID

owner_filter = filters.create(is_owner)

@app.on_message(filters.command("start", prefixes="/"))
async def start_handler(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply_text(
            f"**Unauthorized**\n"
            f"This bot is private.\n"
            f"Your ID: `{message.from_user.id}`\n"
            f"Configured Owner ID: `{OWNER_ID}`"
        )
        return

    await message.reply_text(
        "**Reddit Saved Post Downloader (Bot)**\n\n"
        "This bot fetches your saved posts from Reddit and uploads the media to Telegram.\n\n"
        "**Commands:**\n"
        "`/info` - Show information.\n"
        "`/from <start_index> [limit] [target]` - Fetch saved posts.\n\n"
        "**Target Channel**: Make sure to add this bot as an Admin in the target channel first!\n\n"
        "Example: `/from 0 10 @MyArchive`"
    )

@app.on_message(filters.command("info", prefixes="/") & owner_filter)
async def info_handler(client, message):
    await message.reply_text(
        "**Bot Information**\n\n"
        "Type: Telegram Bot (MTProto)\n"
        "Function: Downloads saved media from Reddit account.\n"
        "Support: Images, Videos, Galleries.\n\n"
        "**Usage:**\n"
        "`/from <start_index> <count> [target]`\n"
        "- `start_index`: 0 for newest.\n"
        "- `count`: Number of posts to check.\n"
        "- `target`: (Optional) Channel username/ID."
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
        'max_filesize': 2000 * 1024 * 1024, # 2GB Limit
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
            print(f"yt-dlp error for {url}: {e}")
            return []

@app.on_message(filters.command("from", prefixes="/") & owner_filter)
async def fetch_reddit_handler(client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text("Usage: `/from <start_index> [limit] [target]`\nExample: `/from 0 10 @MyChannel`")
            return

        start_index = int(args[1])
        limit_count = int(args[2]) if len(args) > 2 and args[2].isdigit() else 10

        # Default target is the chat where command is sent
        target_chat_id = message.chat.id
        target_name = "This chat"

        # Parse target arg
        target_arg = None
        if len(args) > 2 and not args[2].isdigit():
             target_arg = args[2]
        elif len(args) > 3:
             target_arg = args[3]

        if target_arg:
            try:
                target_chat = await client.get_chat(target_arg)
                target_chat_id = target_chat.id
                target_name = target_chat.title or target_chat.username or str(target_chat_id)
            except Exception as e:
                await message.reply_text(f"Invalid Target Chat: `{target_arg}`\n\n**Error**: {e}\n\nMake sure the Bot is an **Admin** in that channel!")
                return

    except ValueError:
        await message.reply_text("Invalid arguments. Use integers for index/limit.")
        return

    status_msg = await message.reply_text(f"Fetching Reddit saved posts...\nStart: {start_index}\nCount: {limit_count}\nTarget: {target_name}")

    try:
        # Fetch saved posts generator
        saved_gen = reddit.user.me().saved(limit=None)

        # Slice
        posts_slice = list(itertools.islice(saved_gen, start_index, start_index + limit_count))

        if not posts_slice:
            await status_msg.edit_text("No posts found in this range.")
            return

        success_count = 0

        for i, post in enumerate(posts_slice):
            current_idx = start_index + i
            # Update status every 5 posts
            if i % 5 == 0:
                try:
                    await status_msg.edit_text(
                        f"Processing post {i+1}/{len(posts_slice)} (Index {current_idx})\n"
                        f"Success: {success_count}"
                    )
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception:
                    pass

            if getattr(post, 'is_self', False):
                continue

            url = getattr(post, 'url', None)
            if not url:
                continue

            files = await asyncio.to_thread(download_media, url)

            if not files:
                continue

            caption = f"**{post.title}**\n/r/{post.subreddit}\n[Link](https://reddit.com{post.permalink})"

            for file_path in files:
                try:
                    if not os.path.exists(file_path):
                        continue

                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        await client.send_photo(target_chat_id, photo=file_path, caption=caption)
                    elif ext in ['.mp4', '.mkv', '.webm', '.gif']:
                         await client.send_video(target_chat_id, video=file_path, caption=caption)
                    else:
                        await client.send_document(target_chat_id, document=file_path, caption=caption)

                    success_count += 1
                    os.remove(file_path)
                    await asyncio.sleep(1)

                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    try:
                        await client.send_document(target_chat_id, document=file_path, caption=caption)
                        success_count += 1
                        os.remove(file_path)
                    except:
                        pass
                except Exception as e:
                    print(f"Upload error: {e}")

        await status_msg.edit_text(
            f"**Fetch Complete!**\n"
            f"Processed: {len(posts_slice)}\n"
            f"Uploaded: {success_count}"
        )

        if os.path.exists("downloads") and not os.listdir("downloads"):
             os.rmdir("downloads")

    except Exception as e:
        await status_msg.edit_text(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    print("Starting Telegram Bot...")
    app.run()
