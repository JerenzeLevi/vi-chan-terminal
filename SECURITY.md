# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Use GitHub's private reporting instead: **Security → Report a vulnerability** on
https://github.com/JerenzeLevi/vi-chan-terminal/security/advisories/new

Include what you found, how to reproduce it, and the impact. I'll acknowledge reports as soon as I can and
credit you in the fix unless you prefer to stay anonymous. Please give me reasonable time to fix an issue before disclosing it.

## Supported versions

Only the latest commit on `main` receives security fixes.

## How Vi-Chan protects you

- **Approval before action.** Writing or editing files, running shell commands, generating images, editing Office files,
  and every MCP tool that isn't read-only all ask first. Edits show a diff. "Always allow" lasts only for the current session,
  and `auto_approve` is off by default.
- **Plan mode.** Only read-only tools are offered until you approve a plan.
- **No telemetry.** Vi-Chan talks only to the AI provider you log in with and to any MCP servers you add.
- **Keys stay local.** API keys are stored in `~/.cutie-term/config.json` (owner-only permissions where the OS supports it),
  entered hidden, and never written to the project folder or sent anywhere except your chosen provider.

## Things to know

- The config file stores keys in **plain text**. Keep your home folder private and never commit or share that file.
- Auto-approve, and any command you approve, run with **your** user's permissions. Read what you approve.
- MCP servers are programs that run on your machine. Only add servers you trust (`/mcp add ...`).
- File contents and command output are sent to your AI provider as part of the conversation. Don't point Vi-Chan at secrets
  you don't want your provider to see.
- Project instruction files (`CUTIE.md`, `CLAUDE.md`, `AGENTS.md`) and skills are fed to the model. Review them in
  repositories you don't trust, since they can contain prompt injection.
