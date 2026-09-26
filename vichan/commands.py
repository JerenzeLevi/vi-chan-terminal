"""Slash commands."""
import os
import shlex

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import about, auth, skills
from .agent import compact
from .config import APP, MCP_PRESETS, SETTINGS, USER_SKILLS_DIR, get_setting, save_config, set_setting
from .state import state
from .ui import BLUSH, LAV, PINK, ask, choose, console
from .views import display_name, show_usage


def cmd_help(arg):
    t = Table.grid(padding=(0, 2))
    for name, (_, desc) in COMMANDS.items():
        t.add_row(Text(name, style="bold #ff6fb1"), desc)
    t.add_row(Text("shift+tab", style="bold #ff6fb1"), "toggle plan mode")
    console.print(Panel(t, title="♡ commands", title_align="left", border_style=LAV, box=box.ROUNDED))


def cmd_clear(arg):
    state.messages = state.messages[:1]
    state.ctx_tokens = 0
    console.print("[mint]memory cleared ✧[/]")


def cmd_compact(arg):
    if not state.client:
        return console.print("[peach]not logged in yet ♡[/]")
    console.print(f"[mint]{compact()} ✧[/]")


def cmd_plan(arg):
    want = {"on": True, "off": False}.get(arg.lower(), not state.plan_mode)
    state.plan_mode = want
    console.print(
        "[rose]✎ plan mode ON[/] [blush]— I'll only research and ask questions, then show a plan for your approval.[/]"
        if want
        else "[mint]plan mode off ✧ I can make changes again.[/]"
    )


def cmd_model(arg):
    auth.pick_model(arg)


def cmd_config(arg):
    cfg = state.cfg
    parts = arg.split(None, 1)
    if len(parts) == 2:
        try:
            console.print(f"[mint]{parts[0]} = {set_setting(cfg, parts[0], parts[1])!r} ✧[/]")
        except ValueError as e:
            console.print(f"[peach]{e}[/]")
        return
    names = list(SETTINGS)
    if len(parts) == 1:
        name = parts[0]
    else:
        t = Table.grid(padding=(0, 2))
        for n in names:
            t.add_row(Text(n, style="bold #ff6fb1"), Text(repr(get_setting(cfg, n)), style=BLUSH), Text(SETTINGS[n][1], style="dim"))
        t.add_row("", "", "")
        t.add_row(Text("AI", style=LAV), display_name(state.provider) or "not logged in", f"{len(cfg['providers'])} saved key(s)")
        t.add_row(Text("mcp", style=LAV), f"{len(cfg['mcp_servers'])} server(s)", "/mcp")
        console.print(Panel(t, title="♡ config", title_align="left", border_style=PINK, box=box.ROUNDED))
        idx = choose("Change which setting?", [f"{n} = {get_setting(cfg, n)!r}" for n in names])
        if idx is None:
            return
        name = names[idx]
    if name not in SETTINGS:
        return console.print(f"[peach]unknown setting '{name}'. try /config[/]")
    raw = ask(f"new value for {name} (now {get_setting(cfg, name)!r})")
    if raw:
        try:
            console.print(f"[mint]{name} = {set_setting(cfg, name, raw)!r} ✧[/]")
        except ValueError as e:
            console.print(f"[peach]{e}[/]")


def cmd_mcp(arg):
    cfg = state.cfg
    try:
        parts = shlex.split(arg, posix=os.name != "nt")
    except ValueError as e:
        return console.print(f"[peach]{e}[/]")
    parts = [p.strip("\"'") for p in parts]
    sub = parts[0] if parts else "list"
    if sub == "add" and len(parts) >= 2:
        name = parts[1]
        if len(parts) > 2:
            server = {"command": parts[2], "args": parts[3:]}
        elif name in MCP_PRESETS:
            server = dict(MCP_PRESETS[name])
        else:
            return console.print(f"[peach]usage: /mcp add <name> <command> [args...]   presets: {', '.join(MCP_PRESETS)}[/]")
        cfg["mcp_servers"][name] = server
        save_config(cfg)
        state.mcp.start(name, server)
        console.print(f"[mint]added '{name}' ✧ connecting in the background (first run may download things). check /mcp[/]")
    elif sub == "remove" and len(parts) == 2:
        cfg["mcp_servers"].pop(parts[1], None)
        state.mcp.stop(parts[1])
        save_config(cfg)
        console.print(f"[mint]removed '{parts[1]}' ✧[/]")
    elif sub == "reload":
        for n, s in cfg["mcp_servers"].items():
            state.mcp.start(n, s)
        console.print("[mint]reconnecting all servers ✧[/]")
    else:
        t = Table.grid(padding=(0, 2))
        for n in cfg["mcp_servers"]:
            info = state.mcp.servers.get(n, {"status": "stopped", "tools": [], "error": ""})
            color = {"ready": "green", "connecting": "yellow"}.get(info["status"], "red")
            extra = f"{len(info['tools'])} tools" if info["status"] == "ready" else info["error"][:80]
            t.add_row(Text(n, style="bold #ff6fb1"), Text(info["status"], style=color), extra)
        if not cfg["mcp_servers"]:
            t.add_row("no MCP servers yet", "", "")
        console.print(Panel(t, title="♡ mcp servers", title_align="left", border_style=PINK, box=box.ROUNDED))
        console.print(
            f"[blush]  /mcp add playwright   ← a real browser the AI can drive\n"
            f"  presets: {', '.join(MCP_PRESETS)} · custom: /mcp add <name> <command> [args] · /mcp remove <name> · /mcp reload[/]"
        )


def cmd_skills(arg):
    t = Table.grid(padding=(0, 2))
    for name, desc in skills.BUILTIN_CAPABILITIES:
        t.add_row(Text(name, style="bold #ff6fb1"), desc)
    console.print(Panel(t, title="♡ built-in skills", title_align="left", border_style=PINK, box=box.ROUNDED))
    found = skills.discover()
    if found:
        t2 = Table.grid(padding=(0, 2))
        for n, v in found.items():
            t2.add_row(Text(n, style="bold #ff6fb1"), v["description"])
        console.print(Panel(t2, title="♡ your skills", title_align="left", border_style=LAV, box=box.ROUNDED))
    else:
        console.print(f"[blush]  add your own: a folder with SKILL.md in {USER_SKILLS_DIR} or ./.cutie/skills/[/]")


def cmd_about(arg):
    caps = "\n".join(f"  ♡ {c}" for c in about.CAPABILITIES)
    body = (
        f"[bold #ff6fb1]Vi-Chan[/] is the AI agent inside [bold]{APP}[/], a kawaii, jolly and curious helper for your terminal.\n\n"
        f"[#c9b6ff]creator[/]  {about.CREATOR}\n[#c9b6ff]github[/]   {about.GITHUB}\n\n"
        f"[#c9b6ff]about the name[/]\n{about.ORIGIN}\n\n[#c9b6ff]what I can do[/]\n{caps}\n\n"
        f"[#ffc8e2]I run on whatever AI you log in with, so the smarter the model, the smarter I am ♡[/]"
    )
    console.print(Panel(body, title="♡ about Vi-Chan", title_align="left", border_style=PINK, box=box.ROUNDED, padding=(1, 2)))


def cmd_cd(arg):
    try:
        os.chdir(os.path.expanduser(arg or "~"))
        console.print(f"[mint]now in {os.getcwd()} ✧[/]")
    except OSError as e:
        console.print(f"[peach]{e}[/]")


COMMANDS = {
    "/help": (cmd_help, "show this list"),
    "/login": (lambda a: auth.login(), "pick an AI and enter its API key"),
    "/switch": (lambda a: auth.switch(), "switch to another AI (asks for a key if needed)"),
    "/logout": (lambda a: auth.logout(a), "forget the current key (/logout all = every key)"),
    "/model": (cmd_model, "show / change the model (/model gemini-2.5-pro or just /model)"),
    "/config": (cmd_config, "view / change settings (/config key value)"),
    "/usage": (lambda a: show_usage(), "tokens, context fullness, rate limits"),
    "/plan": (cmd_plan, "plan mode: research + approve a plan before changes"),
    "/mcp": (cmd_mcp, "tools from MCP servers, e.g. /mcp add playwright"),
    "/skills": (cmd_skills, "built-in abilities + your own SKILL.md skills"),
    "/compact": (cmd_compact, "summarise the chat to free up context"),
    "/clear": (cmd_clear, "forget this conversation"),
    "/vi-chan": (cmd_about, "about me, my creator, and the story of my name"),
    "/cd": (cmd_cd, "change working folder"),
    "/exit": (None, "quit"),
}


def dispatch(text):
    """Run a slash command. Returns False if the app should exit."""
    cmd, _, arg = text.partition(" ")
    if cmd in ("/exit", "/quit"):
        return False
    entry = COMMANDS.get(cmd)
    if not entry:
        console.print("[peach]unknown command, try /help[/]")
    else:
        entry[0](arg.strip())
    return True
