"""Theme, formatting helpers, and small interactive prompts."""
import sys

from prompt_toolkit.styles import Style
from rich.console import Console
from rich.theme import Theme

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

PINK, ROSE, BLUSH, LAV, MINT, PEACH = "#ff9ecf", "#ff6fb1", "#ffc8e2", "#c9b6ff", "#9dffd6", "#ffcfa8"
console = Console(theme=Theme({"pink": PINK, "rose": ROSE, "blush": BLUSH, "lav": LAV, "mint": MINT, "peach": PEACH}))
PT_STYLE = Style.from_dict(
    {
        "bottom-toolbar": "bg:#ffd6ea #8a2b5c noreverse",
        "bottom-toolbar.text": "bg:#ffd6ea #8a2b5c",
        "completion-menu.completion": "bg:#ffe3f1 #8a2b5c",
        "completion-menu.completion.current": "bg:#ff9ecf #ffffff",
    }
)

ART = [
    "  /\\_/\\   ",
    " ( ˶•ᴗ•˶) ",
    "  >  ♡ <  ",
]

THINKING_WORDS = [
    "Thinking", "Awakening", "Ascending", "Transcending", "Manifesting", "Channeling", "Unleashing",
    "Invoking", "Conjuring", "Perceiving", "Foreseeing", "Envisioning", "Realizing", "Discovering",
    "Unraveling", "Deciphering", "Deducing", "Probing", "Pursuing", "Seeking", "Reckoning",
    "Calculating", "Adapting", "Evolving", "Overcoming", "Delving",
]


def fmt_n(n):
    n = float(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n / 1000:.0f}k"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(int(n))


def fmt_time(s):
    return f"{s:.1f}s" if s < 60 else f"{int(s // 60)}m{int(s % 60):02d}s"


def ask(prompt):
    return console.input(f"[mint]  {prompt} › [/]").strip()


def choose(title, options, current=None, hint=""):
    """Numbered single-choice menu. Returns the chosen index, or None if cancelled."""
    console.print(f"\n[lav]{title}[/]")
    for i, label in enumerate(options, 1):
        mark = " [rose]★ current[/]" if current is not None and i - 1 == current else ""
        console.print(f"  [rose]{i}[/] {label}{mark}")
    if hint:
        console.print(f"[blush]  {hint}[/]")
    while True:
        raw = ask("pick a number (enter to cancel)")
        if not raw:
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
