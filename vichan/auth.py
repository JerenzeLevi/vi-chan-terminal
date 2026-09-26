"""/login, /switch, /logout and picking the model."""
import re

import openai
from openai import OpenAI
from prompt_toolkit import prompt as pt_prompt

from .config import PROVIDERS, save_config
from .state import state
from .ui import ask, choose, console
from .views import display_name, show_home


def activate(pid):
    p = state.cfg["providers"][pid]
    state.client = OpenAI(api_key=p["api_key"] or "none", base_url=p["base_url"])
    state.model, state.provider = p["model"], pid
    state.limits, state.limited_until, state.ctx_tokens = {}, 0.0, 0
    state.stream_usage = True
    state.cfg["active"] = pid
    save_config(state.cfg)


def login(pid=None):
    """Pick provider (if not given), ask for key + model, verify, save, activate."""
    cfg = state.cfg
    ids = list(PROVIDERS)
    if pid is None:
        idx = choose("Choose your AI provider", [PROVIDERS[i]["label"] for i in ids])
        if idx is None:
            return False
        pid = ids[idx]
    preset = PROVIDERS[pid]
    base_url = preset["base_url"]
    if pid == "custom":
        base_url = ask("base URL (e.g. https://host/v1)")
        if not base_url:
            return False
    key = ""
    if preset["needs_key"]:
        key = pt_prompt(f"  {preset['label']} API key (hidden) › ", is_password=True).strip()
        if not key:
            console.print("[peach]no key given, cancelled.[/]")
            return False
    model = ask(f"model [{preset['model'] or 'required'}]") or preset["model"]
    if not model:
        return False
    name = pid if pid != "custom" else "custom:" + re.sub(r"\W+", "-", base_url.split("//")[-1])[:30]
    cfg["providers"][name] = {"api_key": key, "base_url": base_url, "model": model}
    activate(name)
    try:
        with console.status("[lav]checking key~[/]"):
            state.client.chat.completions.create(model=model, messages=[{"role": "user", "content": "hi"}], max_tokens=5)
    except openai.AuthenticationError:
        console.print("[red]that key was rejected. use /login to try again.[/]")
        cfg["providers"].pop(name, None)
        cfg["active"], state.client, state.provider = None, None, None
        save_config(cfg)
        return False
    except Exception as e:  # noqa: BLE001
        console.print(f"[peach]saved, but the test call failed: {e}[/]\n[peach]check the model name / URL (use /model to fix).[/]")
    console.print(f"[mint]logged in ✧ {preset['label']} · {model}[/]")
    show_home()
    return True


def switch():
    cfg = state.cfg
    saved = list(cfg["providers"])
    rows = [f"{display_name(p)} · {cfg['providers'][p]['model']} (saved)" for p in saved]
    unsaved = [p for p in PROVIDERS if p not in saved and p != "custom"] + ["custom"]
    rows += [f"{PROVIDERS[p]['label']} (needs API key)" for p in unsaved]
    idx = choose("Switch to which AI?", rows, current=saved.index(state.provider) if state.provider in saved else None)
    if idx is None:
        return False
    if idx < len(saved):
        activate(saved[idx])
        console.print(f"[mint]switched ✧ {display_name(saved[idx])} · {state.model}[/]")
        return True
    return login(unsaved[idx - len(saved)])


def logout(arg=""):
    cfg = state.cfg
    if arg == "all":
        cfg["providers"].clear()
        console.print("[mint]all keys removed ✧[/]")
    elif state.provider:
        cfg["providers"].pop(state.provider, None)
        console.print(f"[mint]logged out of {display_name(state.provider)} ✧[/]")
    cfg["active"], state.client, state.provider = None, None, None
    save_config(cfg)
    console.print("[lav]use /login or /switch to pick an AI again.[/]")


# ---- models
_JUNK = ("embed", "tts", "whisper", "dall-e", "image", "moderation", "transcribe", "audio", "realtime", "imagen", "veo", "aqa", "guard")


def list_models():
    ids = sorted({m.id.removeprefix("models/") for m in state.client.models.list()})
    return [i for i in ids if not any(j in i.lower() for j in _JUNK)] or ids


def set_model(name):
    state.model = state.cfg["providers"][state.provider]["model"] = name
    state.ctx_tokens = 0
    save_config(state.cfg)
    console.print(f"[mint]model → {name} ✧[/]")


def pick_model(arg=""):
    if not state.client:
        console.print("[peach]not logged in yet. use /login first ♡[/]")
        return
    console.print(f"[lav]current:[/] {display_name(state.provider)} · [rose]{state.model}[/]")
    try:
        with console.status("[lav]fetching models~[/]"):
            models = list_models()
    except Exception:  # noqa: BLE001
        models = []
    if arg:
        if arg in models or not models:
            return set_model(arg)
        matches = [m for m in models if arg.lower() in m.lower()]
        if len(matches) == 1:
            return set_model(matches[0])
        if not matches:
            console.print("[peach]not in this provider's list; using it anyway.[/]")
            return set_model(arg)
        models = matches
    if not models:
        name = ask("model name")
        return set_model(name) if name else None
    shown = models[:50]
    hint = f"showing {len(shown)} of {len(models)}. use /model <search> to filter." if len(models) > 50 else "or set one directly: /model <name>"
    idx = choose("Pick a model", shown, current=shown.index(state.model) if state.model in shown else None, hint=hint)
    if idx is not None:
        set_model(shown[idx])
