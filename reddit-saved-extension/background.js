// Listen for messages from content.js
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'sendToTelegram') {
        sendToTelegram(request.data)
            .then(result => sendResponse({ success: true, result }))
            .catch(error => sendResponse({ success: false, error: error.message }));

        // Return true to indicate we wish to send a response asynchronously
        return true;
    }
});

async function sendToTelegram({ botToken, chatId, message, parseMode }) {
    try {
        const body = {
            chat_id: chatId,
            text: message,
            disable_web_page_preview: true
        };

        if (parseMode) {
            body.parse_mode = parseMode;
        }

        const response = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (!data.ok) {
            throw new Error(data.description || 'Telegram API Error');
        }

        return data;
    } catch (error) {
        throw error;
    }
}
