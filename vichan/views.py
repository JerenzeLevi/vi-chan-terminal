"""Things printed to the screen: home panel, usage panel, bottom toolbar."""
import os

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import APP, PROVIDERS
from .state import ctx_bar, ctx_pct, ctx_window, limit_pairs, limit_status, state
from .ui import ART, BLUSH, LAV, PINK, ROSE, console, fmt_n


def display_name(pid):
    if not pid:
        return ""
    return pid if pid.startswith("custom:") else PROVIDERS.get(pid, {}).get("label", pid)


def show_home():
    art = Text("\n".join(ART), style=f"bold {ROSE}")
    info = Table.grid(padding=(0, 1))
    info.add_row(Text(APP, style=f"bold {ROSE}"), "")
    info.add_row(Text("your tiny terminal AI ♡", style=PINK), "")
    info.add_row(Text(""), "")
    if state.client:
        info.add_row(Text("AI", style=LAV), Text(display_name(state.provider), style=BLUSH))
        info.add_row(Text("model", style=LAV), Text(state.model, style=BLUSH))
        info.add_row(Text("context", style=LAV), Text(f"~{fmt_n(ctx_window())} tokens", style=BLUSH))
    info.add_row(Text("folder", style=LAV), Text(os.getcwd(), style=BLUSH))
    grid = Table.grid(padding=(0, 3))
    grid.add_row(art, info)
    console.print(Panel(grid, border_style=PINK, box=box.ROUNDED, padding=(1, 2)))
    console.print(Text("  tips: just type what you want ♡ · /help for commands · shift+tab = plan mode · /usage for limits", style=BLUSH))


def show_usage():
    _, lim = limit_status()
    t = Table.grid(padding=(0, 2))
    t.add_row(Text("AI", style=LAV), f"{display_name(state.provider)} · {state.model}")
    t.add_row(Text("requests", style=LAV), str(state.requests))
    t.add_row(Text("tokens in", style=LAV), f"{state.session_in:,}")
    t.add_row(Text("tokens out", style=LAV), f"{state.session_out:,}")
    t.add_row(Text("context", style=LAV), f"{ctx_bar()} {ctx_pct()}%  ({state.ctx_tokens:,} / ~{ctx_window():,})")
    t.add_row(Text("limits", style=LAV), lim)
    for lbl, rem, lim_ in limit_pairs():
        t.add_row(Text(f"  {lbl} left", style=LAV), f"{rem:,.0f}" + (f" of {lim_:,.0f}" if lim_ else ""))
    if not limit_pairs():
        t.add_row(Text(""), Text("this provider doesn't report limits; I'll warn you when it says 429.", style=BLUSH))
    console.print(Panel(t, title="♡ usage", title_align="left", border_style=PINK, box=box.ROUNDED))


def toolbar():
    if not state.client:
        return " ♡ not logged in · /login "
    _, lim = limit_status()
    parts = [f"♡ {display_name(state.provider)} · {state.model}"]
    if state.plan_mode:
        parts.append("✎ PLAN MODE")
    parts.append(f"ctx {ctx_pct()}%")
    parts.append(f"↑{fmt_n(state.session_in)} ↓{fmt_n(state.session_out)}")
    parts.append(lim)
    if state.mcp and state.mcp.servers:
        ready = sum(1 for s in state.mcp.servers.values() if s["status"] == "ready")
        parts.append(f"mcp {ready}/{len(state.mcp.servers)}")
    return " " + " │ ".join(parts) + " "
