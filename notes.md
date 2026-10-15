# Project Notes

## Day 1: Setup

- Installed Python 3.13, VS Code, Git; created venv and GitHub repo
- Stored the Gemini API key in .env and added .env to .gitignore

### Problems and fixes
- PowerShell blocked venv activation (execution policy) -> switched terminal to Command Prompt
- "pip is not recognized" -> venv was not active; activate it in every new terminal
- Connection reset error during the big install -> used --default-timeout, --retries and installed packages in smaller groups
- Gemini 404 (model retired) -> updated the model name
- Gemini 503 (server busy) -> retried a few minutes later
- Two git commands pasted together caused an error -> run commands one at a time