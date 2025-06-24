"""
Webhook-based bot for Render deployment.
"""

import os
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

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

class WebhookBot:
    def __init__(self, token: str, webhook_url: str, port: int = 8080):
        self.token = token
        self.webhook_url = webhook_url
        self.port = port
        self.application = None
        
    async def setup(self):
        """Set up the bot application."""
        # Initialize battle system
        initialize_battle_system()
        
        # Create application
        self.application = Application.builder().token(self.token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler('start', start_command))
        self.application.add_handler(CommandHandler('help', help_command))
        self.application.add_handler(CommandHandler('challenge', simple_challenge_command))
        
        # Add callback handlers
        self.application.add_handler(CallbackQueryHandler(simple_challenge_response, pattern=r'^(accept|decline)_'))
        
        # Initialize the application
        await self.application.initialize()
        await self.application.start()
        
        # Set webhook
        await self.application.bot.set_webhook(
            url=f"{self.webhook_url}/webhook",
            drop_pending_updates=True
        )
        
        logger.info(f"Webhook set to: {self.webhook_url}/webhook")
    
    async def webhook_handler(self, request: Request) -> Response:
        """Handle incoming webhook requests."""
        try:
            # Get the update from the request
            update_data = await request.json()
            update = Update.de_json(update_data, self.application.bot)
            
            if update:
                # Process the update
                await self.application.process_update(update)
            
            return Response(text="OK")
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return Response(text="Error", status=500)
    
    async def health_check(self, request: Request) -> Response:
        """Health check endpoint."""
        return web.json_response({
            'status': 'healthy',
            'service': 'marbitz-battlebot-webhook'
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
        
        logger.info(f"Webhook server started on port {self.port}")
        return runner, site

async def main():
    """Run the webhook bot."""
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.critical("BOT_TOKEN environment variable not found!")
        return
    
    # Get webhook URL from environment or construct it
    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        # Try to construct from Render service URL
        render_service_url = os.getenv('RENDER_EXTERNAL_URL')
        if render_service_url:
            webhook_url = render_service_url.rstrip('/')
        else:
            logger.critical("WEBHOOK_URL or RENDER_EXTERNAL_URL environment variable not found!")
            return
    
    port = int(os.getenv('PORT', 8080))
    
    bot = WebhookBot(bot_token, webhook_url, port)
    
    try:
        await bot.setup()
        runner, site = await bot.start_server()
        
        logger.info("Webhook bot is running...")
        
        # Keep the server running
        try:
            import asyncio
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            await site.stop()
            await runner.cleanup()
            if bot.application:
                await bot.application.stop()
                await bot.application.shutdown()
                
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
        raise

if __name__ == '__main__':
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
        raise