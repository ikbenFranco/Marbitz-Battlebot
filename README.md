# Marbitz Battlebot

A Telegram bot for fun marble battles in your group chat!

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ikbenFranco/Marbitz-Battlebot)
## Features

*   Challenge other users with `/challenge @username`
*   Wager on battles
*   Exciting, randomly generated battle storylines
*   Overall and Weekly Leaderboards
*   Thread-safe state management
*   Automatic challenge expiration

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

The project is organized into the following modules:

* `main.py` - Entry point for the application
* `run_tests.py` - Script to run tests with coverage reporting
* `pytest.ini` - Pytest configuration
* `marbitz_battlebot/` - Main package
  * `__init__.py` - Package initialization
  * `bot.py` - Bot initialization and main application logic
  * `handlers.py` - Command handlers for Telegram commands
  * `battle.py` - Battle mechanics
  * `state.py` - State management with thread-safe challenge tracking
  * `leaderboard.py` - Leaderboard functionality and user stats
  * `storage.py` - Data persistence functions
* `tests/` - Test suite
  * `conftest.py` - Test fixtures and configuration
  * `unit/` - Unit tests
    * `test_storage.py` - Tests for storage module
    * `test_state.py` - Tests for state management
    * `test_leaderboard.py` - Tests for leaderboard functionality
    * `test_battle.py` - Tests for battle mechanics
  * `integration/` - Integration tests
    * `test_handlers.py` - Tests for command handlers

## Testing

The project includes a comprehensive test suite:

* **Unit Tests**: Tests for individual modules and functions
* **Integration Tests**: Tests for interactions between components
* **Test Fixtures**: Reusable test components and mock objects
* **Coverage Reporting**: Test coverage analysis to identify untested code

To run the tests:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=marbitz_battlebot

# Run specific test file
pytest tests/unit/test_storage.py

# Or use the run_tests.py script
python run_tests.py
```

## Getting Started (for users)

1.  Add `@MarbitzBattleBot` to your Telegram group.
2.  Use `/start` to see a welcome message.
3.  Use `/help` to see available commands.
4.  Challenge someone using `/challenge @username`!

## Running the Bot (for developers)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ikbenFranco/Marbitz-Battlebot.git
    cd Marbitz-Battlebot
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set your Bot Token (for Local Development):**
    The bot is configured to load the `BOT_TOKEN` from an environment variable. For local development:
    *   Copy the `.env.example` file to a new file named `.env` (this file is ignored by Git).
        ```bash
        cp .env.example .env
        ```
    *   Open the `.env` file and replace `YOUR_TELEGRAM_BOT_TOKEN_HERE` with your actual Telegram Bot Token.

    The `main.py` script will automatically load this token from the `.env` file using the `python-dotenv` library.

    **Important for Render Deployment:** When deploying to Render (see below), you will **NOT** use a `.env` file. Instead, you will set the `BOT_TOKEN` directly in Render's environment variable settings in their dashboard.

5.  **Run the bot:**
    ```bash
    python main.py
    ```

6.  **Run tests:**
    ```bash
    # Run all tests
    pytest
    
    # Run tests with coverage report
    pytest --cov=marbitz_battlebot
    
    # Run specific test file
    pytest tests/unit/test_storage.py
    
    # Or use the run_tests.py script
    python run_tests.py
    ```
## Deploying to Render

You can easily deploy your own instance of Marbitz Battlebot using Render.

1.  **Fork this Repository:** Click the "Fork" button at the top right of this page to create your own copy of this repository.
2.  **Sign up/Log in to Render:** Go to [render.com](https://render.com) and create an account or log in.
3.  **Create a New Web Service:**
    *   Click on "New +" and then "Web Service".
    *   Connect your GitHub account if you haven't already.
    *   Select your forked `Marbitz-Battlebot` repository.
    *   Give your service a unique name (e.g., `my-marbitz-bot`).
    *   **Region:** Choose a region closest to you or your users.
    *   **Branch:** `main` (or your default branch).
    *   **Root Directory:** Leave blank (it's the root of your repo).
    *   **Runtime:** `Python 3`
    *   **Build Command:** `pip install -r requirements.txt`
    *   **Start Command:** `python main.py`
    *   **Instance Type:** `Free` is likely sufficient to start, but you can choose a paid tier for better performance/uptime.
4.  **Add Environment Variable (Crucial for Render):**
    *   Scroll down to the "Environment" section.
    *   Click "Add Environment Variable".
    *   **Key:** `BOT_TOKEN`
    *   **Value:** Paste your Telegram Bot Token here (the one you get from BotFather).
    *   **Make sure the Key is exactly `BOT_TOKEN` and the Value is your correct Telegram API token.** This is the most common point of failure if the bot doesn't start correctly on Render and gives a token-related error.
    *   You can also add `PYTHON_VERSION` and set it to your desired Python 3 version (e.g., `3.10.4` or whatever Render supports and you prefer).
    
    **Security Note:** Never commit your bot token to version control. Always use environment variables or a `.env` file (which is gitignored) for local development. If you accidentally expose your token, regenerate it immediately using BotFather's `/revoke` command.
5.  **Create Web Service:** Click the "Create Web Service" button. Render will now build and deploy your bot.
6.  **Bot Setup (Telegram):**
    *   If you haven't already, talk to `@BotFather` on Telegram.
    *   Create a new bot: `/newbot`
    *   Follow the instructions to choose a name and username for your bot.
    *   BotFather will give you an **API token**. This is the `BOT_TOKEN` you used in the environment variables on Render.
    *   **Important for Group Usage:**
        *   Disable group privacy for your bot so it can read messages in groups. Talk to `@BotFather`, use `/mybots`, select your bot, go to "Bot Settings" -> "Group Privacy" -> "Turn off".
        *   Ensure your bot has permission to send messages in the group.

Once deployed, your bot should be running and responsive on Telegram!

## How Other Telegram Groups Can Implement This Bot

If you want to run a *public* instance of this bot that other groups can add (like the official `@MarbitzBattleBot` once it's deployed and running publicly by @ikbenFranco):

1.  The group admin simply needs to search for the bot's username (e.g., `@MarbitzBattleBot`) on Telegram.
2.  Add the bot to their group.
3.  The bot should then respond to commands like `/start`, `/help`, and `/challenge`.

If other users want to host *their own private instance* of the bot for their group:

1.  They should follow the "Deploying to Render" (or "Running the Bot (for developers)") instructions above using their *own* Telegram Bot Token.
2.  This will create a separate, independent bot that they control.
