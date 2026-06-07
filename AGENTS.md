# Repository Guidelines

## Project Structure & Module Organization
This repository is a Python 3.12 Telegram bot. Core runtime files live at the repo root:
- `main.py` starts the bot.
- `config.py`, `utils.py`, `memory_manager.py`, `sheets.py`, and `ai.py` hold shared logic.
- `handlers/` contains command handlers (`admin.py`, `ai_handler.py`, `members.py`, `quiz_handler.py`).
- `llm/` contains provider adapters (`gemini.py`, `deepseek.py`, `openrouter.py`, `qwen.py`).
- `secrets/credential.json` is for local Google service-account credentials and is ignored by git.

Keep new code close to the feature it supports. Prefer adding a new handler or provider module instead of expanding `main.py`.

## Build, Test, and Development Commands
- `uv sync` installs dependencies from `pyproject.toml` and `uv.lock`.
- `uv run python main.py` runs the bot locally in the default polling mode.
- `MODE=webhook python main.py` starts the webhook path for deployment-style testing.
- `python -m pip install -r requirements.txt` is the fallback when `uv` is unavailable.

## Coding Style & Naming Conventions
Follow standard Python style: 4-space indentation, `snake_case` for functions and modules, `PascalCase` for classes, and uppercase environment variables such as `TELEGRAM_TOKEN`.
Use descriptive module names that match the existing layout (`quiz_handler.py`, `openrouter.py`). Keep functions small and prefer explicit names over abbreviations. No formatter or linter is configured in the repo, so make changes consistent with nearby code.

## Testing Guidelines
There is no committed automated test suite yet. Before opening a PR, at minimum run the bot locally and exercise the changed command flow in Telegram.
If you add tests, place them under `tests/` and name them `test_*.py`. Prefer deterministic unit tests for handler logic and provider selection; avoid relying on live API calls unless the test is explicitly marked as integration-only.

## Commit & Pull Request Guidelines
Recent commits use short, imperative summaries such as `Add quiz feature` or `Fix debug environment setup`. Keep commit messages similarly concise and action-oriented.
PRs should include a brief summary, the user-visible behavior changed, and any setup or environment changes. Link related issues when applicable and add screenshots or chat logs only when they help verify Telegram-facing behavior.

## Security & Configuration Tips
Do not commit `.env` files, API keys, or service-account JSON. Use `.env.example` as the starting point for local configuration and verify that any new secrets are documented there.
