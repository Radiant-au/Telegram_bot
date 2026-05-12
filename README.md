# 🤖 Technologia Club Telegram Bot

A feature-rich Telegram bot for managing university club groups with AI chat capabilities, member management, and administrative tools.

## ✨ Features

### 🎯 Core Features
- **AI Chat Integration** - Powered by Google Gemini AI with token-based usage limits
- **New Member Announcements** - Automatic welcome messages with user data from Google Sheets
- **Admin Panel** - Owner-only command interface for announcements and polls
- **@all Mentions** - Notify all members with admin-only access
- **Fun Interactions** - Greeting responses and blame game features
- **Google Sheets Integration** - Store and retrieve member information

### 🤖 AI Features
- `/miki <question>` - Ask the AI anything
- Token system: 3 tokens per day for regular users
- Unlimited tokens for admins
- Daily token reset at midnight
- Powered by Google Gemini 2.0 Flash

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
- Python 3.8+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Google Sheets API credentials
- Gemini API key (optional, for AI features)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd telegram-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
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
GOOGLE_CREDENTIALS={"type": "service_account", ...}
SHEET_NAME=your_google_sheet_name

# Optional (AI features)
GEMINI_API_KEY=your_gemini_api_key

# Group settings
GROUP_CHAT_ID=your_group_chat_id
ANNOUNCEMENT_TOPIC_ID=2
MEMBER_TOPIC_ID=2

# Deployment
MODE=webhook  # or 'polling' for local
WEBHOOK_URL=https://your-domain.com
PORT=8080
```

4. **Run the bot**

For local development (polling mode):
```bash
MODE=polling python bot.py
```

For production (webhook mode):
```bash
python bot.py
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
6. Copy entire JSON content to `GOOGLE_CREDENTIALS` in `.env`
7. Share your Google Sheet with the service account email

**Required Sheet Columns:**
- Name
- Telegram username
- Phone
- Major
- Year
- What fields are u interested in?

### Gemini API Key (Optional)
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API key
3. Add to `.env` as `GEMINI_API_KEY`

## 🎮 Usage

### User Commands
```
/miki <question>     - Ask AI anything
/tokens              - Check remaining AI tokens
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
├── bot.py                 # Main bot entry point
├── config.py              # Configuration management
├── ai.py                  # AI/Gemini integration
├── sheets.py              # Google Sheets integration
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── handlers/
│   ├── __init__.py
│   ├── admin.py          # Admin panel handlers
│   ├── ai.py             # AI command handlers
│   ├── fun.py            # Fun interaction handlers
│   └── members.py        # Member management handlers
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
MODE=polling python bot.py
```

## 🔧 Troubleshooting

### Bot not responding
- Check if bot token is correct
- Verify bot is admin in the group
- Check console for error messages

### Google Sheets not working
- Verify service account email has access to sheet
- Check sheet name matches exactly
- Ensure all required columns exist

### AI not working
- Check if `GEMINI_API_KEY` is set
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
- 3 tokens per day
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
- [Google Gemini AI](https://ai.google.dev/)

---

Made with ❤️ for Technologia Club
