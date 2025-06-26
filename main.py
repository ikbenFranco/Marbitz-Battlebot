"""
Production-ready Marbitz Battlebot - Webhook Mode
Telegram bot for battle challenges with leaderboards and statistics.
"""

import os
import logging
import asyncio
import signal
import sys
from typing import Optional

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

# Configure production logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', mode='a') if os.getenv('LOG_TO_FILE') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress noisy logs in production
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

# Import handlers
from marbitz_battlebot.handlers import (
    start_command, help_command, challenge_command, 
    challenge_response_callback, cancel_challenge_command,
    leaderboard_command, weekly_command, stats_command, my_stats_command,
    status_command, cancel_challenge_callback, debug_command
)
from marbitz_battlebot.battle import initialize_battle_system

async def clear_webhook_first(bot_token: str) -> None:
    """Clear any existing webhook before setting up new one."""
    try:
        bot = Bot(token=bot_token)
        
        # Get current webhook info
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            logger.info(f"Clearing existing webhook: {webhook_info.url}")
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook cleared successfully")
        else:
            logger.info("No existing webhook to clear")
        
        await bot.close()
        
    except Exception as e:
        logger.error(f"Error clearing webhook: {str(e)}")
        raise

async def setup_webhook_bot(bot_token: str, webhook_url: str) -> Application:
    """Set up bot with webhook configuration."""
    
    # Clear any existing webhook first
    await clear_webhook_first(bot_token)
    
    # Initialize battle system
    initialize_battle_system()
    logger.info("Battle system initialized")
    
    # Create application without updater (webhook mode)
    application = Application.builder().token(bot_token).updater(None).build()
    
    # Register command handlers
    handlers = [
        CommandHandler('start', start_command),
        CommandHandler('help', help_command),
        CommandHandler('challenge', challenge_command),
        CommandHandler('cancel_challenge', cancel_challenge_command),
        CommandHandler('leaderboard', leaderboard_command),
        CommandHandler('weekly', weekly_command),
        CommandHandler('stats', stats_command),
        CommandHandler('my_stats', my_stats_command),
        CommandHandler('status', status_command),
        CommandHandler('debug', debug_command),
        
        # Callback handlers
        CallbackQueryHandler(challenge_response_callback, pattern=r'^(accept|decline)_'),
        CallbackQueryHandler(cancel_challenge_callback, pattern=r'^cancel_'),
    ]
    
    for handler in handlers:
        application.add_handler(handler)
    
    # Add fallback handler for unhandled callbacks
    async def fallback_callback_handler(update: Update, context):
        query = update.callback_query
        if query:
            logger.warning(f"Unhandled callback: {query.data} from user {query.from_user.username if query.from_user else 'Unknown'}")
            await query.answer("This button is no longer active.")
    
    application.add_handler(CallbackQueryHandler(fallback_callback_handler))
    
    # Initialize and start application
    await application.initialize()
    await application.start()
    
    # Set webhook
    webhook_endpoint = f"{webhook_url}/webhook"
    await application.bot.set_webhook(
        url=webhook_endpoint,
        drop_pending_updates=True,
        max_connections=100,
        allowed_updates=['message', 'callback_query']
    )
    
    logger.info(f"Webhook configured: {webhook_endpoint}")
    
    return application

async def webhook_handler(request: Request, application: Application) -> Response:
    """Handle incoming webhook requests from Telegram."""
    try:
        # Parse update data
        update_data = await request.json()
        update_id = update_data.get('update_id', 'unknown')
        
        # Create Update object
        update = Update.de_json(update_data, application.bot)
        
        if update:
            # Process the update
            await application.process_update(update)
            logger.debug(f"Processed update {update_id}")
        else:
            logger.warning(f"Failed to parse update {update_id}")
        
        return Response(text="OK")
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return Response(text="Error", status=500)

async def health_check(request: Request) -> Response:
    """Health check endpoint for monitoring."""
    return web.json_response({
        'status': 'healthy',
        'service': 'marbitz-battlebot',
        'mode': 'webhook',
        'version': '1.0.0'
    })

async def get_webhook_url() -> str:
    """Get webhook URL from environment variables."""
    webhook_url = os.getenv('WEBHOOK_URL')
    if webhook_url:
        return webhook_url.rstrip('/')
    
    # Try Render service URL
    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url:
        return render_url.rstrip('/')
    
    # Fallback for Render deployment
    return "https://marbitz-battlebot.onrender.com"

async def shutdown_handler(application: Optional[Application], runner: Optional[web.AppRunner], site: Optional[web.TCPSite]):
    """Clean shutdown handler."""
    logger.info("Shutting down gracefully...")
    
    if site:
        await site.stop()
    if runner:
        await runner.cleanup()
    if application:
        await application.stop()
        await application.shutdown()
    
    logger.info("Shutdown complete")

async def main():
    """Main entry point for the bot."""
    # Validate environment
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.critical("BOT_TOKEN environment variable is required")
        sys.exit(1)
    
    webhook_url = await get_webhook_url()
    port = int(os.getenv('PORT', 8080))
    
    logger.info(f"Starting Marbitz Battlebot")
    logger.info(f"Webhook URL: {webhook_url}")
    logger.info(f"Port: {port}")
    
    application = None
    runner = None
    site = None
    
    try:
        # Set up bot
        application = await setup_webhook_bot(bot_token, webhook_url)
        
        # Create web server
        app = web.Application()
        
        # Route handlers
        async def webhook_route(request):
            return await webhook_handler(request, application)
        
        app.router.add_post('/webhook', webhook_route)
        app.router.add_get('/', health_check)
        app.router.add_get('/health', health_check)
        
        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"Bot server started on port {port}")
        logger.info("Bot is ready to receive updates")
        
        # Set up signal handlers for graceful shutdown
        def signal_handler():
            logger.info("Received shutdown signal")
            raise KeyboardInterrupt()
        
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, lambda s, f: signal_handler())
        
        # Keep server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
            
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
        raise
    finally:
        await shutdown_handler(application, runner, site)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        sys.exit(1)