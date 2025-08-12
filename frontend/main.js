// frontend/main.js (The Definitive V4 - Final Polish)

document.addEventListener('DOMContentLoaded', () => {
    // --- 1. INITIAL SETUP (No changes needed here) ---
    if (typeof qt === 'undefined' || typeof qt.webChannelTransport === 'undefined') {
        document.body.innerHTML = "<h1>Error: Backend connection failed.</h1>";
        return;
    }
    const inputBox = document.getElementById('input-box');
    const sendBtn = document.getElementById('send-btn');
    const micBtn = document.getElementById('mic-btn');
    const chatContainer = document.getElementById('chat-container');
    const terminalHeader = document.getElementById('terminal-header');
    const terminalContainer = document.getElementById('terminal-container');
    const terminalOutput = document.getElementById('terminal-output');
    const muteBtn = document.getElementById('mute-btn');
    const newChatBtn = document.getElementById('new-chat-btn'); // For future use
    let isMuted = false;

    new QWebChannel(qt.webChannelTransport, function (channel) {
        window.backend = channel.objects.backend_bridge;
    });

    // --- 2. EVENT LISTENERS (Mute button added) ---
    sendBtn.addEventListener('click', sendMessage);
    inputBox.addEventListener('keydown', (e) => {
        // Use Ctrl+Enter to send, Enter for new line
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    micBtn.addEventListener('click', () => { if (window.backend) window.backend.toggle_listening(); });
    terminalHeader.addEventListener('click', () => { terminalContainer.classList.toggle('hidden'); });
    inputBox.addEventListener('input', adjustInputHeight);

    muteBtn.addEventListener('click', () => {
        isMuted = !isMuted;
        muteBtn.classList.toggle('muted', isMuted);
        muteBtn.innerHTML = isMuted ? '&#x1f507;' : '&#x1f50a;';
        if (window.backend) {
            window.backend.toggle_mute(isMuted);
        }
    });

    // --- 3. HELPER FUNCTIONS ---
    function sendMessage() {
        const text = inputBox.value.trim();
        if (text && window.backend) {
            window.backend.process_user_query(text);
            inputBox.value = '';
            adjustInputHeight();
        }
    }
    function adjustInputHeight() {
        inputBox.style.height = 'auto';
        inputBox.style.height = (inputBox.scrollHeight) + 'px';
    }

    // --- 4. THE DEFINITIVE UI LOGIC ---

    /**
     * This is the function for the copy button on regular message bubbles.
     * It copies the raw text of the entire message.
     */
    window.copyFullMessage = (button) => {
        const messageContainer = button.closest('.message-container');
        const textToCopy = messageContainer.dataset.rawText;
        showCopyNotification(button, textToCopy);
    };

    /**
     * This is the function for the copy button INSIDE a code block.
     * The raw code is passed directly to it from the HTML onclick attribute.
     */
    window.copyCode = (button) => {
        // Find the <code> element within the same <pre> container
        const codeElement = button.parentElement.querySelector('code');
        if (codeElement) {
            const textToCopy = codeElement.textContent;
            showCopyNotification(button, textToCopy); // Use our shared helper
        } else {
            console.error("Could not find code element to copy.");
        }
    };

    /**
     * A shared helper function to show the "Copied!" notification.
     */
    function showCopyNotification(button, text) {
        navigator.clipboard.writeText(text).then(() => {
            const originalContent = button.innerHTML;
            button.innerHTML = '&#x2714;'; // Checkmark
            button.classList.add('copied');
            
            const notification = document.createElement('div');
            notification.className = 'copy-notification';
            notification.textContent = 'Copied to clipboard!';
            document.body.appendChild(notification);
            setTimeout(() => { notification.remove(); }, 2000);

            setTimeout(() => {
                button.innerHTML = originalContent;
                button.classList.remove('copied');
            }, 1500);
        });
    }

    /**
     * Creates and adds a new message to the chat window.
     */
    window.add_message = (role, htmlContent, rawText = '') => {
        const msgContainer = document.createElement('div');
        msgContainer.className = 'message-container';
        // Store the raw text for the general copy button
        msgContainer.dataset.rawText = rawText || htmlContent;

        if (role === 'system') {
            msgContainer.classList.add('system-message');
            msgContainer.innerHTML = `<i>${htmlContent}</i>`;
        } else {
            msgContainer.classList.add(role === 'user' ? 'user-message' : 'assistant-message');
            
            const bubble = document.createElement('div');
            bubble.className = `bubble ${role === 'user' ? 'user-bubble' : 'assistant-bubble'}`;
            bubble.innerHTML = htmlContent;
            
            // This actions container holds the general-purpose copy button
            const actions = document.createElement('div');
            actions.className = 'message-actions';
            const copyBtn = document.createElement('button');
            copyBtn.className = 'action-btn';
            copyBtn.innerHTML = '&#x1f4cb;'; // Clipboard emoji
            copyBtn.title = 'Copy full message';
            copyBtn.onclick = () => copyFullMessage(copyBtn);
            actions.appendChild(copyBtn);
            
            msgContainer.appendChild(bubble);
            msgContainer.appendChild(actions);
        }

        chatContainer.appendChild(msgContainer);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    };

    // --- 5. UNCHANGED FUNCTIONS ---
    window.add_terminal_output = (text) => {
        const line = document.createElement('div');
        line.textContent = text;
        terminalOutput.appendChild(line);
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    };
    window.update_mic_button = (state) => {
        micBtn.classList.remove('listening', 'thinking');
        if (state === 'listening') { micBtn.classList.add('listening'); micBtn.textContent = '...'; }
        else if (state === 'thinking') { micBtn.classList.add('thinking'); micBtn.textContent = '🧠'; }
        else { micBtn.textContent = '🎤'; }
    };
});