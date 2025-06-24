"""
WEBHOOK-ONLY main entry point for Render deployment.
This version NEVER uses polling and ONLY uses webhooks.
"""

import os
import logging
import asyncio

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import handlers
from marbitz_battlebot.handlers import (
    start_command, help_command, challenge_command, 
    challenge_response_callback, cancel_challenge_command,
    leaderboard_command, weekly_command, stats_command, my_stats_command,
    status_command, cancel_challenge_callback, debug_command
)
from marbitz_battlebot.battle import initialize_battle_system

async def clear_webhook_first(bot_token: str):
    """Clear any existing webhook before setting up."""
    try:
        bot = Bot(token=bot_token)
        
        # Get current webhook info
        webhook_info = await bot.get_webhook_info()
        logger.info(f"🔍 Current webhook: {webhook_info.url}")
        logger.info(f"🔍 Pending updates: {webhook_info.pending_update_count}")
        
        # Clear webhook
        result = await bot.delete_webhook(drop_pending_updates=True)
        logger.info(f"🧹 Webhook cleared: {result}")
        
        await bot.close()
        
    except Exception as e:
        logger.error(f"❌ Error clearing webhook: {str(e)}")

async def setup_webhook_bot(bot_token: str, webhook_url: str):
    """Set up bot with webhook ONLY - NO POLLING."""
    
    # Clear any existing webhook first
    await clear_webhook_first(bot_token)
    
    # Initialize battle system
    initialize_battle_system()
    
    # Create application WITHOUT updater (no polling)
    application = Application.builder().token(bot_token).updater(None).build()
    
    # Add command handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('challenge', challenge_command))
    application.add_handler(CommandHandler('cancel_challenge', cancel_challenge_command))
    application.add_handler(CommandHandler('leaderboard', leaderboard_command))
    application.add_handler(CommandHandler('weekly', weekly_command))
    application.add_handler(CommandHandler('stats', stats_command))
    application.add_handler(CommandHandler('my_stats', my_stats_command))
    application.add_handler(CommandHandler('status', status_command))
    application.add_handler(CommandHandler('debug', debug_command))
    
    # Add callback handlers
    application.add_handler(CallbackQueryHandler(challenge_response_callback, pattern=r'^(accept|decline)_'))
    application.add_handler(CallbackQueryHandler(cancel_challenge_callback, pattern=r'^cancel_'))
    
    # Add debug handler for unhandled callbacks
    async def debug_callback_handler(update: Update, context):
        query = update.callback_query
        if query:
            logger.info(f"🐛 DEBUG: Unhandled callback - Data: '{query.data}', User: {query.from_user.username if query.from_user else 'Unknown'}")
            await query.answer("Button received!")
    
    application.add_handler(CallbackQueryHandler(debug_callback_handler))
    
    # Initialize the application (but DON'T start updater)
    await application.initialize()
    await application.start()
    
    # Set webhook
    webhook_endpoint = f"{webhook_url}/webhook"
    await application.bot.set_webhook(
        url=webhook_endpoint,
        drop_pending_updates=True
    )
    
    logger.info(f"✅ Webhook set to: {webhook_endpoint}")
    
    return application

async def webhook_handler(request: Request, application: Application) -> Response:
    """Handle incoming webhook requests."""
    try:
        # Get the update from the request
        update_data = await request.json()
        logger.info(f"📨 Received webhook update: {update_data.get('update_id', 'unknown')}")
        
        update = Update.de_json(update_data, application.bot)
        
        if update:
            # Process the update
            await application.process_update(update)
            logger.info(f"✅ Processed update: {update.update_id}")
        
        return Response(text="OK")
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(text="Error", status=500)

async def health_check(request: Request) -> Response:
    """Health check endpoint."""
    return web.json_response({
        'status': 'healthy',
        'service': 'marbitz-battlebot-webhook-only',
        'mode': 'webhook-only',
        'polling': 'DISABLED'
    })

async def main():
    """Run the webhook-only bot."""
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.critical("❌ BOT_TOKEN environment variable not found!")
        return
    
    # Get webhook URL from environment
    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        # Try to construct from Render service URL
        render_service_url = os.getenv('RENDER_EXTERNAL_URL')
        if render_service_url:
            webhook_url = render_service_url.rstrip('/')
        else:
            # Fallback - construct from service name
            webhook_url = "https://marbitz-battlebot.onrender.com"
    
    port = int(os.getenv('PORT', 8080))
    
    logger.info(f"🤖 Starting WEBHOOK-ONLY bot with URL: {webhook_url}")
    logger.info(f"🚫 POLLING IS COMPLETELY DISABLED")
    
    try:
        # Set up bot with webhook
        application = await setup_webhook_bot(bot_token, webhook_url)
        
        # Create web application
        app = web.Application()
        
        # Add webhook handler with application closure
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
        
        logger.info(f"🚀 Webhook-only server started on port {port}")
        logger.info("✅ Bot is running and ready to receive webhook updates!")
        logger.info("🚫 NO POLLING - WEBHOOK ONLY!")
        
        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down...")
        finally:
            logger.info("🧹 Cleaning up...")
            await site.stop()
            await runner.cleanup()
            if application:
                await application.stop()
                await application.shutdown()
                
    except Exception as e:
        logger.critical(f"💥 Critical error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
        raise