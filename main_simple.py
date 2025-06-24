"""
Simplified main entry point for testing.
"""

import os
import logging
import asyncio
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import handlers
from marbitz_battlebot.handlers import start_command, help_command
from simple_handlers import simple_challenge_command, simple_challenge_response
from marbitz_battlebot.battle import initialize_battle_system

async def main():
    """Run the bot."""
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.critical("BOT_TOKEN environment variable not found!")
        return
    
    logger.info("Starting Marbitz Battlebot (Simple Version)...")
    
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
    
    # Add debug handler for all callbacks
    async def debug_all_callbacks(update: Update, context):
        query = update.callback_query
        if query:
            logger.info(f"DEBUG: Unhandled callback - Data: '{query.data}', User: {query.from_user.username if query.from_user else 'Unknown'}")
            await query.answer("Button clicked!")
    
    application.add_handler(CallbackQueryHandler(debug_all_callbacks))
    
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
        logger.info("Bot is running. Press Ctrl+C to stop.")
        await application.updater.idle()
        
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}")
        raise
    finally:
        logger.info("Shutting down bot...")
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