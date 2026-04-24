from __future__ import annotations
from tutor import hooks
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
    MONGODB_URL: "mongodb://{{ MONGODB_USERNAME }}:{{ MONGODB_PASSWORD }}@mongodb:27017"
    DEV_MODE: "true"

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

# Auto-copy footer with chatbot widget to theme templates
@hooks.Actions.ENV_GENERATED.add()
def copy_footer(*args, **kwargs):
    import shutil
    src = os.path.join(os.path.dirname(__file__), "templates", "tutorchatbot", "footer.html")
    dst = os.path.expanduser(
        "~/.local/share/tutor/env/build/openedx/themes/indigo/lms/templates/footer.html"
    )
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)