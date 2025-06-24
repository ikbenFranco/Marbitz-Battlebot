"""
Main entry point for Marbitz Battlebot.

This script imports and runs the bot from the marbitz_battlebot package.
"""

import os
import logging
from dotenv import load_dotenv

from marbitz_battlebot.bot import main

# Load environment variables from .env file if it exists
load_dotenv()

if __name__ == '__main__':
    main()