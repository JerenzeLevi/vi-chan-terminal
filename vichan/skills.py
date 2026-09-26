"""User skills: folders containing SKILL.md (with name/description frontmatter).

Looked up in ./.cutie/skills/ and ~/.cutie-term/skills/. The AI sees the list and loads one with use_skill.
"""
from pathlib import Path

from .config import USER_SKILLS_DIR

BUILTIN_CAPABILITIES = [
    ("excel", "create / read / update .xlsx spreadsheets (create_xlsx, read_xlsx, update_xlsx_cells)"),
    ("word", "create / read .docx documents (create_docx, read_docx)"),
    ("powerpoint", "create / read .pptx decks (create_pptx, read_pptx)"),
    ("images", "generate an image file with the AI (generate_image; needs OpenAI or Gemini key)"),
    ("browser", "drive a real browser via MCP (/mcp add playwright)"),
    ("ask", "ask you multiple-choice questions (ask_user_question)"),
    ("plan", "plan mode: research first, approve a plan before any change (/plan or shift+tab)"),
]


def _parse(path):
    meta, body = {}, path.read_text(encoding="utf-8", errors="replace")
    if body.startswith("---"):
        _, _, rest = body.partition("---")
        head, _, body = rest.partition("---")
        for line in head.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip().lower()] = v.strip().strip("\"'")
    return meta, body.strip()


def discover():
    """name -> {description, path}. Project skills win over user skills."""
    found = {}
    for base in (Path.cwd() / ".cutie" / "skills", USER_SKILLS_DIR):
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            f = d / "SKILL.md"
            if f.is_file():
                meta, _ = _parse(f)
                found.setdefault(meta.get("name") or d.name, {"description": meta.get("description", ""), "path": f})
    return found


def read_skill(name):
    skill = discover().get(name)
    if not skill:
        return None
    return _parse(skill["path"])[1]
