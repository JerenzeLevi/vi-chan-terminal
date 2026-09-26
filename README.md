# Vi-Chan Terminal ♡

A kawaii, Claude-Code-style AI agent for your terminal. Bring any API key.

```
pip install -r requirements.txt
python cutie.py
```

First run: pick an AI, paste your API key, pick a model. Works with OpenAI, Anthropic, Gemini, OpenRouter, Groq, Ollama, or any OpenAI-compatible URL.

## Commands
`/login` `/logout` `/switch` `/model` `/config` `/usage` `/plan` `/mcp` `/skills` `/compact` `/clear` `/cd` `/help` `/exit`
`shift+tab` toggles plan mode.

## What the AI can do
- Files: read, write, edit (exact replace), list, glob, grep, run shell commands (asks first, shows a diff).
- Office: create/read `.xlsx`, `.docx`, `.pptx`.
- Images: `generate_image` saves a file (needs an OpenAI or Gemini key; folder set in `/config images_dir`).
- Ask you multiple-choice questions, and plan-then-approve (`/plan`).
- MCP tools: `/mcp add playwright` gives it a real browser.

## Your own skills
Create `~/.cutie-term/skills/<name>/SKILL.md` (or `./.cutie/skills/<name>/SKILL.md`):

```
---
name: my-skill
description: when to use it
---
Instructions the AI follows when it loads this skill.
```

Project instructions: put a `CUTIE.md` (or `CLAUDE.md` / `AGENTS.md`) in the folder you run it from.

Config and keys live in `~/.cutie-term/config.json` (plain text, keep it private).

## License & credit
Apache License 2.0 © 2026 Jerenze Levi ([@JerenzeLevi](https://github.com/JerenzeLevi)). Forks are welcome, but you must keep the
[LICENSE](LICENSE) and [NOTICE](NOTICE) and credit the original author with a link to this repo. The "Vi-Chan" name and persona are not licensed for forks.
Found a security issue? See [SECURITY.md](SECURITY.md).
