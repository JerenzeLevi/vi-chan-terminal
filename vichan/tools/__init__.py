"""Tool registry. Built-in tools register themselves with @tool; MCP tools are added dynamically."""
from dataclasses import dataclass
from typing import Callable, Optional

from ..state import state


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict  # JSON schema
    fn: Callable
    readonly: bool = False  # safe to use in plan mode, never needs approval
    approval: bool = False  # ask the user before running
    interactive: bool = False  # talks to the user, so no spinner while it runs
    plan_only: bool = False  # only offered while in plan mode
    preview: Optional[Callable] = None  # args -> renderable shown at the approval prompt


BUILTIN = {}


def tool(name, description, properties=None, required=(), **flags):
    def deco(fn):
        schema = {"type": "object", "properties": properties or {}, "required": list(required)}
        BUILTIN[name] = Tool(name, description, schema, fn, **flags)
        return fn

    return deco


def available_tools():
    """name -> Tool for everything the AI may use right now (respects plan mode)."""
    from .. import skills

    tools = {}
    have_skills = bool(skills.discover())
    for t in BUILTIN.values():
        if t.plan_only and not state.plan_mode:
            continue
        if state.plan_mode and not t.readonly:
            continue
        if t.name == "use_skill" and not have_skills:
            continue
        tools[t.name] = t
    if state.mcp:
        for t in state.mcp.tools():
            if not state.plan_mode or t.readonly:
                tools[t.name] = t
    return tools


def schemas(tools):
    return [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}} for t in tools.values()]


from . import files, images, interact, office, shell  # noqa: E402,F401  (registers the tools)
