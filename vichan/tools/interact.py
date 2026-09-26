"""Tools that talk to the user or change the agent's mode: questions, plan approval, skills."""
from rich import box
from rich.markdown import Markdown
from rich.panel import Panel

from .. import skills
from ..state import state
from ..ui import BLUSH, LAV, PINK, ROSE, ask, console
from . import tool


def _norm(opt):
    if isinstance(opt, str):
        return {"label": opt, "description": ""}
    return {"label": str(opt.get("label", "")), "description": str(opt.get("description", ""))}


@tool(
    "ask_user_question",
    "Ask the user a multiple-choice question when you need a decision or preference instead of guessing. "
    "Provide 2-4 concrete options; the user can also type their own answer.",
    {
        "question": {"type": "string"},
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"label": {"type": "string"}, "description": {"type": "string"}},
                "required": ["label"],
            },
        },
        "multi_select": {"type": "boolean", "description": "allow choosing several options"},
    },
    ["question", "options"],
    readonly=True,
    interactive=True,
)
def ask_user_question(question, options, multi_select=False):
    opts = [_norm(o) for o in options]
    console.print(Panel(question, title="♡ Vi-Chan asks", title_align="left", border_style=LAV, box=box.ROUNDED))
    for i, o in enumerate(opts, 1):
        desc = f" [blush]— {o['description']}[/]" if o["description"] else ""
        console.print(f"  [rose]{i}[/] {o['label']}{desc}")
    console.print(f"  [rose]{len(opts) + 1}[/] Other (type your own answer)")
    hint = "numbers separated by commas" if multi_select else "a number"
    while True:
        raw = ask(f"choose {hint}")
        if not raw:
            return "User skipped the question."
        picks = [p.strip() for p in raw.split(",")] if multi_select else [raw]
        if all(p.isdigit() and 1 <= int(p) <= len(opts) + 1 for p in picks):
            break
        console.print("[peach]  please enter a valid number[/]")
    answers = []
    for p in picks:
        i = int(p)
        answers.append(ask("your answer") if i == len(opts) + 1 else opts[i - 1]["label"])
    return "User answered: " + "; ".join(answers)


@tool(
    "exit_plan_mode",
    "Present your finished plan to the user for approval. Call this once you have researched enough. "
    "The plan should be concrete markdown: files to change, steps, risks.",
    {"plan": {"type": "string"}},
    ["plan"],
    readonly=True,
    interactive=True,
    plan_only=True,
)
def exit_plan_mode(plan):
    console.print(Panel(Markdown(plan), title="✎ plan", title_align="left", border_style=ROSE, box=box.ROUNDED))
    ans = ask("approve this plan? [y = yes, or type feedback]")
    if ans.lower() in ("y", "yes"):
        state.plan_mode = False
        console.print(f"[{PINK}]plan approved ♡ leaving plan mode[/]")
        return "User approved the plan. Plan mode is now off; go ahead and implement it."
    if not ans:
        return "User did not approve. Stay in plan mode and ask what they want changed."
    return f"User wants changes to the plan: {ans}. Revise it and call exit_plan_mode again."


@tool(
    "use_skill",
    "Load the full instructions of one of the user's skills (listed in the system prompt).",
    {"name": {"type": "string"}},
    ["name"],
    readonly=True,
)
def use_skill(name):
    body = skills.read_skill(name)
    return body if body is not None else f"error: no skill named '{name}'. available: {', '.join(skills.discover()) or 'none'}"
