# Reddit Saved Media Downloader Bot

This is a **Telegram Userbot** that connects to your **Reddit Account**, fetches your Saved Posts, downloads the media (images/videos), and uploads them to a Telegram Chat/Channel.

## Features

- **Fetch from Reddit**: Access your saved posts directly via Reddit API.
- **Sequential Fetching**: Use `/from <index> <count>` to process batches (e.g., fetch 10 posts starting from the 50th newest).
- **Media Support**: Uses `yt-dlp` to download Videos (Reddit, RedGifs, etc.) and Images.
- **Large File Support**: Uses Pyrogram for uploads (up to 2GB).

## Setup

### 1. Requirements

- Python 3.8+
- A Reddit Account
- A Telegram Account

### 2. Get Credentials

#### Telegram API
1.  Go to [my.telegram.org](https://my.telegram.org/).
2.  Log in and go to **API Development Tools**.
3.  Copy `API_ID` and `API_HASH`.

#### Reddit API
1.  Go to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps).
2.  Click **Create Another App** (at the bottom).
3.  Select **script**.
4.  Name: `MyTelegramBot` (or anything).
5.  Redirect URI: `http://localhost:8080` (doesn't matter for script apps).
6.  Click **Create app**.
7.  Copy the **Client ID** (under the name) and **Client Secret**.

### 3. Installation

1.  Clone this repo.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure `config.py`:
    - Edit `config.py` and fill in your Telegram and Reddit credentials.

### 4. Usage

1.  Run the bot:
    ```bash
    python3 bot.py
    ```
2.  Log in to Telegram (enter phone number and OTP when prompted).

3.  **Commands**:
    Send these commands to your **Saved Messages** (or the chat where the bot is running):

    - **Fetch Newest 10 Saved Posts**:
      `/from 0 10`

    - **Fetch Posts #50 to #60**:
      `/from 50 10`

    - **Fetch and Send to Channel**:
      `/from 0 5 @MyArchiveChannel`

## Notes
- The "Index" is 0-based. 0 is the most recently saved post.
- Text posts are skipped.
- Some complex galleries or external links might fail to download if `yt-dlp` doesn't support them.
