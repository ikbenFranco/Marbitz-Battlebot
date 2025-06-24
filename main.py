"""
Main entry point for Marbitz Battlebot.

This script imports and runs the bot from the marbitz_battlebot package.
"""

import os
import logging
from dotenv import load_dotenv

from marbitz_battlebot.bot import run_main

# Load environment variables from .env file if it exists
load_dotenv()

# Set up logging for production
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Start health server for Render deployment
try:
    from health_server import start_health_server_thread
    start_health_server_thread()
    logging.info("Health server started")
except ImportError:
    logging.warning("Health server not available")
except Exception as e:
    logging.error(f"Failed to start health server: {e}")

if __name__ == '__main__':
    run_main()