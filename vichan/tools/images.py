"""Image generation via the provider's OpenAI-compatible /images endpoint (OpenAI, Gemini)."""
import base64
import re
import time
import urllib.request
from pathlib import Path

from openai import OpenAI

from ..config import PROVIDERS, get_setting
from ..state import state
from . import tool


def _pick_client():
    """Use the current provider if it can make images, else any saved one that can."""
    cfg = state.cfg
    order = [state.provider] + [p for p in cfg["providers"] if p != state.provider]
    for pid in order:
        preset = PROVIDERS.get(pid, {})
        override = get_setting(cfg, "image_model")
        model = override if (override and pid == state.provider) else preset.get("image_model")
        if model and pid in cfg["providers"]:
            p = cfg["providers"][pid]
            return OpenAI(api_key=p["api_key"], base_url=p["base_url"]), model, pid
    raise RuntimeError(
        "no image-capable AI logged in. /login to OpenAI or Google Gemini "
        "(or set one with /config image_model if your provider supports images)."
    )


def _extension(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".png"


@tool(
    "generate_image",
    "Generate an image from a text prompt and save it as a file. Returns the saved path. "
    "Leave path blank to auto-name it in the user's images folder.",
    {
        "prompt": {"type": "string"},
        "path": {"type": "string", "description": "optional output file path"},
        "size": {"type": "string", "description": "e.g. 1024x1024, 1536x1024 (OpenAI only)"},
    },
    ["prompt"],
    approval=True,
)
def generate_image(prompt, path="", size="1024x1024"):
    client, model, pid = _pick_client()
    kw = {"model": model, "prompt": prompt, "n": 1}
    if pid == "openai":
        kw["size"] = size
    if not model.startswith("gpt-image"):
        kw["response_format"] = "b64_json"
    item = client.images.generate(**kw).data[0]
    if getattr(item, "b64_json", None):
        data = base64.b64decode(item.b64_json)
    elif getattr(item, "url", None):
        data = urllib.request.urlopen(item.url, timeout=60).read()
    else:
        return "error: the provider returned no image data"
    if path:
        out = Path(path)
    else:
        base = Path(get_setting(state.cfg, "images_dir") or ".")
        slug = re.sub(r"\W+", "-", prompt.lower())[:40].strip("-") or "image"
        out = base / f"{slug}-{int(time.time())}{_extension(data)}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return f"saved image ({len(data) // 1024} KB, model {model}) to {out.resolve()}"
