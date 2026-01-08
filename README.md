# Reddit Saved Posts to Telegram Extension

This is a Chrome Extension that runs on your Reddit "Saved" page. It extracts post URLs and sends them to your Telegram bot.

## Features
- **In-Page Panel**: No need to click the extension icon. A small panel appears on the bottom right of Reddit pages.
- **Duplicate Prevention**: Remembers which posts (IDs) have already been sent to avoid spam.
- **Batch Sending**: Sends multiple URLs in a single message to respect rate limits.
- **Privacy**: Runs entirely in your browser. Tokens are stored in your browser's local storage.

## Installation

1.  **Download the Extension**:
    - Clone or download this repository.
    - Ensure you have the folder `reddit-saved-extension` containing `manifest.json`.

2.  **Load in Chrome**:
    - Open Chrome and go to `chrome://extensions/`.
    - Enable **Developer mode** (top right).
    - Click **Load unpacked**.
    - Select the `reddit-saved-extension` folder.

## Configuration

1.  **Get Telegram Credentials**:
    - **Bot Token**: Chat with [@BotFather](https://t.me/BotFather) on Telegram to create a new bot and get the HTTP API Token.
    - **Chat ID**: Chat with [@userinfobot](https://t.me/userinfobot) to get your numeric User ID.

2.  **Configure the Extension**:
    - Go to your Reddit Saved page: [https://www.reddit.com/user/YOUR_USERNAME/saved/](https://www.reddit.com/user/me/saved/).
    - You should see a panel in the bottom right corner.
    - Click **Settings**.
    - Enter your **Bot Token** and **Chat ID**.
    - Click **Save**.

## Usage

1.  **Scroll**: Scroll down on your Reddit Saved page to load as many posts as you want to process. (The extension only sees what is loaded in the DOM).
2.  **Fetch**: Click **Fetch URLs** on the panel. It will tell you how many *new* posts it found.
3.  **Send**: Click **Send to Telegram**.
4.  Check your Telegram!

## Notes
- Works on both Old Reddit and New Reddit (as long as the URL structure contains `/comments/id/`).
- If you clear your browser extension data, the "already sent" history will be lost.

---

# Part 2: Media Downloader Bot (Python)

To automatically download the videos/images from the links sent by the extension, run this Python script.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: You also need `ffmpeg` installed on your system for `yt-dlp` to merge video/audio streams.*

2.  **Configuration**:
    - Copy `.env.example` to `.env`:
      ```bash
      cp .env.example .env
      ```
    - Fill in:
      - `API_ID`, `API_HASH` (from my.telegram.org)
      - `BOT_TOKEN` (Same as used in Extension)
      - `TELEGRAM_CHANNEL_ID` (Same as used in Extension)

3.  **Run**:
    ```bash
    python media_bot.py
    ```
    The bot will poll the channel every 15 seconds. When it sees a message from the Extension ("New Saved Posts:"), it will download the media (using `yt-dlp`) and upload it to the channel, then mark the text message as "✅ Processed".
