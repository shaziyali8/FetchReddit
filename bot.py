import os
import asyncio
import logging
import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import praw

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
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

# Initialize Reddit Client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    username=REDDIT_USERNAME,
    password=REDDIT_PASSWORD,
    user_agent=REDDIT_USER_AGENT
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Reddit Saved Posts Bot\n\n"
        "Commands:\n"
        "/info - Check status\n"
        "/post from=START to=END - Post saved items to channel (max 20)"
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        me = await asyncio.to_thread(reddit.user.me)
        username = me.name if me else "Unknown"
        await update.message.reply_text(
            f"Bot Status: Online\n"
            f"Reddit User: /u/{username}\n"
            f"Target Channel: {TELEGRAM_CHANNEL_ID}"
        )
    except Exception as e:
        await update.message.reply_text(f"Error connecting to Reddit: {e}")

async def post_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    start_idx = 0
    end_idx = 10

    # Parse arguments like from=0 to=10
    try:
        for arg in args:
            if arg.startswith("from="):
                start_idx = int(arg.split("=")[1])
            elif arg.startswith("to="):
                end_idx = int(arg.split("=")[1])
    except ValueError:
        await update.message.reply_text("Invalid arguments. Use from=START to=END")
        return

    count = end_idx - start_idx
    if count <= 0 or count > 20:
        await update.message.reply_text("Range must be positive and max 20 items.")
        return

    status_msg = await update.message.reply_text(f"Fetching {count} posts (from {start_idx} to {end_idx})...")

    try:
        # Fetch posts in a separate thread to avoid blocking
        def fetch_posts():
            # saved(limit=None) fetches everything, but we need to slice locally
            # because PRAW doesn't support offset directly in saved()
            # Note: This might be slow for users with thousands of saved posts.
            # Ideally we iterate and discard, but PRAW generators are efficient.
            saved = reddit.user.me().saved(limit=None)
            import itertools
            return list(itertools.islice(saved, start_idx, end_idx))

        posts = await asyncio.to_thread(fetch_posts)

        if not posts:
            await status_msg.edit_text("No posts found in this range.")
            return

        success_count = 0

        for post in posts:
            # Sleep to respect limits
            await asyncio.sleep(2)

            try:
                # Skip deleted/private? PRAW usually filters these or raises error on access.
                # Check if it's a submission or comment
                if not isinstance(post, praw.models.Submission):
                    # We only handle submissions, not saved comments
                    continue

                title = post.title
                url = post.url
                subreddit = post.subreddit.display_name
                permalink = f"https://reddit.com{post.permalink}"
                caption = f"<b>{title}</b>\n/r/{subreddit}\n<a href='{permalink}'>Reddit Link</a>"

                # Determine type
                is_video = getattr(post, 'is_video', False)
                is_gallery = hasattr(post, 'is_gallery') and post.is_gallery
                domain = post.domain

                sent = False

                # Try sending as media first
                try:
                    if is_video:
                        # PRAW doesn't give direct video URL easily for hosted videos.
                        # Usually fallback_url in media dict.
                        video_url = None
                        if hasattr(post, 'media') and post.media and 'reddit_video' in post.media:
                            video_url = post.media['reddit_video']['fallback_url']
                        else:
                            video_url = url # External video?

                        await context.bot.send_video(
                            chat_id=TELEGRAM_CHANNEL_ID,
                            video=video_url,
                            caption=caption,
                            parse_mode='HTML'
                        )
                        sent = True

                    elif is_gallery:
                        # Telegram limits to 10 photos in group. Just link it or send first image.
                        # Parsing gallery is complex. Let's send link for robustness as requested "fallback to link"
                        # Or try sending first image?
                        # Let's fallback to link for galleries to avoid errors.
                        raise ValueError("Gallery not supported directly")

                    elif url.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                        await context.bot.send_photo(
                            chat_id=TELEGRAM_CHANNEL_ID,
                            photo=url,
                            caption=caption,
                            parse_mode='HTML'
                        )
                        sent = True
                    else:
                        # Text post or external link
                        if post.is_self:
                            text = post.selftext
                            if len(text) > 500:
                                text = text[:500] + "..."
                            msg_text = f"{caption}\n\n{text}"
                            await context.bot.send_message(
                                chat_id=TELEGRAM_CHANNEL_ID,
                                text=msg_text,
                                parse_mode='HTML',
                                disable_web_page_preview=True
                            )
                        else:
                            # Link post
                            msg_text = f"{caption}\nLink: {url}"
                            await context.bot.send_message(
                                chat_id=TELEGRAM_CHANNEL_ID,
                                text=msg_text,
                                parse_mode='HTML'
                            )
                        sent = True

                except Exception as e:
                    logging.warning(f"Media send failed for {post.id}: {e}. Fallback to link.")
                    # Fallback to link
                    await context.bot.send_message(
                        chat_id=TELEGRAM_CHANNEL_ID,
                        text=f"{caption}\n\n(Media failed to upload, see original link)",
                        parse_mode='HTML'
                    )
                    sent = True

                if sent:
                    success_count += 1

            except Exception as e:
                logging.error(f"Error processing post {post.id}: {e}")

        await status_msg.edit_text(f"Done. Successfully posted {success_count}/{len(posts)} items.")

    except Exception as e:
        await status_msg.edit_text(f"Error: {e}")

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set.")
        exit(1)

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('info', info))
    application.add_handler(CommandHandler('post', post_saved))

    print("Bot is running...")
    application.run_polling()
