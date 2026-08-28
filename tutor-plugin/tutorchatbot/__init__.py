from __future__ import annotations
from tutor import hooks
from tutormfe.hooks import PLUGIN_SLOTS
import os

__version__ = "0.1.0"

# Default config
hooks.Filters.CONFIG_DEFAULTS.add_items([
    ("CHATBOT_HOST", "chatbot"),
    ("CHATBOT_PORT", 8000),
    ("CHATBOT_GEMINI_API_KEY", ""),
    ("CHATBOT_GROQ_API_KEY", ""),
    ("CHATBOT_DB_NAME", "chatbot"),
    ("CHATBOT_DB_USER", "chatbot"),
    ("CHATBOT_DB_PASSWORD", "changeme"),
    ("GITHUB_USERNAME", "danylopohrebniak"),
])

# Unique config (auto-generated)
hooks.Filters.CONFIG_UNIQUE.add_items([
    ("CHATBOT_DB_PASSWORD", "{{ 24|random_string }}"),
])

# Nginx patch
hooks.Filters.ENV_PATCHES.add_item((
    "openedx-lms-nginx-configs",
    """
location /chatbot-api/ {
    proxy_pass http://{{ CHATBOT_HOST }}:{{ CHATBOT_PORT }}/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
"""
))

# Add chatbot services to docker-compose
hooks.Filters.ENV_PATCHES.add_item((
    "local-docker-compose-services",
    """
chatbot:
  image: ghcr.io/{{ GITHUB_USERNAME }}/vle-ai-service:latest
  restart: unless-stopped
  environment:
    GEMINI_API_KEY: "{{ CHATBOT_GEMINI_API_KEY }}"
    GROQ_API_KEY: "{{ CHATBOT_GROQ_API_KEY }}"
    DATABASE_URL: "postgresql+asyncpg://{{ CHATBOT_DB_USER }}:{{ CHATBOT_DB_PASSWORD }}@chatbot-db:5432/{{ CHATBOT_DB_NAME }}"
    MONGODB_URL: "mongodb://mongodb:27017"
    DEV_MODE: "true"
    CHROMA_DIR: "/app/chroma_data"

chatbot-db:
  image: postgres:16-alpine
  restart: unless-stopped
  environment:
    POSTGRES_USER: "{{ CHATBOT_DB_USER }}"
    POSTGRES_PASSWORD: "{{ CHATBOT_DB_PASSWORD }}"
    POSTGRES_DB: "{{ CHATBOT_DB_NAME }}"
"""
))

# Register templates
hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
    os.path.join(os.path.dirname(__file__), "templates")
)

# Caddy patch — proxy /chatbot-api/ to chatbot service
hooks.Filters.ENV_PATCHES.add_item((
    "caddyfile-lms",
    """
    handle_path /chatbot-api/* {
        reverse_proxy chatbot:8000
    }
"""
))

# Floating chat widget for the MFEs (React apps served under apps.*) —
# footer.html theme overrides never reach these pages, so the widget
# has to be injected via the frontend plugin framework's footer_slot instead.
hooks.Filters.ENV_PATCHES.add_item((
    "mfe-env-config-buildtime-imports",
    r"""
const AI_CHAT_WIDGET_MARKUP = `
<style>
  #cb-btn {
    position: fixed; bottom: 28px; right: 28px;
    width: 56px; height: 56px;
    background: #1d4ed8; color: white;
    border: none; border-radius: 50%;
    font-size: 26px; cursor: pointer;
    box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    z-index: 9999;
    display: flex; align-items: center; justify-content: center;
    padding: 0; line-height: 1;
    transition: background 0.2s, transform 0.2s;
  }
  #cb-btn:hover { background: #1e40af; transform: scale(1.08); }
  #cb-panel {
    position: fixed; bottom: 96px; right: 28px;
    width: 360px; height: 520px;
    background: white; border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.18);
    z-index: 9998; display: none;
    flex-direction: column; overflow: hidden;
  }
  #cb-panel.open { display: flex; }
  #cb-header {
    background: #1d4ed8; color: white;
    padding: 12px 16px;
    display: flex; align-items: center; justify-content: space-between;
  }
  #cb-title { font-weight: 600; font-size: 14px; }
  #cb-sub { font-size: 11px; opacity: 0.8; }
  #cb-close {
    background: none; border: none; color: white;
    font-size: 18px; cursor: pointer; padding: 0; line-height: 1;
  }
  #cb-messages {
    flex: 1; overflow-y: auto; padding: 12px;
    display: flex; flex-direction: column; gap: 8px;
    background: #f8fafc;
  }
  .cb-msg {
    max-width: 85%; padding: 8px 12px; border-radius: 14px;
    font-size: 13px; line-height: 1.5; word-break: break-word;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  .cb-msg.user {
    background: #1d4ed8; color: white;
    align-self: flex-end; border-bottom-right-radius: 3px;
  }
  .cb-msg.bot {
    background: white; color: #1e293b;
    align-self: flex-start; border-bottom-left-radius: 3px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  .cb-typing span {
    display: inline-block; width: 6px; height: 6px;
    background: #94a3b8; border-radius: 50%; margin: 0 2px;
    animation: cb-bounce 1.2s infinite;
  }
  .cb-typing span:nth-child(2) { animation-delay: 0.2s; }
  .cb-typing span:nth-child(3) { animation-delay: 0.4s; }
  @keyframes cb-bounce {
    0%,80%,100% { transform: translateY(0); }
    40% { transform: translateY(-5px); }
  }
  #cb-input-area {
    display: flex; padding: 10px 12px; gap: 8px;
    background: white; border-top: 1px solid #e2e8f0;
  }
  #cb-input {
    flex: 1; border: 1px solid #cbd5e1; border-radius: 10px;
    padding: 8px 12px; font-size: 13px; font-family: inherit;
    resize: none; outline: none; max-height: 80px;
  }
  #cb-input:focus { border-color: #1d4ed8; }
  #cb-send {
    background: #1d4ed8; color: white; border: none;
    border-radius: 10px; padding: 0 14px; font-size: 16px;
    cursor: pointer; align-self: flex-end; height: 36px;
  }
  #cb-send:disabled { background: #93c5fd; cursor: not-allowed; }
</style>
<button id="cb-btn" title="AI Assistant">&#x1F4AC;</button>
<div id="cb-panel">
  <div id="cb-header">
    <div>
      <div id="cb-title">&#x1F916; AI Learning Assistant</div>
      <div id="cb-sub">Ask me about this course</div>
    </div>
    <button id="cb-close">&#x2715;</button>
  </div>
  <div id="cb-messages">
    <div class="cb-msg bot">&#x1F44B; Hello! Ask me anything about your course materials.</div>
  </div>
  <div id="cb-input-area">
    <textarea id="cb-input" placeholder="Ask a question..." rows="1"></textarea>
    <button id="cb-send">&#x27A4;</button>
  </div>
</div>
`;

function AiChatWidget() {
  if (typeof document !== 'undefined' && !document.getElementById('cb-btn')) {
    const host = document.createElement('div');
    host.id = 'cb-widget-host';
    host.innerHTML = AI_CHAT_WIDGET_MARKUP;
    document.body.appendChild(host);

    const API = "//{{ LMS_HOST }}/chatbot-api/api/v1";
    let sessionId = sessionStorage.getItem("cb_session") || null;
    const userId = (function() {
      try {
        const cookie = document.cookie.split("; ").find(function(r) {
          return r.startsWith("edx-user-info=");
        });
        if (cookie) {
          const val = decodeURIComponent(cookie.split("=").slice(1).join("="));
          const fixed = val.slice(1, -1).replace(/\054/g, ",").replace(/\"/g, '"');
          const info = JSON.parse(fixed);
          return info.username || "anonymous";
        }
      } catch (e) { /* fall through to anonymous */ }
      return "anonymous";
    })();
    const courseId = (function() {
      const m = window.location.pathname.match(/course-v1:[^/]+[+][^/]+[+][^/]+/);
      return m ? m[0] : null;
    })();

    const btn = document.getElementById("cb-btn");
    const panel = document.getElementById("cb-panel");
    const closeBtn = document.getElementById("cb-close");
    const messages = document.getElementById("cb-messages");
    const input = document.getElementById("cb-input");
    const sendBtn = document.getElementById("cb-send");

    btn.onclick = function() {
      panel.classList.toggle("open");
      if (panel.classList.contains("open")) input.focus();
    };
    closeBtn.onclick = function() { panel.classList.remove("open"); };
    input.addEventListener("input", function() {
      input.style.height = "auto";
      input.style.height = input.scrollHeight + "px";
    });
    input.addEventListener("keydown", function(e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
    });
    sendBtn.onclick = send;

    function addMsg(role, text) {
      const d = document.createElement("div");
      d.className = "cb-msg " + role;
      d.textContent = text;
      messages.appendChild(d);
      messages.scrollTop = messages.scrollHeight;
      return d;
    }
    function addTyping() {
      const d = document.createElement("div");
      d.className = "cb-msg bot cb-typing";
      d.innerHTML = "<span></span><span></span><span></span>";
      messages.appendChild(d);
      messages.scrollTop = messages.scrollHeight;
      return d;
    }
    function send() {
      const text = input.value.trim();
      if (!text) return;
      input.value = ""; input.style.height = "auto";
      sendBtn.disabled = true;
      addMsg("user", text);
      const typing = addTyping();
      fetch(API + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId, user_id: userId, course_id: courseId })
      })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        typing.remove();
        if (data.session_id) { sessionId = data.session_id; sessionStorage.setItem("cb_session", sessionId); }
        addMsg("bot", data.reply || "Sorry, could not process that.");
      })
      .catch(function() { typing.remove(); addMsg("bot", "Connection error. Please try again."); })
      .finally(function() { sendBtn.disabled = false; input.focus(); });
    }
  }

  return null;
}
"""
))

PLUGIN_SLOTS.add_items([
    (
        "all",
        "footer_slot",
        """
        {
          op: PLUGIN_OPERATIONS.Insert,
          widget: {
            id: 'ai_chat_widget',
            type: DIRECT_PLUGIN,
            RenderWidget: AiChatWidget,
          },
        }"""
    ),
])
