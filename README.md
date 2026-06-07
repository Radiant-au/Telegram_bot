# 🤖 Technologia Club Telegram Bot

A Telegram bot for managing university club groups with AI chat, member lookup, Google Sheets integration, quizzes, announcements, and owner-only admin tools.

## ✨ Features

### 🎯 Core Features
- **AI Chat Integration** - Multi-provider LLM support with token-based usage limits
- **New Member Announcements** - Automatic welcome messages with user data from Google Sheets
- **Admin Panel** - Owner-only command interface for announcements and polls
- **@all Mentions** - Notify all members with admin-only access
- **Google Sheets Integration** - Store and retrieve member information
- **Quiz Generator** - AI-assisted quiz generation in a dedicated topic

### 🤖 AI Features
- `/miki <question>` - Ask the AI anything
- `/tokens` - Check remaining daily AI tokens
- `/switchllm` - Switch between configured LLM providers
- `/llmstatus` - Show active and available LLM providers
- Token system: 10 tokens per day for regular users
- Unlimited tokens for admins
- Daily token reset at midnight
- Supported providers: Gemini, DeepSeek, OpenRouter, and Qwen

### 👥 Member Management
- Automatic member announcements in dedicated topic
- `/getinfo @username` - View member details (admin-only)
- Google Sheets integration for member data
- `@all` mention system for group-wide notifications

### 📢 Admin Tools
- `/start` - Admin panel (owner-only)
- Create announcements
- Create polls
- Post to specific topics/channels

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Google Sheets API credentials
- At least one AI API key if AI features should be enabled

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd telegram-bot
```

2. **Install dependencies**
```bash
uv sync
```

If you are not using `uv`, install the requirements directly:

```bash
python -m pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# Required
TELEGRAM_TOKEN=your_telegram_bot_token
BOT_OWNER_ID=your_telegram_user_id
SHEET_NAME=your_google_sheet_name

# Recommended for local/debug runs
GOOGLE_CREDENTIALS_FILE=secrets/credential.json

# Alternative for deployment platforms
GOOGLE_CREDENTIALS={"type":"service_account","project_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"..."}

# Optional (AI features)
GEMINI_API_KEY=your_gemini_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
QWEN_API_KEY=your_qwen_api_key
DEFAULT_LLM=gemini

# Group settings
GROUP_CHAT_ID=your_group_chat_id
ANNOUNCEMENT_TOPIC_ID=2
QUIZ_TOPIC_ID=2
MEMBER_TOPIC_ID=2

# Deployment
MODE=polling
WEBHOOK_URL=https://your-domain.com
PORT=8080
```

4. **Run the bot**

For local development (polling mode):
```bash
uv run python main.py
```

For production (webhook mode):
```bash
MODE=webhook python main.py
```

## 📋 Configuration Guide

### Getting Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the token provided

### Getting Your User ID
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your user ID

### Google Sheets Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Sheets API
4. Create service account credentials
5. Download JSON key file
6. Put the JSON file at `secrets/credential.json`
7. Set `GOOGLE_CREDENTIALS_FILE=secrets/credential.json` in `.env`
8. Share your Google Sheet with the service account email

For deployment platforms that cannot use local files, set `GOOGLE_CREDENTIALS` to the full service account JSON instead. Keep the private key newlines escaped as `\n`.

**Required Sheet Columns:**
- Name
- Telegram username
- Phone
- Major
- Year
- What fields are u interested in?

### AI API Keys (Optional)
Add one or more provider keys to `.env`:

```env
GEMINI_API_KEY=
DEEPSEEK_API_KEY=
OPENROUTER_API_KEY=
QWEN_API_KEY=
DEFAULT_LLM=gemini
```

AI commands are enabled only when at least one provider key is configured.

## 🎮 Usage

### User Commands
```
/miki <question>     - Ask AI anything
/tokens              - Check remaining AI tokens
/switchllm           - Switch LLM provider
/llmstatus           - Show LLM provider status
/quiz                - Generate a quiz
/help                - Show help message
```

### Admin Commands
```
/start               - Open admin panel (owner only)
/getinfo @username   - Get user info from sheets
@all <message>       - Mention all members
```

### AI Examples
```
/miki What is Python?
/miki Explain machine learning simply
/miki Write a haiku about coding
/miki Help me debug this error
```

## 🏗️ Project Structure

```
telegram-bot/
├── main.py                # Main bot entry point
├── config.py              # Configuration management
├── ai.py                  # AI manager and token tracking
├── sheets.py              # Google Sheets integration
├── utils.py               # Utility functions
├── llm/                   # LLM provider implementations
├── requirements.txt       # Python dependencies
├── pyproject.toml         # uv/Python project metadata
├── handlers/
│   ├── __init__.py
│   ├── admin.py          # Admin panel handlers
│   ├── ai_handler.py     # AI command handlers
│   ├── quiz_handler.py   # Quiz command handlers
│   └── members.py        # Member management handlers
├── secrets/
│   └── credential.json   # Local Google service account file, ignored by git
└── .env                   # Environment variables (create this)
```

## 🌐 Deployment

### Deploy to Render/Railway/Fly.io

1. **Set environment variables** in your platform's dashboard
2. **Set MODE** to `webhook`
3. **Set WEBHOOK_URL** to your deployment URL
4. **Deploy** the application

### Deploy to Heroku

```bash
# Install Heroku CLI
heroku login
heroku create your-app-name

# Set environment variables
heroku config:set TELEGRAM_TOKEN=your_token
heroku config:set BOT_OWNER_ID=your_id
# ... set all other variables

# Deploy
git push heroku main
```

### Local Development

```bash
# Use polling mode for testing
MODE=polling python main.py
```

### VS Code / Antigravity Debugging

Use one of the launch configurations in `.vscode/launch.json`:

- `🤖 Run Bot (INFO)`
- `🐛 Debug Bot (DEBUG)`
- `📝 Debug Bot → bot.log`

The workspace is configured to use `.venv/bin/python`. If the debug console shows `/home/radiant/.pyenv/.../python`, re-select the interpreter or restart the IDE so it picks up `.vscode/settings.json`.

## 🔧 Troubleshooting

### Bot not responding
- Check if bot token is correct
- Verify bot is admin in the group
- Check console for error messages

### Google Sheets not working
- Verify service account email has access to sheet
- Check sheet name matches exactly
- Ensure all required columns exist
- Prefer `GOOGLE_CREDENTIALS_FILE=secrets/credential.json` for local/debug runs
- If using `GOOGLE_CREDENTIALS`, keep private key newlines escaped as `\n`

### Debugger crashes before startup
- Confirm the debugger uses `.venv/bin/python`
- Confirm `.env` exists in the project root
- Use `GOOGLE_CREDENTIALS_FILE` if the debugger has trouble parsing JSON credentials from `.env`

### AI not working
- Check if at least one AI API key is set
- Verify API key is valid
- Check if AI_ENABLED prints `True` on startup

### Webhook issues
- Ensure WEBHOOK_URL is publicly accessible
- Check if PORT matches your platform's requirements
- Verify SSL certificate is valid

## 🛡️ Security Notes

- Never commit `.env` file to version control
- Keep API keys and credentials secure
- Regularly rotate API keys
- Use environment variables for all secrets

## 📝 Token System

### Regular Users
- 10 tokens per day
- Tokens reset at midnight
- One token per `/miki` command

### Admins
- Unlimited tokens
- No daily limits
- Creator and administrator status

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues or questions:
- Open an issue on GitHub
- Contact the bot owner
- Check the troubleshooting section

## 🙏 Credits

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Google Sheets API](https://developers.google.com/sheets/api)
- Gemini, DeepSeek, OpenRouter, and Qwen LLM providers

---

Made with ❤️ for Technologia Club
