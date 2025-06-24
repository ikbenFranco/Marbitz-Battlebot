"""
Emergency webhook clear script.
Run this if you're still getting polling conflicts.
"""

import asyncio
import aiohttp
import sys

async def emergency_clear(bot_token):
    """Emergency clear using direct HTTP requests."""
    base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async with aiohttp.ClientSession() as session:
        print("🔍 Getting current webhook info...")
        
        # Get webhook info
        async with session.get(f"{base_url}/getWebhookInfo") as response:
            info = await response.json()
            print(f"Current webhook: {info}")
        
        print("🧹 Clearing webhook...")
        
        # Clear webhook with all options
        clear_data = {
            "drop_pending_updates": True
        }
        async with session.post(f"{base_url}/deleteWebhook", json=clear_data) as response:
            result = await response.json()
            print(f"Clear result: {result}")
        
        print("🔍 Verifying webhook cleared...")
        
        # Verify cleared
        async with session.get(f"{base_url}/getWebhookInfo") as response:
            info = await response.json()
            print(f"After clear: {info}")
        
        print("✅ Emergency clear completed!")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python emergency_clear.py <BOT_TOKEN>")
        print("Example: python emergency_clear.py 8047371965:AAGFlIgTDk9lkYQe1-mBdBC6-99KadUP3ZE")
        sys.exit(1)
    
    bot_token = sys.argv[1]
    asyncio.run(emergency_clear(bot_token))