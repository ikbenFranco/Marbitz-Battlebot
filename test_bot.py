#!/usr/bin/env python3
"""
Test script to verify bot functionality locally.
"""

import os
import logging
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_bot():
    """Test bot initialization."""
    try:
        from marbitz_battlebot.bot import BotApplication
        
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            logger.error("BOT_TOKEN not found in environment variables")
            return False
        
        logger.info("Creating bot application...")
        bot = BotApplication(bot_token)
        
        logger.info("Setting up bot...")
        bot.setup()
        
        logger.info("Bot setup completed successfully!")
        logger.info("Bot is ready to start (not starting polling in test mode)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing bot: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_bot())
    if success:
        print("✅ Bot test passed!")
    else:
        print("❌ Bot test failed!")