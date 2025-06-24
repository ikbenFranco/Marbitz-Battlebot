"""
Webhook-based main entry point for Render deployment.
This solves the conflict issues by using webhooks instead of polling.
"""

import os
import logging
import asyncio

from telegram import Update
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
    status_command, cancel_challenge_callback
)
from marbitz_battlebot.battle import initialize_battle_system

class WebhookBot:
    def __init__(self, token: str, webhook_url: str, port: int = 8080):
        self.token = token
        self.webhook_url = webhook_url
        self.port = port
        self.application = None
        
    async def setup(self):
        """Set up the bot application."""
        logger.info("Setting up webhook bot...")
        
        # Initialize battle system
        initialize_battle_system()
        
        # Create application
        self.application = Application.builder().token(self.token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler('start', start_command))
        self.application.add_handler(CommandHandler('help', help_command))
        self.application.add_handler(CommandHandler('challenge', challenge_command))
        self.application.add_handler(CommandHandler('cancel_challenge', cancel_challenge_command))
        self.application.add_handler(CommandHandler('leaderboard', leaderboard_command))
        self.application.add_handler(CommandHandler('weekly', weekly_command))
        self.application.add_handler(CommandHandler('stats', stats_command))
        self.application.add_handler(CommandHandler('my_stats', my_stats_command))
        self.application.add_handler(CommandHandler('status', status_command))
        
        # Add callback handlers
        self.application.add_handler(CallbackQueryHandler(challenge_response_callback, pattern=r'^(accept|decline)_'))
        self.application.add_handler(CallbackQueryHandler(cancel_challenge_callback, pattern=r'^cancel_'))
        
        # Add debug handler for unhandled callbacks
        async def debug_callback_handler(update: Update, context):
            query = update.callback_query
            if query:
                logger.info(f"DEBUG: Unhandled callback - Data: '{query.data}', User: {query.from_user.username if query.from_user else 'Unknown'}")
                await query.answer("Button received!")
        
        self.application.add_handler(CallbackQueryHandler(debug_callback_handler))
        
        # Initialize the application
        await self.application.initialize()
        await self.application.start()
        
        # Set webhook
        webhook_endpoint = f"{self.webhook_url}/webhook"
        await self.application.bot.set_webhook(
            url=webhook_endpoint,
            drop_pending_updates=True
        )
        
        logger.info(f"✅ Webhook set to: {webhook_endpoint}")
    
    async def webhook_handler(self, request: Request) -> Response:
        """Handle incoming webhook requests."""
        try:
            # Get the update from the request
            update_data = await request.json()
            logger.info(f"📨 Received webhook update: {update_data.get('update_id', 'unknown')}")
            
            update = Update.de_json(update_data, self.application.bot)
            
            if update:
                # Process the update
                await self.application.process_update(update)
                logger.info(f"✅ Processed update: {update.update_id}")
            
            return Response(text="OK")
        except Exception as e:
            logger.error(f"❌ Error processing webhook: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(text="Error", status=500)
    
    async def health_check(self, request: Request) -> Response:
        """Health check endpoint."""
        return web.json_response({
            'status': 'healthy',
            'service': 'marbitz-battlebot-webhook',
            'webhook_url': self.webhook_url,
            'mode': 'webhook'
        })
    
    async def start_server(self):
        """Start the webhook server."""
        app = web.Application()
        app.router.add_post('/webhook', self.webhook_handler)
        app.router.add_get('/', self.health_check)
        app.router.add_get('/health', self.health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"🚀 Webhook server started on port {self.port}")
        return runner, site

async def main():
    """Run the webhook bot."""
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
    
    logger.info(f"🤖 Starting webhook bot with URL: {webhook_url}")
    
    bot = WebhookBot(bot_token, webhook_url, port)
    
    try:
        await bot.setup()
        runner, site = await bot.start_server()
        
        logger.info("✅ Webhook bot is running and ready to receive updates!")
        
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
            if bot.application:
                await bot.application.stop()
                await bot.application.shutdown()
                
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