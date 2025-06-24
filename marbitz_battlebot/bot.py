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
    status_command, cancel_challenge_callback, cancel_conversation, 
    WAGER_AMOUNT, CHALLENGE_CONFIRMATION
)
from marbitz_battlebot.battle import initialize_battle_system, cleanup_expired_challenges

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def cleanup_task(context: ContextTypes.DEFAULT_TYPE, interval_hours: int = 1, expiry_hours: int = 6) -> None:
    """Periodic task to clean up expired challenges and notify users about expiring challenges.
    
    Args:
        context: Bot context for sending notifications
        interval_hours: Interval in hours between cleanup runs
        expiry_hours: Number of hours after which a challenge expires
    """
    while True:
        try:
            logger.info(f"Running scheduled cleanup of expired challenges (expiry: {expiry_hours} hours)")
            
            # Get all challenges before cleanup to check for expiring ones
            from marbitz_battlebot.battle import get_all_challenges
            all_challenges = get_all_challenges()
            
            # Clean up expired challenges
            expired_ids = cleanup_expired_challenges(expiry_hours)
            
            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} expired challenges")
                
                # Log details of expired challenges
                for challenge_id in expired_ids:
                    if challenge_id in all_challenges:
                        challenge_data = all_challenges[challenge_id]
                        challenger = challenge_data.get('challenger_user', 'Unknown')
                        challenged = challenge_data.get('challenged_user', 'Unknown')
                        logger.info(f"Expired challenge {challenge_id}: {challenger} vs {challenged}")
            
            # Check for challenges that will expire soon and notify users
            from datetime import datetime, timedelta
            now = datetime.now()
            warning_threshold = timedelta(hours=expiry_hours - 1)  # Notify when 1 hour left
            
            for challenge_id, challenge_data in all_challenges.items():
                if challenge_id not in expired_ids:  # Skip already expired challenges
                    try:
                        # Check if the challenge has a timestamp
                        if 'timestamp' in challenge_data:
                            # Parse the timestamp
                            challenge_time = datetime.fromisoformat(challenge_data['timestamp'])
                            time_elapsed = now - challenge_time
                            time_remaining = timedelta(hours=expiry_hours) - time_elapsed
                            
                            # If challenge will expire within the warning threshold and hasn't been warned yet
                            if (time_remaining < warning_threshold and 
                                time_remaining > timedelta(minutes=5) and  # At least 5 minutes left
                                not challenge_data.get('expiry_warning_sent', False)):
                                
                                # Get user IDs for notification
                                challenger_id = challenge_data.get('challenger_id')
                                if challenger_id:
                                    try:
                                        # Format time remaining in a user-friendly way
                                        hours, remainder = divmod(int(time_remaining.total_seconds()), 3600)
                                        minutes = remainder // 60
                                        time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                                        
                                        # Send notification to challenger
                                        await context.bot.send_message(
                                            chat_id=challenger_id,
                                            text=f"⚠️ Your challenge to @{challenge_data.get('challenged_user', 'Unknown')} "
                                                 f"will expire in {time_str}! Use /status to check your challenge status."
                                        )
                                        
                                        # Mark as warned
                                        from marbitz_battlebot.battle import update_challenge
                                        update_challenge(challenge_id, {'expiry_warning_sent': True})
                                        
                                        logger.info(f"Sent expiry warning for challenge {challenge_id}")
                                    except Exception as e:
                                        logger.error(f"Error sending expiry notification: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error processing challenge {challenge_id} during expiry check: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error in cleanup task: {str(e)}")
        
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
            per_chat=True
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
        self.application.add_handler(CommandHandler('status', status_command))
        
        # Add callback handlers for buttons outside of conversation
        self.application.add_handler(CallbackQueryHandler(cancel_challenge_callback, pattern=r'^cancel_'))
    
    async def start(self) -> None:
        """Start the bot application."""
        if not self.application:
            logger.error("Application not set up. Call setup() first.")
            return
        
        # Create a job queue for periodic tasks
        job_queue = self.application.job_queue
        
        # Add the cleanup task to run every hour
        job_queue.run_repeating(
            callback=lambda context: asyncio.create_task(cleanup_task(context, interval_hours=1, expiry_hours=6)),
            interval=3600,  # 1 hour in seconds
            first=10  # Start after 10 seconds
        )
        
        # Start the bot
        logger.info("Bot is starting up and will begin polling...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Run the bot until Ctrl+C is pressed
        await self.application.updater.stop()
        await self.application.stop()

async def main() -> None:
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
    await bot.start()

def run_main():
    """Run the main function with asyncio."""
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
        raise

if __name__ == '__main__':
    run_main()