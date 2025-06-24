"""
Storage module for Marbitz Battlebot.

This module handles data persistence for leaderboards and other data.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Enable logging
logger = logging.getLogger(__name__)

# File paths
OVERALL_LEADERBOARD_FILE = 'overall_leaderboard.json'
WEEKLY_LEADERBOARD_FILE = 'weekly_leaderboard.json'
WEEKLY_RESET_FILE = 'weekly_reset.json'
CHALLENGES_FILE = 'challenges.json'

def load_json_file(filename: str) -> Dict[str, Any]:
    """Load data from JSON file.
    
    Args:
        filename: Path to the JSON file
        
    Returns:
        Dictionary containing the loaded data or empty dict if file not found
    """
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info(f"File {filename} not found. Returning empty dictionary.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {filename}. Returning empty dictionary.")
        return {}

def save_json_file(data: Dict[str, Any], filename: str) -> None:
    """Save data to JSON file.
    
    Args:
        data: Dictionary to save
        filename: Path to the JSON file
    """
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving data to {filename}: {e}")
        raise

def load_leaderboard(filename: str = OVERALL_LEADERBOARD_FILE) -> Dict[str, Dict[str, int]]:
    """Load leaderboard from JSON file.
    
    Args:
        filename: Path to the leaderboard file
        
    Returns:
        Dictionary containing the leaderboard data
    """
    return load_json_file(filename)

def save_leaderboard(leaderboard: Dict[str, Dict[str, int]], 
                    filename: str = OVERALL_LEADERBOARD_FILE) -> None:
    """Save leaderboard to JSON file.
    
    Args:
        leaderboard: Dictionary containing the leaderboard data
        filename: Path to the leaderboard file
    """
    save_json_file(leaderboard, filename)

def get_weekly_reset_info() -> Dict[str, Any]:
    """Get information about the weekly reset.
    
    Returns:
        Dictionary containing reset information
    """
    try:
        reset_info = load_json_file(WEEKLY_RESET_FILE)
        if not reset_info:
            # Default to Monday reset if no info exists
            reset_info = {'reset_day': 'Monday', 'last_reset': None}
        return reset_info
    except Exception as e:
        logger.error(f"Error getting weekly reset info: {e}")
        return {'reset_day': 'Monday', 'last_reset': None}

def save_weekly_reset_info(reset_info: Dict[str, Any]) -> None:
    """Save weekly reset information.
    
    Args:
        reset_info: Dictionary containing reset information
    """
    save_json_file(reset_info, WEEKLY_RESET_FILE)

# These functions are now handled by the ChallengeManager class in state.py