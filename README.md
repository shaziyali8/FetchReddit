# Reddit Saved Posts Telegram Bot

A Python Telegram Bot (v20+) that posts your saved Reddit posts to a Telegram Channel.

## Features
- Fetches saved posts via PRAW (OAuth).
- Supports `/post from=X to=Y` command (max 20 items).
- Handles text, images, videos, and links.
- Fallback to Reddit link if media upload fails (e.g., >50MB).
- Skips deleted posts.
- Respects rate limits (sleeps between posts).

## Requirements
- Python 3.10+
- A Reddit Account (Client ID/Secret)
- A Telegram Bot (Token)
- A Telegram Channel (ID)

## Setup

1.  **Clone/Download** this repository.

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables**:
    - Copy `.env.example` to `.env`:
      ```bash
      cp .env.example .env
      ```
    - Edit `.env` and fill in your details:
        - `TELEGRAM_BOT_TOKEN`: From @BotFather.
        - `TELEGRAM_CHANNEL_ID`: Channel ID (e.g. `@my_channel` or `-100...`). **Add the bot as Admin**.
        - `REDDIT_...`: From https://www.reddit.com/prefs/apps (Create a "script" app).

4.  **Run**:
    ```bash
    python bot.py
    ```

## Usage

Send commands to the bot (in private chat):

- `/start`: Check if bot is alive.
- `/info`: Check Reddit connection status.
- `/post from=0 to=10`: Fetch the 10 most recent saved posts and send them to the channel.
- `/post from=10 to=20`: Fetch the next 10.

## Notes
- Reddit videos often have separate audio streams. This bot attempts to send the fallback URL provided by Reddit. If audio is missing or it fails, it sends the link.
- Large files (>50MB) are rejected by Telegram Bot API; the bot will link to them instead.
