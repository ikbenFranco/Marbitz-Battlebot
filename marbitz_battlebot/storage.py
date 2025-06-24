"""
Storage module for Marbitz Battlebot.

This module handles data persistence for leaderboards and other data.
"""

import json
import logging
import os
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
    
    Raises:
        ValueError: If filename is empty or None
    """
    if not filename:
        logger.error("Empty filename provided to load_json_file")
        raise ValueError("Filename cannot be empty")
        
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                logger.warning(f"File {filename} did not contain a dictionary. Converting to empty dict.")
                return {}
            return data
    except FileNotFoundError:
        logger.info(f"File {filename} not found. Returning empty dictionary.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {filename}: {str(e)}. Returning empty dictionary.")
        return {}
    except PermissionError:
        logger.error(f"Permission denied when trying to read {filename}. Returning empty dictionary.")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading {filename}: {str(e)}. Returning empty dictionary.")
        return {}

def save_json_file(data: Dict[str, Any], filename: str) -> bool:
    """Save data to JSON file.
    
    Args:
        data: Dictionary to save
        filename: Path to the JSON file
        
    Returns:
        True if save was successful, False otherwise
        
    Raises:
        ValueError: If filename is empty or None or data is not a dictionary
    """
    if not filename:
        logger.error("Empty filename provided to save_json_file")
        raise ValueError("Filename cannot be empty")
        
    if not isinstance(data, dict):
        logger.error(f"Non-dictionary data provided to save_json_file: {type(data)}")
        raise ValueError("Data must be a dictionary")
    
    try:
        # Create a backup of the existing file if it exists
        try:
            if os.path.exists(filename):
                backup_filename = f"{filename}.bak"
                with open(filename, 'r') as src, open(backup_filename, 'w') as dst:
                    dst.write(src.read())
                logger.debug(f"Created backup of {filename} at {backup_filename}")
        except Exception as e:
            logger.warning(f"Failed to create backup of {filename}: {str(e)}")
        
        # Write the new data
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.debug(f"Successfully saved data to {filename}")
        return True
    except PermissionError:
        logger.error(f"Permission denied when trying to write to {filename}")
        return False
    except OSError as e:
        logger.error(f"OS error when saving data to {filename}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving data to {filename}: {str(e)}")
        return False

def load_leaderboard(filename: str = OVERALL_LEADERBOARD_FILE) -> Dict[str, Dict[str, int]]:
    """Load leaderboard from JSON file.
    
    Args:
        filename: Path to the leaderboard file
        
    Returns:
        Dictionary containing the leaderboard data
    """
    return load_json_file(filename)

def save_leaderboard(leaderboard: Dict[str, Dict[str, int]], 
                    filename: str = OVERALL_LEADERBOARD_FILE) -> bool:
    """Save leaderboard to JSON file.
    
    Args:
        leaderboard: Dictionary containing the leaderboard data
        filename: Path to the leaderboard file
        
    Returns:
        True if save was successful, False otherwise
    """
    if not isinstance(leaderboard, dict):
        logger.error(f"Invalid leaderboard data type: {type(leaderboard)}")
        return False
        
    # Validate leaderboard structure
    for username, stats in leaderboard.items():
        if not isinstance(stats, dict):
            logger.error(f"Invalid stats type for user {username}: {type(stats)}")
            return False
    
    return save_json_file(leaderboard, filename)

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

def save_weekly_reset_info(reset_info: Dict[str, Any]) -> bool:
    """Save weekly reset information.
    
    Args:
        reset_info: Dictionary containing reset information
        
    Returns:
        True if save was successful, False otherwise
    """
    if not isinstance(reset_info, dict):
        logger.error(f"Invalid reset_info data type: {type(reset_info)}")
        return False
        
    # Validate required fields
    if 'reset_day' not in reset_info:
        logger.error("Missing 'reset_day' in reset_info")
        reset_info['reset_day'] = 'Monday'  # Set default
        
    # Validate reset_day value
    valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    if reset_info.get('reset_day') not in valid_days:
        logger.error(f"Invalid reset_day value: {reset_info.get('reset_day')}")
        reset_info['reset_day'] = 'Monday'  # Set default
    
    return save_json_file(reset_info, WEEKLY_RESET_FILE)

# These functions are now handled by the ChallengeManager class in state.py