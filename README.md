# Telegram Saved Messages Media Fetcher

This is a **Telegram Userbot** designed to manage and organize media you have saved in your **Saved Messages**.

It is particularly useful if you save posts (e.g., Reddit videos/images forwarded from other bots/channels) to your Saved Messages and want to bulk-forward them to a specific archive channel.

## Features

- **Fetch from specific ID**: Resume forwarding from where you left off (e.g., `/from 50`).
- **Target Channel**: Forward media to a specific channel (e.g., `/from 50 @MyArchive`).
- **Large File Support**: Uses Pyrogram (MTProto) to handle files up to 2GB efficiently.
- **No Reddit Login Required**: This bot operates entirely within Telegram.

## FAQ

### 1. Where do I add my Reddit account details?
**You don't.**
This bot does **not** connect to Reddit. It works on the assumption that you have *already* forwarded Reddit posts (or any media) into your **Telegram Saved Messages** (the "Saved Messages" chat with yourself).
- **Source**: Your Telegram "Saved Messages".
- **Destination**: The chat where you run the command (or the specified target channel).

### 2. Why is there no Bot Token?
Standard Telegram Bots (created via BotFather) **cannot access your personal Saved Messages**.
To read your history, this script acts as a **Userbot**. It logs in as *you* (using your account credentials).
- **Required**: `API_ID` and `API_HASH` (from [my.telegram.org](https://my.telegram.org/)).
- **Not Required**: Bot Token.

### 3. What is `SESSION_NAME`?
This is simply the name of the file where Pyrogram saves your login session (e.g., `my_account.session`).
- When you run the script for the first time, it will ask for your **Phone Number** and **Login Code** (OTP).
- It saves this login data into `my_account.session`.
- Future runs will use this file to log in automatically without asking for code again.

## Setup & Usage

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure**:
    - Open `config.py`.
    - Enter your `API_ID` and `API_HASH` (get them from [https://my.telegram.org/](https://my.telegram.org/) -> API Development Tools).

3.  **Run**:
    ```bash
    python3 bot.py
    ```
    *Follow the on-screen prompts to log in.*

4.  **Commands (in Telegram)**:
    Send these commands to your **Saved Messages** (or any chat where you are running the bot):

    - **Check Info**:
      `/info`

    - **Start Fetching**:
      `/from <message_id> [target_channel]`

      *Examples:*
      - `/from 100` -> Fetches media from Message ID 100 up to the latest, forwarding to the current chat.
      - `/from 100 @MyRedditArchive` -> Fetches from ID 100 and forwards to the channel `@MyRedditArchive`.
