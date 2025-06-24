"""
Simple bot for testing without conversation handlers.
"""

import os
import logging
import asyncio
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from simple_handlers import simple_challenge_command, simple_challenge_response
from marbitz_battlebot.handlers import start_command, help_command
from marbitz_battlebot.battle import initialize_battle_system

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Run the simple bot."""
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.critical("BOT_TOKEN environment variable not found!")
        return
    
    # Initialize battle system
    initialize_battle_system()
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('challenge', simple_challenge_command))
    
    # Add callback handlers
    application.add_handler(CallbackQueryHandler(simple_challenge_response, pattern=r'^(accept|decline)_'))
    
    logger.info("Starting simple bot...")
    
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
        logger.info("Simple bot is running. Press Ctrl+C to stop.")
        await application.updater.idle()
        
    except Exception as e:
        logger.error(f"Error running simple bot: {str(e)}")
        raise
    finally:
        logger.info("Shutting down simple bot...")
        try:
            if application.updater.running:
                await application.updater.stop()
            if application.running:
                await application.stop()
            await application.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
        raise