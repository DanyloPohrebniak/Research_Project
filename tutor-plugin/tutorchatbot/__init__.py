from __future__ import annotations
import pkg_resources
from tutor import hooks

__version__ = "0.1.0"

# Default config
hooks.Filters.CONFIG_DEFAULTS.add_items([
    ("CHATBOT_HOST", "chatbot"),
    ("CHATBOT_PORT", 8000),
    ("CHATBOT_GEMINI_API_KEY", ""),
    ("CHATBOT_DB_NAME", "chatbot"),
    ("CHATBOT_DB_USER", "chatbot"),
    ("CHATBOT_DB_PASSWORD", "changeme"),
])

# Unique config (auto-generated)
hooks.Filters.CONFIG_UNIQUE.add_items([
    ("CHATBOT_DB_PASSWORD", "{{ 24|random_string }}"),
])

# Nginx patch — proxy /chatbot-api/ to our service
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

# Add chatbot service to docker-compose
hooks.Filters.ENV_PATCHES.add_item((
    "local-docker-compose-services",
    """
  chatbot:
    image: ghcr.io/{{ GITHUB_USERNAME }}/vle-ai-service:latest
    restart: unless-stopped
    environment:
      GEMINI_API_KEY: "{{ CHATBOT_GEMINI_API_KEY }}"
      DATABASE_URL: "postgresql+asyncpg://{{ CHATBOT_DB_USER }}:{{ CHATBOT_DB_PASSWORD }}@chatbot-db:5432/{{ CHATBOT_DB_NAME }}"
      MONGODB_URL: "mongodb://{{ MONGODB_USERNAME }}:{{ MONGODB_PASSWORD }}@mongodb:27017"
    volumes:
      - chatbot-chroma:/data/chroma
    depends_on:
      - chatbot-db
    networks:
      - default

  chatbot-db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: "{{ CHATBOT_DB_USER }}"
      POSTGRES_PASSWORD: "{{ CHATBOT_DB_PASSWORD }}"
      POSTGRES_DB: "{{ CHATBOT_DB_NAME }}"
    volumes:
      - chatbot-pgdata:/var/lib/postgresql/data
    networks:
      - default
"""
))

# Add volumes
hooks.Filters.ENV_PATCHES.add_item((
    "local-docker-compose-volume-mounts",
    """
  chatbot-pgdata:
  chatbot-chroma:
"""
))

# Register templates
hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
    pkg_resources.resource_filename("tutorchatbot", "templates")
)