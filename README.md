# Reddit Saved Posts to Telegram Extension

This is a Chrome Extension that runs on your Reddit "Saved" page. It extracts post URLs and titles, then sends them as clickable links to your Telegram Group or Channel.

## Features
- **In-Page Panel**: No need to click the extension icon. A small panel appears on the bottom right of Reddit pages.
- **Duplicate Prevention**: Remembers which posts (IDs) have already been sent to avoid spam.
- **Batch Sending**: Sends multiple links in a single message to respect rate limits.
- **Markdown Support**: Automatically extracts post titles and formats them as `[Title](URL)`.
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

1.  **Create a Telegram Bot**:
    - Chat with [@BotFather](https://t.me/BotFather) on Telegram.
    - Create a new bot and copy the **HTTP API Token**.

2.  **Get Your Group ID**:
    - Add your new bot to the desired Telegram Group.
    - Ensure the bot has permission to send messages.
    - To find the Group ID:
        - You can use a bot like [@userinfobot](https://t.me/userinfobot) or [@RawDataBot](https://t.me/RawDataBot) in the group.
        - Or, open the group in [Telegram Web](https://web.telegram.org/). The URL will look like `.../c/1234567890/...`. Your Group ID is usually `-100` followed by that number (e.g., `-1001234567890`).

3.  **Configure the Extension**:
    - Go to your Reddit Saved page: [https://www.reddit.com/user/me/saved/](https://www.reddit.com/user/me/saved/).
    - You should see the extension panel in the bottom right.
    - Click **Settings**.
    - Enter your **Bot Token** and **Group ID**.
    - Click **Save**.

## Usage

1.  **Scroll**: Scroll down on your Reddit Saved page to load the posts you want to forward.
2.  **Fetch**: Click **Fetch URLs** on the panel. It will scan the page for new posts.
3.  **Send**: Click **Send to Telegram**. The extension will format the links and send them to your group.
4.  Check your Telegram Group!

## Notes
- Works on both Old Reddit and New Reddit.
- If you clear your browser extension data, the "already sent" history will be lost.
