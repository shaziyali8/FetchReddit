import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from config import API_ID, API_HASH, SESSION_NAME

# Initialize the Client (Userbot)
app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)

@app.on_message(filters.me & filters.command("start", prefixes="/"))
async def start_handler(client, message):
    """
    Handles the /start command.
    """
    await message.edit_text(
        "**Reddit Saved Posts Fetcher**\n\n"
        "This bot fetches media (e.g., Reddit posts) from your Telegram Saved Messages and forwards it here.\n\n"
        "**Commands:**\n"
        "`/info` - Show information.\n"
        "`/from <id>` - Fetch media starting from the specified Message ID.\n\n"
        "Example: `/from 50`"
    )

@app.on_message(filters.me & filters.command("info", prefixes="/"))
async def info_handler(client, message):
    """
    Handles the /info command.
    """
    await message.edit_text(
        "**Bot Information**\n\n"
        "Library: Pyrogram (MTProto)\n"
        "Function: Fetches Saved Messages media (Reddit posts) and forwards it.\n"
        "Support: Large files (up to 2GB), Real-time updates.\n\n"
        "**Usage:**\n"
        "Use `/from <n>` to start fetching from a specific Message ID.\n"
        "This allows you to resume fetching or fetch only new posts.\n"
        "e.g., If you have processed up to ID 90, use `/from 91` next time."
    )

async def copy_message_safe(msg, target_chat_id):
    """
    Copies a message handling FloodWait.
    """
    while True:
        try:
            await msg.copy(target_chat_id)
            return True
        except FloodWait as e:
            print(f"FloodWait hit. Sleeping for {e.value} seconds.")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Error copying message {msg.id}: {e}")
            return False

@app.on_message(filters.me & filters.command("from", prefixes="/"))
async def fetch_handler(client, message: Message):
    """
    Handles the /from command to fetch messages.
    """
    # Parse the argument
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.edit_text("Usage: `/from <message_id>`\nExample: `/from 50`")
            return

        start_id = int(args[1])
        if start_id < 1:
            await message.edit_text("Message ID must be positive.")
            return
    except ValueError:
        await message.edit_text("Invalid ID. Please provide an integer.")
        return

    # Send status message
    status_msg = await message.edit_text(f"Initializing fetch from ID {start_id}...")

    try:
        # Get the latest message ID from Saved Messages ("me") to know where to stop
        history = []
        async for msg in client.get_chat_history("me", limit=1):
            history.append(msg)

        if not history:
            await status_msg.edit_text("Saved Messages is empty.")
            return

        latest_id = history[0].id

        if start_id > latest_id:
            await status_msg.edit_text(f"Start ID {start_id} is greater than the latest message ID ({latest_id}).")
            return

        await status_msg.edit_text(f"Fetching from ID {start_id} to {latest_id}...\nTarget: This chat")

        processed_ids = 0
        media_count = 0
        batch_size = 100 # Fetch in batches of 100 for efficiency

        target_chat_id = message.chat.id

        # Iterate from start_id to latest_id
        for i in range(start_id, latest_id + 1, batch_size):
            # Calculate batch range
            end_batch = min(i + batch_size, latest_id + 1)
            batch_ids = list(range(i, end_batch))

            # Fetch messages by IDs with FloodWait handling
            messages = None
            while messages is None:
                try:
                    messages = await client.get_messages("me", batch_ids)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception as e:
                    await status_msg.edit_text(f"Error fetching messages: {e}")
                    return

            # Allow for single message return if batch is 1
            if not isinstance(messages, list):
                messages = [messages]

            for msg in messages:
                # msg can be None or empty if the ID doesn't exist (deleted message)
                if not msg or msg.empty:
                    continue

                # Check if message has media
                # We check for various media types. msg.media is truthy if any media is present.
                if msg.media:
                    success = await copy_message_safe(msg, target_chat_id)
                    if success:
                        media_count += 1

            # Update progress
            current_progress = min(end_batch, latest_id)
            try:
                await status_msg.edit_text(
                    f"**Fetching...**\n"
                    f"Range: {start_id} - {latest_id}\n"
                    f"Current: {current_progress}\n"
                    f"Media Forwarded: {media_count}"
                )
            except FloodWait as e:
                # If we get floodwaited on edit, just wait and skip this update
                await asyncio.sleep(e.value)
            except Exception:
                # Ignore other edit errors (e.g., "Message not modified")
                pass

        await status_msg.edit_text(
            f"**Fetch Complete!**\n"
            f"Range Scanned: {start_id} - {latest_id}\n"
            f"Total Media Forwarded: {media_count}"
        )

    except Exception as e:
        await status_msg.edit_text(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    print("Starting Userbot...")
    app.run()
