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
# This will create a file named 'my_account.session'.
SESSION_NAME = os.getenv("SESSION_NAME", "my_account")
