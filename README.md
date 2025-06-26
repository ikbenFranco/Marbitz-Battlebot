# Marbitz Battlebot

A production-ready Telegram bot for fun marble battles in your group chat!

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ikbenFranco/Marbitz-Battlebot)

## Features

- 🎯 **Challenge System**: Challenge other users with `/challenge @username`
- 💰 **Wagering**: Bet points on battle outcomes
- 📖 **Dynamic Battles**: Exciting, randomly generated battle storylines
- 🏆 **Leaderboards**: Overall and weekly rankings
- 🔒 **Thread-Safe**: Robust state management with race condition protection
- ⏰ **Auto-Cleanup**: Automatic challenge expiration and cleanup
- 🚀 **Production Ready**: Optimized for deployment with proper logging and error handling

## State Management

The bot uses a robust state management system with the following features:

* **Thread-safe operations**: All state modifications are protected by locks to prevent race conditions
* **Singleton pattern**: Ensures only one instance of the state manager exists
* **Persistent storage**: State is automatically saved to disk to survive bot restarts
* **Automatic cleanup**: Expired challenges are automatically removed to prevent memory leaks
* **Error handling**: Comprehensive error handling to ensure the bot remains stable

## Security

The bot implements several security best practices:

* **Environment Variables**: Sensitive information like API tokens are stored in environment variables, not in code
* **Token Protection**: Bot tokens are never committed to version control
* **Secure Configuration**: The Render.yaml file uses null values for sensitive data, which must be set in the Render dashboard
* **Input Validation**: User inputs are validated to prevent injection attacks
* **Error Handling**: Errors are logged without exposing sensitive information
* **Access Control**: Challenge responses are verified to ensure only the challenged user can respond

## Project Structure

```
marbitz-battlebot/
├── main.py                    # Production entry point (webhook mode)
├── requirements.txt           # All dependencies
├── requirements-prod.txt      # Production-only dependencies
├── Render.yaml               # Render deployment configuration
├── marbitz_battlebot/        # Main package
│   ├── handlers.py           # Telegram command handlers
│   ├── battle.py             # Battle mechanics and logic
│   ├── state.py              # Thread-safe state management
│   ├── leaderboard.py        # Rankings and statistics
│   └── storage.py            # Data persistence
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
└── clear_webhook.py          # Utility for webhook debugging
```

## Quick Start

### For Users
1. Add `@MarbitzBattleBot` to your Telegram group
2. Use `/start` to see the welcome message
3. Use `/help` to see available commands
4. Challenge someone with `/challenge @username`!

### For Developers

#### Local Development
```bash
# Clone and setup
git clone https://github.com/ikbenFranco/Marbitz-Battlebot.git
cd Marbitz-Battlebot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your BOT_TOKEN

# Run the bot
python main.py
```

#### Production Deployment (Render)
1. Fork this repository
2. Create a new Web Service on [Render](https://render.com)
3. Connect your forked repository
4. Set environment variables:
   - `BOT_TOKEN`: Your Telegram bot token from @BotFather
5. Deploy with:
   - **Build Command**: `pip install -r requirements-prod.txt`
   - **Start Command**: `python main.py`

## Commands

- `/start` - Welcome message and bot introduction
- `/help` - Show available commands
- `/challenge @username` - Challenge another user to battle
- `/cancel_challenge` - Cancel your pending challenge
- `/leaderboard` - Show overall rankings
- `/weekly` - Show weekly rankings
- `/stats` - Show global statistics
- `/my_stats` - Show your personal statistics
- `/status` - Show bot status and active challenges

## Testing

Run the comprehensive test suite:

```bash
# Run all tests with coverage
pytest --cov=marbitz_battlebot

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only

# Windows batch file
run_tests.bat
```

For detailed testing information, see [TESTING.md](TESTING.md).

## Bot Setup (Telegram)

1. Talk to [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot: `/newbot`
3. Choose a name and username for your bot
4. Copy the API token provided
5. **For group usage**: Disable group privacy:
   - Use `/mybots` with @BotFather
   - Select your bot → Bot Settings → Group Privacy → Turn off

## Environment Variables

- `BOT_TOKEN` - Your Telegram bot token (required)
- `WEBHOOK_URL` - Webhook URL for production (auto-detected on Render)
- `PORT` - Server port (default: 8080)
- `LOG_TO_FILE` - Enable file logging (optional)
