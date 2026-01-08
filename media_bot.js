require('dotenv').config();
const { TelegramClient } = require('telegram');
const { StringSession } = require('telegram/sessions');
const { Api } = require('telegram/tl');
const input = require('input'); // npm install input
const fs = require('fs');
const path = require('path');
const YTDlpWrap = require('yt-dlp-wrap').default;

// Configuration
const API_ID = Number(process.env.API_ID);
const API_HASH = process.env.API_HASH;
const BOT_TOKEN = process.env.BOT_TOKEN;
const CHANNEL_ID = process.env.TELEGRAM_CHANNEL_ID;

// Session management
const SESSION_FILE = 'session.txt';
let stringSession = new StringSession('');

if (fs.existsSync(SESSION_FILE)) {
    stringSession = new StringSession(fs.readFileSync(SESSION_FILE, 'utf-8'));
}

// Initialize yt-dlp
const ytDlpBinaryPath = path.join(__dirname, 'yt-dlp');
const ytDlpWrap = new YTDlpWrap(ytDlpBinaryPath);

async function ensureYtDlp() {
    if (!fs.existsSync(ytDlpBinaryPath)) {
        console.log('Downloading yt-dlp binary...');
        await YTDlpWrap.downloadFromGithub(ytDlpBinaryPath);
        console.log('Downloaded yt-dlp.');
    }
}

async function downloadMedia(url) {
    const outputDir = path.join(__dirname, 'downloads');
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir);
    }

    // Output template: downloads/id.ext
    const outputTemplate = path.join(outputDir, '%(id)s.%(ext)s');

    try {
        console.log(`Downloading: ${url}`);
        // Get metadata first to check for playlist/entries
        const metadata = await ytDlpWrap.execPromise([
            url,
            '--dump-json',
            '--no-playlist' // We treat playlists as single entries or iterate?
                            // Python script handled entries. Let's do simple download.
        ]);

        // Actually download
        // We use execPromise to run the command
        await ytDlpWrap.execPromise([
            url,
            '-o', outputTemplate,
            '--no-warnings',
            '--max-filesize', '2000m'
        ]);

        // Find downloaded files
        // Since we don't know the exact extension, we list the dir and match ID?
        // Or we parse the JSON dump.
        // Let's rely on listing the directory for files that were just modified or match the pattern?
        // Simpler: List all files in downloads/ and upload them?
        // Or better: yt-dlp prints the filename.
        // Let's use a simpler approach: list files in downloads dir.

        const files = fs.readdirSync(outputDir).map(f => path.join(outputDir, f));
        return files;
    } catch (e) {
        console.error('Download error:', e.message);
        return [];
    }
}

(async () => {
    await ensureYtDlp();

    console.log("Starting Telegram Bot...");
    const client = new TelegramClient(stringSession, API_ID, API_HASH, {
        connectionRetries: 5,
    });

    await client.start({
        botAuthToken: BOT_TOKEN,
    });

    // Save session
    fs.writeFileSync(SESSION_FILE, client.session.save());

    console.log("Bot connected.");

    // Resolve Channel ID (handle @username or -100 ID)
    let entity;
    try {
        // If it looks like an int, parse it.
        const id = isNaN(CHANNEL_ID) ? CHANNEL_ID : BigInt(CHANNEL_ID);
        entity = await client.getEntity(id);
    } catch (e) {
        console.error("Could not find channel:", e);
        return;
    }

    console.log(`Monitoring ${entity.title || CHANNEL_ID}...`);

    while (true) {
        try {
            // Get last 10 messages
            const messages = await client.getMessages(entity, { limit: 10 });

            for (const message of messages) {
                if (!message.text) continue;

                // Check criteria: "New Saved Posts" and not "✅"
                if (message.text.includes("New Saved Posts:") && !message.text.includes("✅")) {
                    console.log(`Processing message ${message.id}...`);

                    // Extract URLs
                    const urlRegex = /(https?:\/\/(?:www\.)?(?:reddit\.com|redd\.it)\/[^\s]+)/g;
                    const urls = message.text.match(urlRegex);

                    if (!urls) continue;

                    const filesToUpload = [];

                    for (const url of urls) {
                        const files = await downloadMedia(url);
                        filesToUpload.push(...files);
                    }

                    // Upload
                    for (const file of filesToUpload) {
                        if (fs.existsSync(file)) {
                            console.log(`Uploading ${file}...`);
                            try {
                                await client.sendFile(entity, {
                                    file: file,
                                });
                                fs.unlinkSync(file); // Delete after upload
                            } catch (err) {
                                console.error("Upload failed:", err);
                            }
                        }
                    }

                    // Mark as processed
                    // GramJS editMessage
                    const newText = message.text + "\n\n✅ Processed & Downloaded";
                    try {
                        await client.editMessage(entity, {
                            message: message.id,
                            text: newText,
                            linkPreview: false
                        });
                        console.log("Message marked as processed.");
                    } catch (err) {
                        console.error("Failed to edit message:", err);
                    }

                    // Cleanup downloads dir
                    const downloadDir = path.join(__dirname, 'downloads');
                    if (fs.existsSync(downloadDir)) {
                         const remaining = fs.readdirSync(downloadDir);
                         if (remaining.length === 0) fs.rmdirSync(downloadDir);
                    }
                }
            }
        } catch (e) {
            console.error("Error in loop:", e);
        }

        // Sleep 15s
        await new Promise(r => setTimeout(r, 15000));
    }
})();
