/**
 * AI Enquiry Assistant – Frontend Chat Logic
 * Handles message sending, receiving, session management,
 * quick replies, typing indicators, and leads modal.
 */

// ─── Configuration ──────────────────────────────────────────
const API_BASE = window.location.origin;
const SESSION_KEY = "teched_session_id";

// ─── State ──────────────────────────────────────────────────
let sessionId = localStorage.getItem(SESSION_KEY) || generateUUID();
localStorage.setItem(SESSION_KEY, sessionId);

let isWaitingForResponse = false;

// ─── DOM Elements ───────────────────────────────────────────
const chatMessages = document.getElementById("chatMessages");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const quickReplies = document.getElementById("quickReplies");
const leadsBtn = document.getElementById("leadsBtn");
const leadsBadge = document.getElementById("leadsBadge");
const clearBtn = document.getElementById("clearBtn");
const leadsModal = document.getElementById("leadsModal");
const closeModal = document.getElementById("closeModal");
const leadsContent = document.getElementById("leadsContent");

// ─── Utility Functions ──────────────────────────────────────

function generateUUID() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
}

function getCurrentTime() {
    return new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
    });
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Convert simple markdown to HTML:
 *  **bold** → <strong>bold</strong>
 *  • list items
 *  Newlines → paragraphs
 */
function renderMarkdown(text) {
    // Escape HTML first
    let html = escapeHtml(text);

    // Bold: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Split into paragraphs on double newlines
    const paragraphs = html.split(/\n\n+/);
    html = paragraphs
        .map((p) => {
            // Check if it's a list
            const lines = p.split("\n");
            const isList = lines.every(
                (l) => l.trim().startsWith("•") || l.trim().startsWith("-") || l.trim().startsWith("*") || l.trim() === ""
            );

            if (isList && lines.some((l) => l.trim())) {
                const items = lines
                    .filter((l) => l.trim())
                    .map((l) => `<li>${l.replace(/^[\s•\-\*]+/, "").trim()}</li>`)
                    .join("");
                return `<ul>${items}</ul>`;
            }

            // Check for numbered list
            const isNumberedList = lines.every(
                (l) => /^\s*\d+[\.\)]\s/.test(l) || l.trim() === ""
            );
            if (isNumberedList && lines.some((l) => l.trim())) {
                const items = lines
                    .filter((l) => l.trim())
                    .map((l) => `<li>${l.replace(/^\s*\d+[\.\)]\s*/, "").trim()}</li>`)
                    .join("");
                return `<ol>${items}</ol>`;
            }

            // Regular paragraph — convert single newlines to <br>
            return `<p>${p.replace(/\n/g, "<br>")}</p>`;
        })
        .join("");

    return html;
}

// ─── Message Rendering ──────────────────────────────────────

function addUserMessage(text) {
    const msg = document.createElement("div");
    msg.className = "message user-message animate-in";
    msg.innerHTML = `
        <div class="message-content">
            <p>${escapeHtml(text)}</p>
        </div>
        <span class="message-time">${getCurrentTime()}</span>
    `;
    chatMessages.appendChild(msg);
    scrollToBottom();
}

function addBotMessage(text) {
    const msg = document.createElement("div");
    msg.className = "message bot-message animate-in";
    msg.innerHTML = `
        <div class="message-content">
            ${renderMarkdown(text)}
        </div>
        <span class="message-time">${getCurrentTime()}</span>
    `;
    chatMessages.appendChild(msg);
    scrollToBottom();
}

function showTypingIndicator() {
    const typing = document.createElement("div");
    typing.className = "message bot-message animate-in";
    typing.id = "typingIndicator";
    typing.innerHTML = `
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatMessages.appendChild(typing);
    scrollToBottom();
}

function removeTypingIndicator() {
    const typing = document.getElementById("typingIndicator");
    if (typing) typing.remove();
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

// ─── Quick Replies ──────────────────────────────────────────

function updateQuickReplies(replies) {
    quickReplies.innerHTML = "";
    if (!replies || replies.length === 0) return;

    replies.forEach((text) => {
        const btn = document.createElement("button");
        btn.className = "quick-reply-btn";
        btn.textContent = text;
        btn.addEventListener("click", () => {
            // Extract the actual message from the button text
            const messageMap = {
                "📚 View Courses": "What courses do you offer?",
                "📚 More Courses": "What courses do you offer?",
                "💰 Fee Structure": "What is the fee structure?",
                "💰 Fees": "What is the fee structure?",
                "💰 Fee Details": "What is the fee structure?",
                "🎯 Placements": "What are the placement statistics?",
                "📝 Enroll Now": "I want to enroll",
                "📝 Enroll": "I want to enroll",
                "🤖 AI & ML Course": "Tell me about the AI and Machine Learning course",
                "💻 Web Development": "Tell me about the Web Development course",
                "📊 Data Science": "Tell me about the Data Science course",
                "❓ Help": "Help",
                "❓ More Questions": "What else can you help me with?",
                "❓ More Info": "Can you give me more information?",
            };
            const msg = messageMap[text] || text;
            sendMessage(msg);
        });
        quickReplies.appendChild(btn);
    });
}

// ─── API Communication ──────────────────────────────────────

async function sendMessage(text) {
    if (!text.trim() || isWaitingForResponse) return;

    isWaitingForResponse = true;
    messageInput.value = "";
    sendBtn.disabled = true;

    // Add user message
    addUserMessage(text);

    // Show typing indicator
    showTypingIndicator();

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: text,
                session_id: sessionId,
            }),
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();

        // Small delay for natural feel
        await new Promise((r) => setTimeout(r, 600 + Math.random() * 400));

        removeTypingIndicator();
        addBotMessage(data.response);

        // Update session ID if returned
        if (data.session_id) {
            sessionId = data.session_id;
            localStorage.setItem(SESSION_KEY, sessionId);
        }

        // Update quick replies
        updateQuickReplies(data.quick_replies);

        // Refresh leads badge
        fetchLeadCount();
    } catch (error) {
        removeTypingIndicator();
        console.error("Chat error:", error);
        addBotMessage(
            "I'm sorry, I'm having trouble connecting right now. Please make sure the backend server is running (`uvicorn app:app --reload`) and try again! 🔄"
        );
    } finally {
        isWaitingForResponse = false;
        updateSendButton();
    }
}

// ─── Leads Modal ────────────────────────────────────────────

async function fetchLeadCount() {
    try {
        const res = await fetch(`${API_BASE}/leads`);
        const data = await res.json();
        const count = data.total || 0;
        leadsBadge.textContent = count;
        if (count > 0) {
            leadsBadge.classList.add("visible");
        } else {
            leadsBadge.classList.remove("visible");
        }
    } catch (e) {
        // Silently fail
    }
}

async function openLeadsModal() {
    leadsModal.classList.add("active");
    try {
        const res = await fetch(`${API_BASE}/leads`);
        const data = await res.json();

        if (!data.leads || data.leads.length === 0) {
            leadsContent.innerHTML = '<p class="empty-state">No leads captured yet. Start a conversation and enroll! 🎓</p>';
            return;
        }

        leadsContent.innerHTML = data.leads
            .reverse()
            .map(
                (lead) => `
                <div class="lead-card">
                    <h3>👤 ${escapeHtml(lead.name)}</h3>
                    <p>📚 Interest: ${escapeHtml(lead.interest)}</p>
                    <p>📞 Contact: ${escapeHtml(lead.contact)}</p>
                    <p class="lead-time">🕐 ${new Date(lead.timestamp).toLocaleString()}</p>
                </div>
            `
            )
            .join("");
    } catch (e) {
        leadsContent.innerHTML = '<p class="empty-state">Unable to load leads. Make sure the server is running.</p>';
    }
}

// ─── Input Handling ─────────────────────────────────────────

function updateSendButton() {
    sendBtn.disabled = !messageInput.value.trim() || isWaitingForResponse;
}

messageInput.addEventListener("input", updateSendButton);

messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage(messageInput.value);
    }
});

sendBtn.addEventListener("click", () => {
    sendMessage(messageInput.value);
});

// ─── Button Handlers ────────────────────────────────────────

leadsBtn.addEventListener("click", openLeadsModal);
closeModal.addEventListener("click", () => leadsModal.classList.remove("active"));
leadsModal.addEventListener("click", (e) => {
    if (e.target === leadsModal) leadsModal.classList.remove("active");
});

clearBtn.addEventListener("click", () => {
    // Reset session
    sessionId = generateUUID();
    localStorage.setItem(SESSION_KEY, sessionId);

    // Clear messages (keep welcome)
    chatMessages.innerHTML = `
        <div class="date-separator"><span>Today</span></div>
        <div class="message bot-message animate-in">
            <div class="message-content">
                <p>Hello! 👋 Welcome to <strong>TechEd Institute</strong>!</p>
                <p>I'm your AI assistant, here to help you explore our courses, answer questions, and get you started on your learning journey. 🎓</p>
                <p>How can I help you today?</p>
            </div>
            <span class="message-time">${getCurrentTime()}</span>
        </div>
    `;

    // Reset quick replies
    updateQuickReplies([
        "📚 View Courses",
        "💰 Fee Structure",
        "🎯 Placements",
        "📝 Enroll Now",
    ]);
});

// Quick reply initial buttons
document.querySelectorAll(".quick-reply-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        const messageMap = {
            "📚 View Courses": "What courses do you offer?",
            "💰 Fee Structure": "What is the fee structure?",
            "🎯 Placements": "What are the placement statistics?",
            "📝 Enroll Now": "I want to enroll",
        };
        const msg = messageMap[btn.textContent] || btn.dataset.message || btn.textContent;
        sendMessage(msg);
    });
});

// ─── Init ───────────────────────────────────────────────────
fetchLeadCount();
messageInput.focus();
