"""The agent loop: stream a reply, run the tools it asks for, repeat until done."""
import json
import os
import random
import sys
import time
from pathlib import Path

import openai
from rich import box
from rich.console import Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from . import skills
from .about import PERSONA, SELF_KNOWLEDGE
from .config import APP, get_setting
from .state import _num, ctx_pct, ctx_window, limit_status, record_headers, state
from .tools import available_tools, schemas
from .ui import BLUSH, LAV, MINT, PINK, THINKING_WORDS, console, fmt_n, fmt_time

PLAN_TEXT = (
    "\n\nPLAN MODE IS ON. You may only read and research (read_file, list_dir, glob, grep, read_* office tools, "
    "read-only MCP tools) and ask the user questions. Do NOT change anything. Investigate, then call "
    "exit_plan_mode with a concrete markdown plan (files, steps, risks). Only after approval will you be allowed to make changes."
)


def build_system():
    s = (
        f"You are Vi-Chan, a capable, friendly software-engineering and productivity agent running in the user's terminal ({APP}). "
        f"Working directory: {os.getcwd()}. OS: {sys.platform}.\n"
        "Work autonomously: explore with list_dir/glob/grep/read_file, make changes with edit_file "
        "(write_file only for new files), verify with run_command, and keep going until the task is done. "
        "Read a file before editing it. Don't guess paths or contents. When a decision is genuinely the user's, "
        "use ask_user_question instead of guessing. You can also create Excel/Word/PowerPoint files, generate images, "
        "and use any MCP tools (e.g. a browser) that are available. Be concise and accurate; "
        "report what you did and anything that failed."
    )
    s += f"\n\n{PERSONA}\n\n{SELF_KNOWLEDGE}"
    if state.plan_mode:
        s += PLAN_TEXT
    found = skills.discover()
    if found:
        s += "\n\nUser skills (load one with use_skill when relevant):\n" + "\n".join(f"- {n}: {v['description']}" for n, v in found.items())
    for name in ("CUTIE.md", "CLAUDE.md", "AGENTS.md"):
        f = Path(name)
        if f.exists():
            s += f"\n\nProject instructions ({name}):\n{f.read_text(encoding='utf-8', errors='replace')[:8000]}"
            break
    return s


def call_model(messages, tools):
    kw = dict(model=state.model, messages=messages, stream=True)
    if tools:
        kw["tools"] = schemas(tools)
    if state.stream_usage:
        kw["stream_options"] = {"include_usage": True}
    try:
        raw = state.client.chat.completions.with_raw_response.create(**kw)
    except openai.BadRequestError as e:
        if state.stream_usage and "stream_options" in str(e):
            state.stream_usage = False
            return call_model(messages, tools)
        raise
    record_headers(raw.headers)
    state.requests += 1
    return raw.parse()


def stream_response(messages, tools, turn):
    """Stream one model response with a live rotating-word status line. Returns (text, tool_calls)."""
    stream = call_model(messages, tools)
    s = {"text": "", "calls": {}, "usage": None, "done": False}

    def view():
        panel = Panel(Markdown(s["text"]), border_style=PINK, title="♡ Vi-Chan", title_align="left", box=box.ROUNDED) if s["text"] else None
        if s["done"]:
            return panel or Text("")
        elapsed = time.time() - turn["start"]
        word = THINKING_WORDS[(turn["seed"] + int(elapsed / 2.5)) % len(THINKING_WORDS)]
        est = (len(s["text"]) + sum(len(c["args"]) for c in s["calls"].values())) // 4
        line = Text(f"  ✧ {word}…  {fmt_time(elapsed)} · ↓ ~{fmt_n(turn['out'] + est)} tokens", style=LAV)
        return Group(panel, line) if panel else line

    with Live(get_renderable=view, console=console, refresh_per_second=10):
        for chunk in stream:
            if getattr(chunk, "usage", None):
                s["usage"] = chunk.usage
            if not chunk.choices:
                continue
            d = chunk.choices[0].delta
            if d.content:
                s["text"] += d.content
            for tc in d.tool_calls or []:
                i = tc.index if tc.index is not None else len(s["calls"])
                c = s["calls"].setdefault(i, {"id": "", "name": "", "args": ""})
                if tc.id:
                    c["id"] = tc.id
                if tc.function:
                    if tc.function.name:
                        c["name"] = tc.function.name
                    if tc.function.arguments:
                        c["args"] += tc.function.arguments
        s["done"] = True

    u = s["usage"]
    if u:
        p_in, p_out = u.prompt_tokens, u.completion_tokens
    else:  # provider gave no usage: estimate ~4 chars/token
        p_in = len(json.dumps(messages, default=str)) // 4
        p_out = (len(s["text"]) + sum(len(c["args"]) for c in s["calls"].values())) // 4
    turn["in"] += p_in
    turn["out"] += p_out
    state.session_in += p_in
    state.session_out += p_out
    state.ctx_tokens = p_in + p_out
    return s["text"], [s["calls"][i] for i in sorted(s["calls"])]


def approve(t, args):
    if state.session_auto_approve or get_setting(state.cfg, "auto_approve"):
        return True
    console.print(t.preview(args) if t.preview else Text(f"  {t.name}: {json.dumps(args, ensure_ascii=False)[:200]}", style=BLUSH))
    ans = console.input("[peach]  ♡ allow? [y/N/a=always this session] [/]").strip().lower()
    if ans == "a":
        state.session_auto_approve = True
        return True
    return ans == "y"


def execute_tool(name, args, tools):
    t = tools.get(name)
    if not t:
        return f"error: tool '{name}' is not available right now" + (" (plan mode is on: read-only tools only)" if state.plan_mode else "")
    if t.approval and not approve(t, args):
        return "User declined this action."
    try:
        if t.interactive:
            result = t.fn(**args)
        else:
            with console.status(f"[lav]{random.choice(THINKING_WORDS)}…[/]", spinner="dots"):
                result = t.fn(**args)
    except TypeError as e:
        result = f"error: bad arguments for {name}: {e}"
    except Exception as e:  # noqa: BLE001
        result = f"error: {e}"
    return str(result)[:20000]


def print_footer(turn):
    level, lim = limit_status()
    pct = ctx_pct()
    if get_setting(state.cfg, "show_footer"):
        console.print(
            Text(
                f"  ⏱ {fmt_time(time.time() - turn['start'])} · ↑ {fmt_n(turn['in'])} in · ↓ {fmt_n(turn['out'])} out · "
                f"ctx {pct}% of {fmt_n(ctx_window())} · {lim}",
                style=BLUSH,
            )
        )
    if pct >= 80:
        console.print("[peach]  ⚠ context is nearly full. try /compact (summarise) or /clear before the model starts forgetting.[/]")
    if level == "low":
        console.print("[peach]  ⚠ you're close to your rate limit. slow down or /switch to another AI.[/]")


def run_turn():
    """Run the agent on state.messages until the model stops calling tools."""
    messages = state.messages
    messages[0] = {"role": "system", "content": build_system()}
    turn = {"start": time.time(), "in": 0, "out": 0, "seed": random.randrange(len(THINKING_WORDS))}
    max_steps = get_setting(state.cfg, "max_steps")
    for _ in range(max_steps):
        tools = available_tools()
        text, calls = stream_response(messages, tools, turn)
        msg = {"role": "assistant", "content": text or None}
        if calls:
            msg["tool_calls"] = [
                {"id": c["id"] or f"call_{i}", "type": "function", "function": {"name": c["name"], "arguments": c["args"] or "{}"}}
                for i, c in enumerate(calls)
            ]
        messages.append(msg)
        if not calls:
            break
        for i, c in enumerate(calls):
            try:
                args = json.loads(c["args"] or "{}")
            except json.JSONDecodeError:
                args = {}
            console.print(Text(f"  ✧ {c['name']} {json.dumps(args, ensure_ascii=False)[:100]}", style=MINT))
            result = execute_tool(c["name"], args, available_tools())
            messages.append({"role": "tool", "tool_call_id": c["id"] or f"call_{i}", "content": result})
    else:
        console.print(f"[peach]  ⚠ stopped after {max_steps} steps. say 'continue' to keep going (or raise it: /config max_steps).[/]")
    print_footer(turn)


def compact():
    """Replace the conversation with a model-written summary to free up context."""
    if len(state.messages) <= 2:
        return "nothing to compact yet."
    convo = json.dumps(state.messages[1:], default=str, ensure_ascii=False)[-60000:]
    with console.status("[lav]Unraveling the conversation…[/]", spinner="dots"):
        resp = state.client.chat.completions.create(
            model=state.model,
            messages=[
                {"role": "system", "content": "Summarise this agent conversation for your own future use: goals, decisions, files touched, "
                 "current state, open TODOs. Be dense and factual, under 500 words."},
                {"role": "user", "content": convo},
            ],
        )
    summary = resp.choices[0].message.content or ""
    state.messages = [
        state.messages[0],
        {"role": "user", "content": f"Summary of our conversation so far:\n{summary}"},
        {"role": "assistant", "content": "Got it ♡ I remember everything important. What's next?"},
    ]
    state.ctx_tokens = len(summary) // 4
    return f"compacted to a ~{fmt_n(len(summary) // 4)} token summary."


def explain_error(e):
    """Friendly message for API failures; also tracks rate-limit state."""
    if isinstance(e, openai.RateLimitError):
        code = ""
        try:
            body = e.body if isinstance(e.body, dict) else {}
            code = body.get("code") or body.get("error", {}).get("code") or ""
        except AttributeError:
            pass
        if "quota" in str(code) or "insufficient" in str(e).lower():
            state.limited_until = time.time() + 3600
            return "✖ your quota / credits ran out for this AI. add billing, or /switch to another AI."
        retry = _num(e.response.headers.get("retry-after")) or 30
        state.limited_until = time.time() + retry
        return f"✖ rate limited. this AI wants you to wait ~{int(retry)}s. (or /switch to another AI)"
    if isinstance(e, openai.AuthenticationError):
        return "✖ the API key was rejected. use /login to enter a new one."
    if isinstance(e, openai.APIConnectionError):
        return "✖ can't reach the provider. check your internet / base URL."
    if isinstance(e, openai.BadRequestError) and "context" in str(e).lower():
        return "✖ the conversation is too long for this model. use /compact or /clear."
    if isinstance(e, openai.NotFoundError):
        return "✖ that model wasn't found for this AI. pick another with /model."
    return f"✖ oops: {e}"
