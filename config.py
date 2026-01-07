import os

# Telegram Bot Configuration
# Get API_ID and API_HASH from https://my.telegram.org/
# These are required for Pyrogram (MTProto) to work.
API_ID = os.getenv("API_ID", "YOUR_API_ID_HERE")
API_HASH = os.getenv("API_HASH", "YOUR_API_HASH_HERE")

# Get BOT_TOKEN from @BotFather
# This script runs as a Standard Telegram Bot.
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Your Telegram User ID (Integer).
# Only this user can control the bot.
# You can get this from @userinfobot
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Session name (internal use for Pyrogram)
SESSION_NAME = os.getenv("SESSION_NAME", "my_bot_session")

# Reddit API Configuration
# Get these from https://www.reddit.com/prefs/apps
# Create a "script" app.
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "YOUR_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "YOUR_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "YOUR_PASSWORD")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "android:com.example.mybot:v1.0.0 (by /u/YOUR_USERNAME)")
