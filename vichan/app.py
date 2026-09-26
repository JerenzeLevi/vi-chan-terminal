"""Main loop."""
import openai
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.text import Text

from . import auth
from .agent import explain_error, run_turn
from .commands import COMMANDS, dispatch
from .config import APP, CONFIG_DIR, load_config
from .mcp_client import MCPManager
from .state import state
from .ui import ART, PT_STYLE, ROSE, console
from .views import show_home, toolbar


def main():
    CONFIG_DIR.mkdir(exist_ok=True)
    state.cfg = load_config()
    state.mcp = MCPManager()
    state.messages = [{"role": "system", "content": ""}]

    if state.cfg["active"] in state.cfg["providers"]:
        auth.activate(state.cfg["active"])
        show_home()
    else:
        console.print(Text(f"\n{chr(10).join(ART)}\n   welcome to {APP}! let's log in first ♡", style=f"bold {ROSE}"))
        auth.login()
    for name, server in state.cfg["mcp_servers"].items():
        state.mcp.start(name, server)

    kb = KeyBindings()

    @kb.add("s-tab")
    def _(event):
        state.plan_mode = not state.plan_mode
        event.app.invalidate()

    session = PromptSession(
        history=FileHistory(str(CONFIG_DIR / "history")),
        bottom_toolbar=toolbar,
        style=PT_STYLE,
        key_bindings=kb,
        completer=WordCompleter(list(COMMANDS), WORD=True),
        complete_while_typing=True,
    )

    while True:
        try:
            text = session.prompt(lambda: [(f"fg:{ROSE} bold", "\nvi-chan " + ("✎ plan " if state.plan_mode else "") + "♡ › ")]).strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text.startswith("/"):
            if not dispatch(text):
                break
            continue
        if not state.client:
            console.print("[peach]not logged in yet, use /login or /switch ♡[/]")
            continue
        checkpoint = len(state.messages)
        state.messages.append({"role": "user", "content": text})
        try:
            run_turn()
        except KeyboardInterrupt:
            del state.messages[checkpoint:]
            console.print("[peach]stopped ✧[/]")
        except openai.OpenAIError as e:
            del state.messages[checkpoint:]
            console.print(f"[red]{explain_error(e)}[/]")
        except Exception as e:  # noqa: BLE001
            del state.messages[checkpoint:]
            console.print(f"[red]oops: {e}[/]")
    state.mcp.shutdown()
    console.print("[pink]bye bye~ ♡[/]")
