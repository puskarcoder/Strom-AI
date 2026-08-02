console.log("NEW SCRIPT LOADED");
const sendBtn = document.getElementById("send");
const input = document.getElementById("message");
const chatBox = document.getElementById("chat-box");
const newChatBtn = document.getElementById("new-chat");

let currentChatId = null;
let voiceMode = false;

// ----------------------
// Create New Chat
// ----------------------

async function createNewChat() {

    try {

        const response = await fetch("/new-chat", {
            method: "POST"
        });

        const data = await response.json();

        currentChatId = data.chat_id;

        console.log("Current Chat:", currentChatId);

        chatBox.innerHTML = `
        <div class="bot-message">
            <div class="avatar ai">AI</div>
            <div class="message">
                👋 Hello! I'm Strom AI.<br>
                Ask me anything.
            </div>
        </div>
        `;
        loadHistory();

    } catch (err) {

        console.log(err);

    }

}

// ----------------------
// Send Message
// ----------------------

async function sendMessage() {

    const message = input.value.trim();

    if (message === "") return;

    chatBox.innerHTML += `
        <div class="user-message">
            <div class="message">${message}</div>
            <div class="avatar user">You</div>
        </div>
    `;

    input.value = "";

    chatBox.scrollTop = chatBox.scrollHeight;

    try {

        const response = await fetch("/stream-chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                message: message,
                chat_id: currentChatId

            })

        });

        const reader = response.body.getReader();

        const decoder = new TextDecoder();
        const botMessage = document.createElement("div");

        botMessage.className = "bot-message";

        botMessage.innerHTML = `
    <div class="avatar ai">AI</div>
    <div class="message"></div>
`;

        chatBox.appendChild(botMessage);

        const messageDiv = botMessage.querySelector(".message");

        while (true) {

            const { done, value } = await reader.read();

            if (done) break;

            const chunk = decoder.decode(value);

            messageDiv.dataset.raw = (messageDiv.dataset.raw || "") + chunk;

            messageDiv.innerHTML = marked.parse(messageDiv.dataset.raw);
            console.log(messageDiv.dataset.raw);

            hljs.highlightAll();

            chatBox.scrollTop = chatBox.scrollHeight;
        }
        console.log("Voice Mode:", voiceMode);
        console.log("Reply:", messageDiv.innerText);

        if (voiceMode) {

            const reply = messageDiv.innerText;

            const speech = new SpeechSynthesisUtterance(reply);

            speech.lang = "en-US";
            speech.rate = 1;
            speech.pitch = 1;

            window.speechSynthesis.speak(speech);

            voiceMode = false;
        }
    }
    catch (error) {

        chatBox.innerHTML += `
            <div class="bot-message">
                <div class="avatar ai">AI</div>
                <div class="message">
                    Something went wrong.
                </div>
            </div>
        `;

    }

}

// ----------------------
// Events
// ----------------------

sendBtn.addEventListener("click", sendMessage);

input.addEventListener("keydown", function (e) {

    if (e.key === "Enter") {

        sendMessage();

    }

});

newChatBtn.addEventListener("click", createNewChat);

// First Chat
createNewChat();

async function openChat(chatId) {

    console.log("Opening Chat:", chatId);

    currentChatId = chatId;

    const response = await fetch(`/chat/${chatId}`);

    const messages = await response.json();

    chatBox.innerHTML = "";

    messages.forEach(msg => {

        if (msg.role === "user") {

            chatBox.innerHTML += `
                <div class="user-message">
                    <div class="message">${msg.message}</div>
                    <div class="avatar user">You</div>
                </div>
            `;

        } else {

            chatBox.innerHTML += `
    <div class="bot-message">
        <div class="avatar ai">AI</div>
        <div class="message">
            ${marked.parse(msg.message)}
        </div>
    </div>
`;

        }

    });

    chatBox.scrollTop = chatBox.scrollHeight;

}
async function loadHistory() {

    const response = await fetch("/history");

    const chats = await response.json();

    const historyList = document.getElementById("history-list");

    historyList.innerHTML = "";

    chats.forEach(chat => {

        const div = document.createElement("div");

        div.className = "chat-item";

        div.dataset.id = chat.id;

        div.innerHTML = `
    <span>${chat.title}</span>
    <button class="delete-btn" data-id="${chat.id}">🗑️</button>
`;
        div.addEventListener("click", () => {

            console.log("Clicked:", chat.id);

            openChat(chat.id);

        });

        historyList.appendChild(div);
        const deleteBtn = div.querySelector(".delete-btn");

        deleteBtn.addEventListener("click", async (e) => {

            e.stopPropagation();

            const response = await fetch(`/delete-chat/${chat.id}`, {
                method: "DELETE"
            });

            const result = await response.json();

            if (result.success) {

                loadHistory();

                chatBox.innerHTML = "";

            }

        });

    });
}
const micBtn = document.getElementById("mic");
const messageInput = document.getElementById("message");

if ("webkitSpeechRecognition" in window) {

    const recognition = new webkitSpeechRecognition();

    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    micBtn.addEventListener("click", () => {
        recognition.start();
    });

    recognition.onresult = (event) => {

        voiceMode = true;

        const text = event.results[0][0].transcript;

        messageInput.value = text;

        sendMessage();

    };

    recognition.onerror = (event) => {
        console.log(event.error);
    };

} else {
    alert("Speech Recognition is not supported in your browser.");
}
const attachBtn = document.getElementById("attach");
const fileInput = document.getElementById("fileInput");

attachBtn.addEventListener("click", () => {
    fileInput.click();
});

fileInput.addEventListener("change", () => {

    const file = fileInput.files[0];

    if (!file) return;

    // যদি Image হয়
    if (file.type.startsWith("image/")) {

        const reader = new FileReader();

        reader.onload = function (e) {

            chatBox.innerHTML += `
                <div class="user-message">
                    <img src="${e.target.result}" class="preview-image">
                    <div class="message">${file.name}</div>
                    <div class="avatar user">You</div>
                </div>
            `;

            chatBox.scrollTop = chatBox.scrollHeight;
            const formData = new FormData();

            formData.append("image", file);

            fetch("/upload-image", {
                method: "POST",
                body: formData
            })
                .then(res => res.json())
                .then(data => {

                    console.log("Image API Response:", data);

if (!data.success) {
    alert(data.error || data.message || "Unknown error");
    return;
}

chatBox.innerHTML += `
<div class="bot-message">
    <div class="avatar ai">AI</div>
    <div class="message">
        ${data.reply}
    </div>
</div>
`;

chatBox.scrollTop = chatBox.scrollHeight;

                    chatBox.scrollTop = chatBox.scrollHeight;

                })
                .catch(err => {
                    console.error("Upload Error:", err);
                });

        };

        reader.readAsDataURL(file);

    }

    // যদি অন্য File হয়
    else {

        chatBox.innerHTML += `
            <div class="user-message">
                <div class="message">📄 ${file.name}</div>
                <div class="avatar user">You</div>
            </div>
        `;

        chatBox.scrollTop = chatBox.scrollHeight;

    }

});