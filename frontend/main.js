document.addEventListener('DOMContentLoaded', () => {
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

    new QWebChannel(qt.webChannelTransport, function (channel) {
        window.backend = channel.objects.backend_bridge;
    });

    sendBtn.addEventListener('click', sendMessage);
    inputBox.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
    micBtn.addEventListener('click', () => { if (window.backend) window.backend.toggle_listening(); });
    terminalHeader.addEventListener('click', () => { terminalContainer.classList.toggle('hidden'); });

    function sendMessage() {
        const text = inputBox.value.trim();
        if (text && window.backend) {
            window.backend.process_user_query(text);
            inputBox.value = ''; adjustInputHeight();
        }
    }

    function adjustInputHeight() { inputBox.style.height = 'auto'; inputBox.style.height = (inputBox.scrollHeight) + 'px'; }
    inputBox.addEventListener('input', adjustInputHeight);
    
    window.add_message = (role, htmlContent) => {
        const msg = document.createElement('div');
        msg.className = 'message-container';
        if (role === 'system') { msg.classList.add('system-message'); msg.innerHTML = `<i>${htmlContent}</i>`; }
        else {
            msg.classList.add(role === 'user' ? 'user-message' : 'assistant-message');
            msg.innerHTML = `<div class='bubble ${role === 'user' ? 'user-bubble' : 'assistant-bubble'}'>${htmlContent}</div>`;
        }
        chatContainer.appendChild(msg);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    };
    window.add_terminal_output = (text) => {
        const line = document.createElement('div'); line.textContent = text;
        terminalOutput.appendChild(line); terminalOutput.scrollTop = terminalOutput.scrollHeight;
    };
    window.update_mic_button = (state) => {
        micBtn.classList.remove('listening', 'thinking');
        if (state === 'listening') { micBtn.classList.add('listening'); micBtn.textContent = '...'; }
        else if (state === 'thinking') { micBtn.classList.add('thinking'); micBtn.textContent = '🧠'; }
        else { micBtn.textContent = '🎤'; }
    };
    window.copyCode = (button, textToCopy) => {
        navigator.clipboard.writeText(textToCopy).then(() => {
            button.textContent = 'Copied!';
            setTimeout(() => { button.textContent = 'Copy'; }, 2000);
        });
    };
});