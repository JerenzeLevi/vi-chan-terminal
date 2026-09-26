"""File tools: read, write, edit, list, glob, grep."""
import fnmatch
import os
import re
from pathlib import Path

from rich.console import Group
from rich.text import Text

from . import tool

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def _walk(root):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            yield Path(dp) / fn


def _edit_preview(a):
    lines = [Text(f"edit {a.get('path', '')}", style="bold")]
    for ln in str(a.get("old_string", "")).splitlines()[:12]:
        lines.append(Text(f"- {ln}", style="red"))
    for ln in str(a.get("new_string", "")).splitlines()[:12]:
        lines.append(Text(f"+ {ln}", style="green"))
    return Group(*lines)


def _write_preview(a):
    body = str(a.get("content", "")).splitlines()
    lines = [Text(f"write {a.get('path', '')} ({len(body)} lines)", style="bold")]
    lines += [Text(f"+ {ln}", style="green") for ln in body[:12]]
    if len(body) > 12:
        lines.append(Text(f"  … {len(body) - 12} more lines", style="dim"))
    return Group(*lines)


@tool(
    "read_file",
    "Read a text file (first 30000 chars).",
    {"path": {"type": "string"}},
    ["path"],
    readonly=True,
)
def read_file(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")[:30000]


@tool(
    "write_file",
    "Create a new file or fully overwrite one. Prefer edit_file for changes to existing files.",
    {"path": {"type": "string"}, "content": {"type": "string"}},
    ["path", "content"],
    approval=True,
    preview=_write_preview,
)
def write_file(path, content):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"wrote {len(content)} chars to {path}"


@tool(
    "edit_file",
    "Replace exact text in a file. old_string must be unique unless replace_all is true.",
    {
        "path": {"type": "string"},
        "old_string": {"type": "string"},
        "new_string": {"type": "string"},
        "replace_all": {"type": "boolean"},
    },
    ["path", "old_string", "new_string"],
    approval=True,
    preview=_edit_preview,
)
def edit_file(path, old_string, new_string, replace_all=False):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    n = text.count(old_string)
    if n == 0:
        return "error: old_string not found"
    if n > 1 and not replace_all:
        return f"error: old_string matches {n} times; add context or set replace_all"
    p.write_text(text.replace(old_string, new_string), encoding="utf-8")
    return f"edited {path} ({n} replacement{'s' if n > 1 else ''})"


@tool("list_dir", "List a directory.", {"path": {"type": "string"}}, readonly=True)
def list_dir(path="."):
    return "\n".join(f"{'[dir] ' if e.is_dir() else ''}{e.name}" for e in sorted(Path(path).iterdir()))


@tool(
    "glob",
    "Find files by glob pattern, e.g. **/*.py.",
    {"pattern": {"type": "string"}, "path": {"type": "string"}},
    ["pattern"],
    readonly=True,
)
def glob(pattern, path="."):
    hits = [str(f) for f in Path(path).glob(pattern) if not SKIP_DIRS & set(f.parts)]
    return "\n".join(sorted(hits)[:200]) or "no matches"


@tool(
    "grep",
    "Regex search inside files. Optional glob filters file names (e.g. *.py).",
    {"pattern": {"type": "string"}, "path": {"type": "string"}, "glob": {"type": "string"}},
    ["pattern"],
    readonly=True,
)
def grep(pattern, path=".", glob="*"):
    rx = re.compile(pattern)
    out = []
    for f in _walk(path):
        if not fnmatch.fnmatch(f.name, glob):
            continue
        try:
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if rx.search(line):
                    out.append(f"{f}:{i}: {line.strip()[:200]}")
                    if len(out) >= 100:
                        return "\n".join(out) + "\n(truncated)"
        except (UnicodeDecodeError, OSError):
            continue
    return "\n".join(out) or "no matches"
