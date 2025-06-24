"""
Main bot module for Marbitz Battlebot.

This module initializes and runs the Telegram bot.
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    ContextTypes, ConversationHandler, CallbackQueryHandler
)

from marbitz_battlebot.handlers import (
    start_command, help_command, challenge_command, wager_callback,
    wager_amount_handler, challenge_response_callback, cancel_challenge_command,
    leaderboard_command, weekly_command, stats_command, my_stats_command,
    cancel_conversation, WAGER_AMOUNT, CHALLENGE_CONFIRMATION
)
from marbitz_battlebot.battle import initialize_battle_system, cleanup_expired_challenges

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def cleanup_task(interval_hours: int = 1) -> None:
    """Periodic task to clean up expired challenges.
    
    Args:
        interval_hours: Interval in hours between cleanup runs
    """
    while True:
        try:
            logger.info("Running scheduled cleanup of expired challenges")
            expired_ids = cleanup_expired_challenges(24)  # Expire after 24 hours
            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} expired challenges")
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
        
        # Sleep for the specified interval
        await asyncio.sleep(interval_hours * 3600)

class BotApplication:
    """
    Main application class for the Marbitz Battlebot.
    
    This class encapsulates the bot application and provides methods
    for starting and stopping the bot.
    """
    
    def __init__(self, token: str):
        """
        Initialize the bot application.
        
        Args:
            token: Telegram bot token
        """
        self.token = token
        self.application = None
    
    def setup(self) -> None:
        """Set up the bot application with handlers."""
        # Initialize battle system
        initialize_battle_system()
        
        # Create application
        self.application = Application.builder().token(self.token).build()
        
        # Challenge conversation handler
        challenge_conv_handler = ConversationHandler(
            entry_points=[CommandHandler('challenge', challenge_command)],
            states={
                WAGER_AMOUNT: [
                    CallbackQueryHandler(wager_callback, pattern=r'^wager_(yes|no)_'),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, wager_amount_handler)
                ],
                CHALLENGE_CONFIRMATION: [
                    CallbackQueryHandler(challenge_response_callback, pattern=r'^(accept|decline)_')
                ]
            },
            fallbacks=[CommandHandler('cancel', cancel_conversation)],
            per_user=True
        )
        
        # Add handlers
        self.application.add_handler(CommandHandler('start', start_command))
        self.application.add_handler(CommandHandler('help', help_command))
        self.application.add_handler(challenge_conv_handler)
        self.application.add_handler(CommandHandler('cancel_challenge', cancel_challenge_command))
        self.application.add_handler(CommandHandler('leaderboard', leaderboard_command))
        self.application.add_handler(CommandHandler('weekly', weekly_command))
        self.application.add_handler(CommandHandler('stats', stats_command))
        self.application.add_handler(CommandHandler('my_stats', my_stats_command))
    
    def start(self) -> None:
        """Start the bot application."""
        if not self.application:
            logger.error("Application not set up. Call setup() first.")
            return
        
        # Start the cleanup task
        asyncio.create_task(cleanup_task())
        
        # Start the bot
        logger.info("Bot is starting up and will begin polling...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main() -> None:
    """Start the bot."""
    # Get bot token from environment variable
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.critical("CRITICAL ERROR: BOT_TOKEN environment variable not found!")
        logger.critical("Please set the BOT_TOKEN environment variable with your Telegram bot token.")
        return
    
    logger.info("Starting Marbitz Battlebot...")
    
    # Create and start the bot application
    bot = BotApplication(bot_token)
    bot.setup()
    bot.start()

if __name__ == '__main__':
    main()