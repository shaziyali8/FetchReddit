# Reddit Saved Media Downloader (Telegram Bot)

This is a **Telegram Bot** (configured to run on your server/computer) that automates downloading your **Reddit Saved Posts** and uploading them to a Telegram Channel or Chat.

It uses **Pyrogram** (MTProto) to support uploading files up to **2GB**, surpassing the standard Bot API limit of 50MB.

## Features

- **Personal Bot**: Restricted to your Telegram User ID.
- **Fetch Saved Posts**: Connects to your Reddit account via PRAW.
- **Media Downloader**: Uses `yt-dlp` to download Videos (Reddit, RedGifs, etc.) and Images.
- **Large File Support**: Uploads large videos directly to Telegram.
- **Channel Support**: Send media directly to an Archive Channel.

## Setup

### 1. Requirements

- Python 3.8+
- **ffmpeg** (Required for `yt-dlp` to merge video/audio).
    - Ubuntu: `sudo apt install ffmpeg`
    - Mac: `brew install ffmpeg`
- A Reddit Account
- A Telegram Account (to create the bot and control it)

### 2. Get Credentials

#### Telegram Bot & API
1.  **Bot Token**: Message [@BotFather](https://t.me/BotFather) on Telegram, create a new bot, and copy the **HTTP API Token**.
2.  **API ID & Hash**: Go to [my.telegram.org](https://my.telegram.org/), log in, and copy `API_ID` and `API_HASH` from "API Development Tools".
3.  **Owner ID**: Message [@userinfobot](https://t.me/userinfobot) on Telegram and copy your **ID** (Integer).

#### Reddit API
1.  Go to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps).
2.  Create a **script** app.
3.  Copy the **Client ID** and **Client Secret**.

### 3. Installation

1.  Clone this repo.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure `config.py`:
    - Edit `config.py` and fill in all the variables (Bot Token, Owner ID, Reddit Creds, etc.).

### 4. Usage

1.  Run the bot:
    ```bash
    python3 bot.py
    ```

2.  **Start the Bot**:
    - Open your bot in Telegram and send `/start`.
    - It should greet you. If it says "Unauthorized", check your `OWNER_ID` in config.

3.  **Forward to Channel**:
    - **Important**: Add your Bot as an **Administrator** in the target channel so it can post messages.
    - Command: `/from <start_index> <count> @MyArchiveChannel`

    **Examples**:
    - `/from 0 10 @MyRedditArchive` (Fetch 10 newest saved posts and send to channel)
    - `/from 50 5` (Fetch 5 posts starting from index 50 and send to the current chat)

## Notes
- The bot deletes downloaded files from your server after uploading to save space.
- The `SESSION_NAME` in `config.py` is for the bot's internal session file.
