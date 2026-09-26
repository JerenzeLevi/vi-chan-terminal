"""Paths, provider presets, and persistent settings."""
import json
import os
from pathlib import Path

APP = "Vi-Chan Terminal"
CONFIG_DIR = Path.home() / ".cutie-term"
CONFIG_FILE = CONFIG_DIR / "config.json"
USER_SKILLS_DIR = CONFIG_DIR / "skills"

PROVIDERS = {
    "openai": dict(label="OpenAI", base_url="https://api.openai.com/v1", model="gpt-4o", needs_key=True, image_model="gpt-image-1"),
    "anthropic": dict(label="Anthropic (Claude)", base_url="https://api.anthropic.com/v1/", model="claude-sonnet-4-5", needs_key=True),
    "gemini": dict(
        label="Google Gemini", base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        model="gemini-2.5-flash", needs_key=True, image_model="imagen-3.0-generate-002",
    ),
    "openrouter": dict(label="OpenRouter (many models)", base_url="https://openrouter.ai/api/v1", model="anthropic/claude-sonnet-4.5", needs_key=True),
    "groq": dict(label="Groq", base_url="https://api.groq.com/openai/v1", model="llama-3.3-70b-versatile", needs_key=True),
    "ollama": dict(label="Ollama (local, no key)", base_url="http://localhost:11434/v1", model="llama3.1", needs_key=False),
    "custom": dict(label="Custom OpenAI-compatible URL", base_url="", model="", needs_key=True),
}

# substring of model name -> context window (tokens). Estimates; first match wins.
CONTEXT_WINDOWS = [
    ("gpt-4.1", 1_000_000), ("gpt-5", 400_000), ("gpt-4o", 128_000), ("o3", 200_000), ("o4", 200_000),
    ("claude", 200_000), ("gemini", 1_000_000), ("llama", 128_000), ("qwen", 128_000), ("deepseek", 128_000),
]

MCP_PRESETS = {
    "playwright": {"command": "npx", "args": ["-y", "@playwright/mcp@latest"]},
    "filesystem": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]},
    "fetch": {"command": "uvx", "args": ["mcp-server-fetch"]},
}

# name -> (default, description)
SETTINGS = {
    "auto_approve": (False, "run file edits, commands & MCP tools without asking"),
    "images_dir": ("", "folder for generated images (blank = current folder)"),
    "image_model": ("", "image model override (blank = provider default)"),
    "max_steps": (40, "max tool steps the AI may take per request"),
    "show_footer": (True, "show time / tokens / limits after each reply"),
}


def load_config():
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        cfg = {}
    cfg.setdefault("active", None)
    cfg.setdefault("providers", {})
    cfg.setdefault("settings", {})
    cfg.setdefault("mcp_servers", {})
    return cfg


def save_config(cfg):
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except OSError:
        pass


def get_setting(cfg, name):
    return cfg["settings"].get(name, SETTINGS[name][0])


def set_setting(cfg, name, raw):
    """Coerce raw text to the setting's type, store it, return the new value."""
    if name not in SETTINGS:
        raise ValueError(f"unknown setting '{name}'")
    default = SETTINGS[name][0]
    if isinstance(default, bool):
        val = raw.strip().lower() in ("1", "true", "yes", "on", "y")
    elif isinstance(default, int):
        val = int(raw)
        if val < 1:
            raise ValueError("must be 1 or more")
    else:
        val = raw.strip()
    cfg["settings"][name] = val
    save_config(cfg)
    return val
