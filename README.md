# Vi-Chan Terminal ♡

A kawaii, jolly, curious AI agent that lives in your terminal. Bring any AI's API key and Vi-Chan can read and edit your files, run commands,
browse the web, make images and build Excel / Word / PowerPoint files, always asking before she changes anything.

```
  /\_/\
 ( ˶•ᴗ•˶)   Vi-Chan Terminal
  >  ♡ <
```

---

## ✨ ELI5: get her running in 3 steps

Think of Vi-Chan as a cute chat window that lets an AI help with your computer. She needs two things: **Python** (a free program that runs her) and an **API key** (a secret password that lets her talk to an AI).

**1. Install Python** (once): download it from [python.org/downloads](https://www.python.org/downloads/). On Windows, tick **"Add Python to PATH"** during install.

**2. Open a terminal and paste this** (Windows: search "Terminal" or "PowerShell"; Mac: search "Terminal"):

```
pip install git+https://github.com/JerenzeLevi/vi-chan-terminal.git
```

**3. Type `vichan` and press Enter.** She'll ask you to pick an AI, paste your API key, and choose a model. Then just talk to her! ♡

> **What's an API key?** A long secret text you get from an AI company's website. It is *not* the same as a ChatGPT Plus or Claude Pro subscription; those don't include one.
> Get a key here (pay-as-you-go, cents for casual use):
> - **Google Gemini**, has a **free tier**: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
> - **OpenAI (ChatGPT models)**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
> - **Anthropic (Claude)**: [console.anthropic.com](https://console.anthropic.com)
> - **OpenRouter** (one key, many models): [openrouter.ai/keys](https://openrouter.ai/keys)
> - **Ollama**: no key at all, runs models on your own computer: [ollama.com](https://ollama.com)
>
> Treat your key like a password. Never share it or post it online.

Stuck? Jump to [Troubleshooting](#-troubleshooting).

---

## 🛠 Technical install

**Requirements:** Python 3.9+, a terminal with UTF-8 / emoji support (Windows Terminal, iTerm2, GNOME Terminal…). Node.js is optional and only needed for MCP servers like Playwright.

### Option A: `pipx` (recommended: isolated, adds the `vichan` command to your PATH)

```bash
pip install --user pipx
pipx ensurepath          # then close and reopen your terminal
pipx install git+https://github.com/JerenzeLevi/vi-chan-terminal.git
vichan
```

### Option B: plain `pip`

```bash
pip install git+https://github.com/JerenzeLevi/vi-chan-terminal.git
vichan            # or: vi-chan   or: python -m vichan.app
```

### Option C: from a clone (for hacking on it)

```bash
git clone https://github.com/JerenzeLevi/vi-chan-terminal.git
cd vi-chan-terminal
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1      macOS/Linux:  source .venv/bin/activate
pip install -e .
vichan            # or simply: python cutie.py
```

**Update:** `pipx upgrade vi-chan-terminal` (or `pip install -U git+https://github.com/JerenzeLevi/vi-chan-terminal.git`)
**Uninstall:** `pipx uninstall vi-chan-terminal` (or `pip uninstall vi-chan-terminal`). Your saved keys stay in `~/.cutie-term/`; delete that folder to remove them.

Run `vichan` **inside the folder you want to work in**; that folder is where she reads and writes files.

### First run
1. `vichan` → pick a provider → paste your API key (hidden as you type) → choose a model (Enter = default).
2. Talk to her in plain language: *"summarise this project"*, *"fix the bug in app.py"*, *"make a budget spreadsheet"*.
3. She asks before edits, commands and image generation. Answer `y`, `N`, or `a` (always, this session).

Any OpenAI-compatible provider works: pick **Custom** and enter its base URL. The smarter the model, the smarter she is.

---

## 💬 Commands

| Command | What it does |
|---|---|
| `/login` `/logout` `/switch` | pick an AI + API key, forget it, or change to another AI |
| `/model` | show the current model and pick another (`/model gpt-4o`, or `/model pro` to search) |
| `/config` | settings: auto-approve, images folder, image model, step limit, footer |
| `/plan` (or `shift+tab`) | plan mode: she researches and shows a plan; nothing changes until you approve |
| `/mcp` | add tool servers, e.g. `/mcp add playwright` for a real browser (needs Node.js) |
| `/skills` | list built-in abilities and your own skills |
| `/usage` | tokens used, context fullness, rate limits |
| `/compact` `/clear` | summarise the chat to save space, or forget it |
| `/cd <folder>` | change working folder |
| `/vi-chan` | about her, her creator, and the story of her name |
| `/help` `/exit` | help / quit |

## 🧰 What she can do
- **Files:** read, write, precisely edit (with a red/green diff), list, glob, grep, run shell commands.
- **Office:** create, read and edit `.xlsx`, `.docx`, `.pptx`.
- **Images:** generate an image into a folder you choose (needs an OpenAI or Gemini key; set the folder with `/config images_dir`).
- **Ask & plan:** multiple-choice questions instead of guessing; plan-then-approve.
- **MCP tools:** connect any MCP server (browser, filesystem, fetch…).
- **Live stats:** the thinking line and footer show time and tokens, and warn you before you hit context or rate limits.

## 📝 Your own skills & project notes
Create `~/.cutie-term/skills/<name>/SKILL.md` (or `./.cutie/skills/<name>/SKILL.md`):

```
---
name: my-skill
description: when to use it
---
Instructions Vi-Chan follows when she loads this skill.
```

Put a `CUTIE.md` (or `CLAUDE.md` / `AGENTS.md`) in a project folder to give her standing instructions there.

## 🔒 Safety in one minute
Vi-Chan asks before writing, editing, running commands or using most MCP tools. Your key is stored **in plain text** at `~/.cutie-term/config.json`, so keep your account private. Full details: [SECURITY.md](SECURITY.md).

## 🩹 Troubleshooting

| Problem | Fix |
|---|---|
| `vichan` is not recognized | Close and reopen the terminal. With pipx run `pipx ensurepath`. With pip, add Python's `Scripts` folder to PATH, or run `python -m vichan.app`. |
| `pip` is not recognized (Windows) | Reinstall Python and tick "Add Python to PATH", or use `py -m pip install ...`. |
| Weird boxes instead of hearts / borders | Use Windows Terminal (not the old console) or another UTF-8 terminal. |
| "key was rejected" | Re-run `/login`. Check you copied the whole key, and that it's an *API key* (not a subscription login). |
| "model wasn't found" | Pick a valid one with `/model`. |
| "rate limited" / "quota" | Wait a moment, add billing/credits, or `/switch` to another AI. |
| Images fail | You need an OpenAI or Gemini key. Set `/config image_model` if your provider uses a different image model. |
| `/mcp add playwright` stays "connecting" | Needs Node.js; the first run downloads the browser tools, so give it a minute. Check `/mcp`. |

## 📜 License & credit
Apache License 2.0 © 2026 Jerenze Levi ([@JerenzeLevi](https://github.com/JerenzeLevi)). Forks are welcome, but you must keep the
[LICENSE](LICENSE) and [NOTICE](NOTICE) and credit the original author with a link to this repo. The "Vi-Chan" name and persona are not licensed for forks.
Found a security issue? See [SECURITY.md](SECURITY.md).
