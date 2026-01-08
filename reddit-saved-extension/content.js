// State
let newUrls = [];
let newIds = [];
let config = {
    botToken: '',
    chatId: ''
};

// --- Initialization ---

function init() {
    console.log("Reddit Saved Extension: Content script loaded...");

    // Check initially
    attemptInjection();

    // Check periodically for SPA navigation (Reddit is an SPA)
    setInterval(attemptInjection, 2000);
}

function attemptInjection() {
    if (document.getElementById('rst-panel')) return; // Already injected

    // Optional: Check URL to be sure we are on a saved page (if manifest is too broad)
    if (!window.location.href.includes('/saved')) return;

    createPanel();
    loadConfig();
}

function createPanel() {
    const panel = document.createElement('div');
    panel.id = 'rst-panel';
    panel.innerHTML = `
        <h3>Reddit -> Telegram</h3>

        <div id="rst-main-view">
            <button id="rst-fetch-btn" class="rst-btn">Fetch URLs</button>
            <button id="rst-send-btn" class="rst-btn" disabled>Send to Telegram</button>
            <div id="rst-status">Ready. Scroll to load posts first.</div>
            <button id="rst-settings-btn" class="rst-btn rst-secondary" style="margin-top: 10px;">Settings</button>
        </div>

        <div id="rst-settings-view" class="hidden">
            <input type="text" id="rst-bot-token" class="rst-input" placeholder="Bot Token">
            <input type="text" id="rst-chat-id" class="rst-input" placeholder="Chat ID">
            <button id="rst-save-btn" class="rst-btn">Save</button>
            <button id="rst-cancel-btn" class="rst-btn rst-secondary">Back</button>
        </div>
    `;
    document.body.appendChild(panel);

    // Event Listeners
    document.getElementById('rst-fetch-btn').addEventListener('click', fetchUrls);
    document.getElementById('rst-send-btn').addEventListener('click', sendToTelegram);
    document.getElementById('rst-settings-btn').addEventListener('click', showSettings);
    document.getElementById('rst-save-btn').addEventListener('click', saveConfig);
    document.getElementById('rst-cancel-btn').addEventListener('click', hideSettings);
}

// --- Configuration Logic ---

function loadConfig() {
    chrome.storage.local.get(['botToken', 'chatId'], (result) => {
        if (result.botToken) config.botToken = result.botToken;
        if (result.chatId) config.chatId = result.chatId;

        // Pre-fill inputs
        document.getElementById('rst-bot-token').value = config.botToken || '';
        document.getElementById('rst-chat-id').value = config.chatId || '';

        if (!config.botToken || !config.chatId) {
            updateStatus('Please configure Bot Settings first.');
        }
    });
}

function saveConfig() {
    const token = document.getElementById('rst-bot-token').value.trim();
    const chatId = document.getElementById('rst-chat-id').value.trim();

    if (!token || !chatId) {
        alert('Both fields are required.');
        return;
    }

    chrome.storage.local.set({ botToken: token, chatId: chatId }, () => {
        config.botToken = token;
        config.chatId = chatId;
        hideSettings();
        updateStatus('Settings saved.');
    });
}

function showSettings() {
    document.getElementById('rst-main-view').classList.add('hidden');
    document.getElementById('rst-settings-view').classList.remove('hidden');
}

function hideSettings() {
    document.getElementById('rst-settings-view').classList.add('hidden');
    document.getElementById('rst-main-view').classList.remove('hidden');
}

// --- Fetch Logic ---

function fetchUrls() {
    if (!config.botToken || !config.chatId) {
        alert('Please configure Bot Token and Chat ID in Settings.');
        showSettings();
        return;
    }

    updateStatus('Scanning...');

    // Find all links containing /comments/
    const links = Array.from(document.querySelectorAll('a[href*="/comments/"]'));
    const uniquePosts = new Map(); // ID -> URL

    links.forEach(link => {
        const href = link.href;
        const match = href.match(/\/comments\/([a-zA-Z0-9]+)\//);
        if (match) {
            const id = match[1];
            // Store the shortest/cleanest URL found for this ID
            if (!uniquePosts.has(id)) {
                uniquePosts.set(id, href.split('?')[0]); // Remove query params
            }
        }
    });

    if (uniquePosts.size === 0) {
        updateStatus('No posts found. Scroll down?');
        return;
    }

    // Filter against storage
    chrome.storage.local.get(['sentIds'], (result) => {
        const sentIds = new Set(result.sentIds || []);
        newUrls = [];
        newIds = [];

        for (const [id, url] of uniquePosts) {
            if (!sentIds.has(id)) {
                newUrls.push(url);
                newIds.push(id);
            }
        }

        if (newUrls.length > 0) {
            updateStatus(`Found ${newUrls.length} new posts.`);
            document.getElementById('rst-send-btn').disabled = false;
        } else {
            updateStatus('No new posts found (all already sent).');
            document.getElementById('rst-send-btn').disabled = true;
        }
    });
}

// --- Send Logic ---

async function sendToTelegram() {
    const btn = document.getElementById('rst-send-btn');
    btn.disabled = true;
    updateStatus('Sending...');

    // Chunk URLs to fit Telegram 4096 char limit
    // A safe chunk size is roughly 30-40 URLs per message
    const chunkSize = 20;
    const chunks = [];

    for (let i = 0; i < newUrls.length; i += chunkSize) {
        chunks.push(newUrls.slice(i, i + chunkSize));
    }

    let success = true;

    for (const chunk of chunks) {
        const message = "New Saved Posts:\n\n" + chunk.join('\n');

        try {
            // Send message to background script to bypass CSP
            const response = await new Promise((resolve, reject) => {
                chrome.runtime.sendMessage({
                    action: 'sendToTelegram',
                    data: {
                        botToken: config.botToken,
                        chatId: config.chatId,
                        message: message
                    }
                }, (response) => {
                    if (chrome.runtime.lastError) {
                        reject(new Error(chrome.runtime.lastError.message));
                    } else if (response && response.success) {
                        resolve(response.result);
                    } else {
                        reject(new Error(response ? response.error : 'Unknown Error'));
                    }
                });
            });

        } catch (err) {
            console.error('Telegram/Background Error:', err);
            updateStatus(`Error: ${err.message}`);
            success = false;
            break;
        }
    }

    if (success) {
        // Mark IDs as sent
        chrome.storage.local.get(['sentIds'], (result) => {
            const currentSent = result.sentIds || [];
            const updatedSent = [...new Set([...currentSent, ...newIds])]; // Merge and unique

            chrome.storage.local.set({ sentIds: updatedSent }, () => {
                updateStatus(`Successfully sent ${newUrls.length} posts!`);
                newUrls = [];
                newIds = [];
            });
        });
    } else {
        btn.disabled = false; // Allow retry
    }
}

function updateStatus(msg) {
    document.getElementById('rst-status').innerText = msg;
}

// Run
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
