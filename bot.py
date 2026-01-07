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
    API_ID, API_HASH, SESSION_NAME,
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME,
    REDDIT_PASSWORD, REDDIT_USER_AGENT
)

# Initialize the Client (Userbot)
app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)

# Initialize Reddit Client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    username=REDDIT_USERNAME,
    password=REDDIT_PASSWORD,
    user_agent=REDDIT_USER_AGENT
)

@app.on_message(filters.me & filters.command("start", prefixes="/"))
async def start_handler(client, message):
    await message.edit_text(
        "**Reddit Saved Post Downloader**\n\n"
        "This bot fetches your saved posts from Reddit and downloads/forwards the media to Telegram.\n\n"
        "**Commands:**\n"
        "`/info` - Show information.\n"
        "`/from <start_index> [limit] [target]` - Fetch saved posts starting from index.\n\n"
        "Example: `/from 0 10` (Fetch 10 newest)\n"
        "Example: `/from 10 5` (Skip 10 newest, fetch next 5)"
    )

@app.on_message(filters.me & filters.command("info", prefixes="/"))
async def info_handler(client, message):
    await message.edit_text(
        "**Bot Information**\n\n"
        "Library: Pyrogram (MTProto) + PRAW + yt-dlp\n"
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
        # 'format': 'bestvideo+bestaudio/best', # Default is usually fine
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

@app.on_message(filters.me & filters.command("from", prefixes="/"))
async def fetch_reddit_handler(client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.edit_text("Usage: `/from <start_index> [limit] [target]`\nExample: `/from 0 10`")
            return

        start_index = int(args[1])
        limit_count = int(args[2]) if len(args) > 2 and args[2].isdigit() else 10

        target_chat_id = message.chat.id
        target_name = "This chat"

        # Check for target chat argument (if 3rd arg is not a digit, or 4th arg)
        target_arg = None
        if len(args) > 2 and not args[2].isdigit():
             target_arg = args[2]
        elif len(args) > 3:
             target_arg = args[3]

        if target_arg:
            try:
                target_chat = await client.get_chat(target_arg)
                target_chat_id = target_chat.id
                target_name = target_chat.title or target_chat.username
            except Exception as e:
                await message.edit_text(f"Invalid Target Chat: {target_arg}\nError: {e}")
                return

    except ValueError:
        await message.edit_text("Invalid arguments. Use integers for index/limit.")
        return

    status_msg = await message.edit_text(f"Fetching Reddit saved posts...\nStart: {start_index}\nCount: {limit_count}\nTarget: {target_name}")

    try:
        # Fetch saved posts generator
        # limit=None fetches all, we slice it
        # Note: Fetching 'all' can be slow if user has thousands.
        # But we need to iterate to reach start_index.
        # PRAW handles pagination transparently.
        saved_gen = reddit.user.me().saved(limit=None)

        # Slice: start, stop (start + limit)
        # itertools.islice consumes the generator
        posts_slice = list(itertools.islice(saved_gen, start_index, start_index + limit_count))

        if not posts_slice:
            await status_msg.edit_text("No posts found in this range.")
            return

        success_count = 0

        for i, post in enumerate(posts_slice):
            current_idx = start_index + i
            # Update status every 5 posts or so
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

            # Skip self posts (text only) unless they have media embedded (rarely reliable to check)
            # Generally 'is_self' means text post.
            if getattr(post, 'is_self', False):
                continue

            # Determine URL
            url = getattr(post, 'url', None)
            if not url:
                continue

            # Download
            files = await asyncio.to_thread(download_media, url)

            if not files:
                # Fallback: Send link if download fails? Or just skip.
                # await client.send_message(target_chat_id, f"Failed to download: {url}")
                continue

            # Upload
            caption = f"{post.title}\n\nVia /u/{post.author} in /r/{post.subreddit}"
            for file_path in files:
                try:
                    if not os.path.exists(file_path):
                        continue

                    # Determine type
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        await client.send_photo(target_chat_id, photo=file_path, caption=caption)
                    elif ext in ['.mp4', '.mkv', '.webm', '.gif']:
                         await client.send_video(target_chat_id, video=file_path, caption=caption)
                    else:
                        await client.send_document(target_chat_id, document=file_path, caption=caption)

                    success_count += 1

                    # Cleanup
                    os.remove(file_path)

                    # Sleep slightly to respect Telegram limits
                    await asyncio.sleep(1)

                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    # Retry once?
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

        # Cleanup download dir if empty
        if os.path.exists("downloads") and not os.listdir("downloads"):
             os.rmdir("downloads")

    except Exception as e:
        await status_msg.edit_text(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    print("Starting Reddit Userbot...")
    app.run()
