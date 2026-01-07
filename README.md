# Reddit Saved Posts Telegram Bot (Pyrogram Edition)

A Telegram Bot that fetches your saved Reddit posts and forwards them to a Telegram Channel using **Pyrogram**.
This version supports uploading **large files (up to 2GB)** by downloading them locally first using `yt-dlp`.

## Features
- **Pyrogram (MTProto)**: Supports 2GB file uploads.
- **Media Support**: Uses `yt-dlp` to download high-quality videos/images from Reddit, RedGifs, etc.
- **PRAW Integration**: Fetches your private "Saved" posts.
- **Commands**: `/post from=X to=Y` to control batching.

## Requirements
- Python 3.8+
- `ffmpeg` (Required for yt-dlp video merging)
- A Reddit Account (Client ID/Secret)
- A Telegram Bot (Token, API ID, Hash)

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    - Copy `.env.example` to `.env`:
      ```bash
      cp .env.example .env
      ```
    - **Telegram**:
        - `API_ID` & `API_HASH`: From [my.telegram.org](https://my.telegram.org).
        - `BOT_TOKEN`: From @BotFather.
        - `OWNER_ID`: Your numeric User ID (from @userinfobot).
        - `TELEGRAM_CHANNEL_ID`: Channel ID (e.g. `@my_channel` or `-100...`). **Add the bot as Admin**.
    - **Reddit**:
        - Credentials from [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps).

3.  **Run**:
    ```bash
    python bot.py
    ```

## Usage

Send commands to the bot (in private chat):

- `/info`: Check status.
- `/post from=0 to=10`: Fetch 10 most recent saved posts.
- `/post from=50 to=55`: Fetch posts #50 to #55.

## Notes
- Ensure `ffmpeg` is installed on your system (`apt install ffmpeg` or `brew install ffmpeg`), or `yt-dlp` may fail to merge video+audio streams for Reddit videos.
- Downloaded files are temporarily stored in `downloads/` and deleted after upload.
