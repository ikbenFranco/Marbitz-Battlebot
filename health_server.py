"""
Simple health check server for Render deployment.
This runs alongside the bot to provide health check endpoints.
"""

import asyncio
import logging
from aiohttp import web
import threading

logger = logging.getLogger(__name__)

class HealthServer:
    def __init__(self, port=8080):
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        
    def setup_routes(self):
        """Set up health check routes."""
        self.app.router.add_get('/', self.health_check)
        self.app.router.add_get('/health', self.health_check)
        
    async def health_check(self, request):
        """Health check endpoint."""
        return web.json_response({
            'status': 'healthy',
            'service': 'marbitz-battlebot'
        })
    
    async def start(self):
        """Start the health server."""
        self.setup_routes()
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
        await self.site.start()
        logger.info(f"Health server started on port {self.port}")
    
    async def stop(self):
        """Stop the health server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Health server stopped")

def start_health_server_thread():
    """Start health server in a separate thread."""
    async def run_server():
        server = HealthServer()
        await server.start()
        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            await server.stop()
    
    def thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_server())
        except Exception as e:
            logger.error(f"Health server error: {e}")
        finally:
            loop.close()
    
    thread = threading.Thread(target=thread_target, daemon=True)
    thread.start()
    return thread