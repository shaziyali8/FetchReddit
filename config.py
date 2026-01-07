import os

# You can either set these environment variables or edit the string values directly below.
# API_ID and API_HASH can be obtained from https://my.telegram.org/
#
# NOTE: This script runs as a "Userbot" (using your personal account) to access your
# "Saved Messages" history. Standard Bot API tokens (from BotFather) CANNOT access
# a user's Saved Messages. Therefore, NO BOT_TOKEN is required/used here.
API_ID = os.getenv("API_ID", "YOUR_API_ID_HERE")
API_HASH = os.getenv("API_HASH", "YOUR_API_HASH_HERE")

# The session name for the Pyrogram client.
# This will create a file named 'my_account.session' (or whatever value you set here)
# in the current directory. This file stores your login session (auth token), so you
# only need to log in once (via phone number + OTP).
SESSION_NAME = os.getenv("SESSION_NAME", "my_account")

# Reddit API Configuration
# Get these from https://www.reddit.com/prefs/apps
# Create a "script" app.
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "YOUR_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "YOUR_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "YOUR_PASSWORD")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "android:com.example.mybot:v1.0.0 (by /u/YOUR_USERNAME)")
