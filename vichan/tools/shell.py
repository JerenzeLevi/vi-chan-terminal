"""Shell tool."""
import subprocess

from . import tool


@tool(
    "run_command",
    "Run a shell command in the working directory and return its output. Default timeout 120s (max 600).",
    {"command": {"type": "string"}, "timeout": {"type": "integer"}},
    ["command"],
    approval=True,
)
def run_command(command, timeout=120):
    timeout = max(1, min(int(timeout), 600))
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return f"error: command timed out after {timeout}s"
    return ((r.stdout or "") + (r.stderr or ""))[-8000:] or f"(exit {r.returncode})"
