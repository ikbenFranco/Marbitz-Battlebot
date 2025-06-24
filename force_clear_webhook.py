"""
Force clear webhook using direct HTTP request.
"""

import asyncio
import aiohttp
import sys

async def clear_webhook(bot_token):
    """Clear webhook using direct API call."""
    url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    
    async with aiohttp.ClientSession() as session:
        # Clear webhook and drop pending updates
        async with session.post(url, json={"drop_pending_updates": True}) as response:
            result = await response.json()
            print(f"Clear webhook result: {result}")
        
        # Get webhook info to verify
        info_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        async with session.get(info_url) as response:
            info = await response.json()
            print(f"Webhook info: {info}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python force_clear_webhook.py <BOT_TOKEN>")
        sys.exit(1)
    
    bot_token = sys.argv[1]
    asyncio.run(clear_webhook(bot_token))