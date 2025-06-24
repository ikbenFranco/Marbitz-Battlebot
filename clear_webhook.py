"""
Script to clear existing webhooks and reset the bot.
Run this if you need to switch between polling and webhook modes.
"""

import os
import asyncio
import logging
from telegram import Bot

# No need to load dotenv for this script

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clear_webhook():
    """Clear the webhook and get bot info."""
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    bot = Bot(token=bot_token)
    
    try:
        # Get bot info
        me = await bot.get_me()
        logger.info(f"Bot info: @{me.username} ({me.first_name})")
        
        # Get current webhook info
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Current webhook URL: {webhook_info.url}")
        logger.info(f"Pending updates: {webhook_info.pending_update_count}")
        
        # Clear webhook
        result = await bot.delete_webhook(drop_pending_updates=True)
        if result:
            logger.info("✅ Webhook cleared successfully!")
        else:
            logger.error("❌ Failed to clear webhook")
        
        # Verify webhook is cleared
        webhook_info = await bot.get_webhook_info()
        logger.info(f"New webhook URL: {webhook_info.url}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        # Close the bot session
        await bot.close()

if __name__ == '__main__':
    asyncio.run(clear_webhook())