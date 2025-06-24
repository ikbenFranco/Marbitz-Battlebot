"""
Leaderboard module for Marbitz Battlebot.

This module handles leaderboard functionality including updating scores,
formatting leaderboards for display, and managing weekly resets.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Tuple

from marbitz_battlebot.storage import (
    load_leaderboard, save_leaderboard, get_weekly_reset_info, 
    save_weekly_reset_info, OVERALL_LEADERBOARD_FILE, WEEKLY_LEADERBOARD_FILE
)

# Enable logging
logger = logging.getLogger(__name__)

def should_reset_weekly_leaderboard() -> bool:
    """Check if weekly leaderboard should be reset.
    
    Returns:
        True if the leaderboard should be reset, False otherwise
    """
    try:
        # Get reset info with error handling
        try:
            reset_info = get_weekly_reset_info()
            if reset_info is None:
                logger.error("get_weekly_reset_info returned None")
                reset_info = {}
        except Exception as e:
            logger.error(f"Error getting weekly reset info: {str(e)}")
            reset_info = {}  # Use empty dict as fallback
        
        # Validate reset_info structure
        if not isinstance(reset_info, dict):
            logger.error(f"Invalid reset_info type: {type(reset_info)}")
            reset_info = {}
        
        # Get reset day with validation
        reset_day = reset_info.get('reset_day')
        valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        if not reset_day or reset_day not in valid_days:
            logger.warning(f"Invalid reset_day: {reset_day}, defaulting to Monday")
            reset_day = 'Monday'
        
        # Get last reset with validation
        last_reset = reset_info.get('last_reset')
        if last_reset and not isinstance(last_reset, str):
            logger.warning(f"Invalid last_reset type: {type(last_reset)}, treating as None")
            last_reset = None
        
        # Get current time
        now = datetime.now()
        current_weekday = now.strftime('%A')
        
        # If no previous reset, always reset on the reset day
        if last_reset is None and current_weekday == reset_day:
            logger.info(f"No previous reset and today is {reset_day}, should reset")
            return True
        
        # If we have a last reset date
        if last_reset:
            try:
                # Parse the last reset date
                last_reset_date = datetime.fromisoformat(last_reset)
                
                # If it's the reset day and the last reset was not today
                if current_weekday == reset_day and last_reset_date.date() != now.date():
                    # Check if the last reset was at least 6 days ago
                    days_since_reset = (now - last_reset_date).days
                    if days_since_reset >= 6:
                        logger.info(f"Today is {reset_day} and last reset was {days_since_reset} days ago, should reset")
                        return True
                    else:
                        logger.info(f"Today is {reset_day} but last reset was only {days_since_reset} days ago, not resetting yet")
                
                # If it's been more than 7 days since the last reset (failsafe)
                if (now - last_reset_date).days >= 7:
                    logger.info(f"It's been {(now - last_reset_date).days} days since last reset, should reset (failsafe)")
                    return True
                    
            except (ValueError, TypeError) as e:
                logger.error(f"Error parsing last reset date '{last_reset}': {str(e)}")
                # Reset on the reset day if we can't parse the date
                if current_weekday == reset_day:
                    logger.info(f"Could not parse last reset date and today is {reset_day}, should reset")
                    return True
        
        logger.info(f"No reset needed. Today: {current_weekday}, Reset day: {reset_day}, Last reset: {last_reset}")
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error in should_reset_weekly_leaderboard: {str(e)}")
        # Default to not resetting in case of unexpected errors
        return False

def reset_weekly_leaderboard() -> bool:
    """Reset the weekly leaderboard.
    
    Returns:
        True if the leaderboard was reset, False otherwise
    """
    try:
        # Check if reset is needed
        should_reset = False
        try:
            should_reset = should_reset_weekly_leaderboard()
        except Exception as e:
            logger.error(f"Error checking if weekly leaderboard should be reset: {str(e)}")
            # Default to not resetting in case of errors
            return False
        
        if not should_reset:
            logger.debug("Weekly leaderboard reset not needed")
            return False
            
        logger.info("Resetting weekly leaderboard...")
        
        # Clear weekly leaderboard with error handling
        try:
            if not save_leaderboard({}, WEEKLY_LEADERBOARD_FILE):
                logger.error("Failed to save empty weekly leaderboard")
                return False
        except Exception as e:
            logger.error(f"Error saving empty weekly leaderboard: {str(e)}")
            return False
        
        # Update reset info with error handling
        try:
            reset_info = get_weekly_reset_info()
            if reset_info is None:
                logger.error("get_weekly_reset_info returned None")
                reset_info = {}
                
            # Validate reset_info structure
            if not isinstance(reset_info, dict):
                logger.error(f"Invalid reset_info type: {type(reset_info)}")
                reset_info = {}
                
            # Update last reset timestamp
            reset_info['last_reset'] = datetime.now().isoformat()
            
            # Ensure reset_day is set
            if 'reset_day' not in reset_info or not reset_info['reset_day']:
                reset_info['reset_day'] = 'Monday'
                
            # Save updated reset info
            if not save_weekly_reset_info(reset_info):
                logger.error("Failed to save weekly reset info")
                return False
                
        except Exception as e:
            logger.error(f"Error updating weekly reset info: {str(e)}")
            return False
        
        logger.info("Weekly leaderboard has been reset successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error in reset_weekly_leaderboard: {str(e)}")
        return False

def update_leaderboard(winner: str, loser: str, marble_change: int = 0) -> None:
    """Update both overall and weekly leaderboards.
    
    Args:
        winner: Username of the winner
        loser: Username of the loser
        marble_change: Number of marbles wagered
        
    Raises:
        ValueError: If usernames are invalid or marble_change is negative
        RuntimeError: If there's an error updating the leaderboard
    """
    # Validate inputs
    if not winner:
        logger.error("Empty winner username provided to update_leaderboard")
        raise ValueError("Winner username cannot be empty")
        
    if not loser:
        logger.error("Empty loser username provided to update_leaderboard")
        raise ValueError("Loser username cannot be empty")
    
    # Normalize usernames (remove @ prefix if present)
    if winner.startswith('@'):
        winner = winner[1:]
    if loser.startswith('@'):
        loser = loser[1:]
    
    # Validate marble change
    try:
        marble_change = int(marble_change)
        if marble_change < 0:
            logger.warning(f"Negative marble_change provided: {marble_change}, using absolute value")
            marble_change = abs(marble_change)
    except (ValueError, TypeError):
        logger.warning(f"Invalid marble_change value: {marble_change}, defaulting to 0")
        marble_change = 0
    
    # Reset weekly leaderboard if needed
    try:
        if reset_weekly_leaderboard():
            logger.info("Weekly leaderboard was reset before updating")
    except Exception as e:
        logger.error(f"Error during weekly leaderboard reset check: {str(e)}")
        # Continue with the update even if reset check fails
    
    try:
        # Load leaderboards with error handling
        try:
            overall = load_leaderboard(OVERALL_LEADERBOARD_FILE)
            if overall is None:
                logger.error("load_leaderboard returned None for overall leaderboard")
                overall = {}
        except Exception as e:
            logger.error(f"Error loading overall leaderboard: {str(e)}")
            overall = {}  # Use empty dict as fallback
            
        try:
            weekly = load_leaderboard(WEEKLY_LEADERBOARD_FILE)
            if weekly is None:
                logger.error("load_leaderboard returned None for weekly leaderboard")
                weekly = {}
        except Exception as e:
            logger.error(f"Error loading weekly leaderboard: {str(e)}")
            weekly = {}  # Use empty dict as fallback
        
        # Validate leaderboard data structures
        if not isinstance(overall, dict):
            logger.error(f"Invalid overall leaderboard type: {type(overall)}")
            overall = {}
            
        if not isinstance(weekly, dict):
            logger.error(f"Invalid weekly leaderboard type: {type(weekly)}")
            weekly = {}
        
        # Initialize user stats if they don't exist
        for leaderboard in [overall, weekly]:
            for user in [winner, loser]:
                if user not in leaderboard:
                    leaderboard[user] = {'wins': 0, 'losses': 0, 'marbles': 0}
                else:
                    # Validate existing user stats
                    required_fields = ['wins', 'losses', 'marbles']
                    for field in required_fields:
                        if field not in leaderboard[user]:
                            logger.warning(f"Missing {field} in {user}'s stats, initializing to 0")
                            leaderboard[user][field] = 0
                        elif not isinstance(leaderboard[user][field], int):
                            logger.warning(f"Invalid {field} type for {user}: {type(leaderboard[user][field])}, resetting to 0")
                            leaderboard[user][field] = 0
        
        # Update stats
        try:
            overall[winner]['wins'] += 1
            overall[loser]['losses'] += 1
            weekly[winner]['wins'] += 1
            weekly[loser]['losses'] += 1
            
            # Update marble counts
            overall[winner]['marbles'] += marble_change
            overall[loser]['marbles'] -= marble_change
            weekly[winner]['marbles'] += marble_change
            weekly[loser]['marbles'] -= marble_change
        except Exception as e:
            logger.error(f"Error updating user stats: {str(e)}")
            raise RuntimeError(f"Failed to update user statistics: {str(e)}")
        
        # Save updated leaderboards
        save_success = True
        try:
            if not save_leaderboard(overall, OVERALL_LEADERBOARD_FILE):
                logger.error("Failed to save overall leaderboard")
                save_success = False
        except Exception as e:
            logger.error(f"Error saving overall leaderboard: {str(e)}")
            save_success = False
            
        try:
            if not save_leaderboard(weekly, WEEKLY_LEADERBOARD_FILE):
                logger.error("Failed to save weekly leaderboard")
                save_success = False
        except Exception as e:
            logger.error(f"Error saving weekly leaderboard: {str(e)}")
            save_success = False
            
        if not save_success:
            raise RuntimeError("Failed to save leaderboard updates")
        
        logger.info(f"Leaderboard updated: {winner} won against {loser} with {marble_change} marbles")
    except Exception as e:
        logger.error(f"Error updating leaderboard: {str(e)}")
        raise RuntimeError(f"Failed to update leaderboard: {str(e)}")

def format_leaderboard(leaderboard: Dict[str, Dict[str, int]], title: str) -> str:
    """Format leaderboard for display.
    
    Args:
        leaderboard: Dictionary containing leaderboard data
        title: Title for the leaderboard
        
    Returns:
        Formatted leaderboard text
    """
    # Validate inputs
    if title is None or not isinstance(title, str):
        logger.warning(f"Invalid title provided to format_leaderboard: {title}")
        title = "Leaderboard"  # Use default title
    
    # Handle empty leaderboard
    if not leaderboard:
        return f"**{title}**\n\nNo battles yet! 🏆"
    
    # Validate leaderboard type
    if not isinstance(leaderboard, dict):
        logger.error(f"Invalid leaderboard type: {type(leaderboard)}")
        return f"**{title}**\n\nError: Invalid leaderboard data format."
    
    try:
        # Validate and clean leaderboard data
        valid_entries = {}
        default_stats = {'wins': 0, 'losses': 0, 'marbles': 0}
        
        for username, stats in leaderboard.items():
            # Skip entries with invalid usernames
            if not username or not isinstance(username, str):
                logger.warning(f"Skipping invalid username in leaderboard: {username}")
                continue
                
            # Skip entries with invalid stats
            if not isinstance(stats, dict):
                logger.warning(f"Skipping invalid stats for user {username}: {stats}")
                continue
                
            # Ensure all required fields exist with valid values
            valid_stats = default_stats.copy()
            for field in default_stats:
                if field in stats and isinstance(stats[field], (int, float)):
                    valid_stats[field] = int(stats[field])  # Convert to int to be safe
                else:
                    logger.warning(f"Invalid or missing {field} for user {username}, using default")
            
            # Only include users who have participated in battles
            if valid_stats['wins'] > 0 or valid_stats['losses'] > 0:
                valid_entries[username] = valid_stats
        
        # If no valid entries after cleaning
        if not valid_entries:
            return f"**{title}**\n\nNo valid battle records found! 🏆"
        
        # Sort by wins (primary), win rate (secondary), and marbles (tertiary)
        try:
            sorted_users = sorted(
                valid_entries.items(),
                key=lambda x: (
                    x[1]['wins'],  # Primary sort by wins
                    x[1]['wins'] / max(1, x[1]['wins'] + x[1]['losses']),  # Secondary sort by win rate
                    x[1]['marbles']  # Tertiary sort by marbles (as a tiebreaker)
                ),
                reverse=True
            )
        except Exception as e:
            logger.error(f"Error sorting leaderboard: {str(e)}")
            # Fallback to simpler sorting if complex sort fails
            sorted_users = sorted(
                valid_entries.items(),
                key=lambda x: x[1]['wins'],
                reverse=True
            )
        
        # Format the leaderboard text
        text = f"**{title}**\n\n"
        
        # Limit to top 10 users
        display_users = sorted_users[:10] if len(sorted_users) > 10 else sorted_users
        
        for i, (user, stats) in enumerate(display_users, 1):
            try:
                wins = stats['wins']
                losses = stats['losses']
                marbles = stats['marbles']
                total_battles = wins + losses
                
                # Calculate win rate safely
                try:
                    win_rate = (wins / total_battles * 100) if total_battles > 0 else 0
                except (ZeroDivisionError, TypeError):
                    win_rate = 0
                
                # Format display with error handling
                try:
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    
                    # Ensure username has @ prefix for display
                    display_username = user
                    if not display_username.startswith('@'):
                        display_username = f"@{display_username}"
                    
                    # Format the line with error handling for each part
                    line_parts = []
                    line_parts.append(f"{medal} {display_username}")
                    line_parts.append(f"{wins}W-{losses}L")
                    line_parts.append(f"({win_rate:.1f}%)")
                    line_parts.append(f"{marbles:+d} marbles")
                    
                    text += " | ".join(line_parts) + "\n"
                except Exception as e:
                    logger.error(f"Error formatting line for user {user}: {str(e)}")
                    text += f"{i}. @{user}: Error displaying stats\n"
            except Exception as e:
                logger.error(f"Error processing stats for user {user}: {str(e)}")
                text += f"{i}. @{user}: Error processing stats\n"
        
        return text
    except Exception as e:
        logger.error(f"Error formatting leaderboard: {str(e)}")
        return f"**{title}**\n\nError formatting leaderboard. Please try again later."

def get_user_stats(username: str) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Get a user's stats from both overall and weekly leaderboards.
    
    Args:
        username: Username to get stats for
        
    Returns:
        Tuple containing overall and weekly stats
        
    Raises:
        ValueError: If username is invalid
        RuntimeError: If there's an error loading the leaderboards
    """
    # Validate username
    if not username:
        logger.error("Empty username provided to get_user_stats")
        raise ValueError("Username cannot be empty")
    
    # Normalize username (remove @ prefix if present)
    if username.startswith('@'):
        username = username[1:]
    
    # Default stats structure
    default_stats = {'wins': 0, 'losses': 0, 'marbles': 0}
    
    try:
        # Load overall leaderboard
        try:
            overall = load_leaderboard(OVERALL_LEADERBOARD_FILE)
            if overall is None:
                logger.error("load_leaderboard returned None for overall leaderboard")
                overall = {}
        except Exception as e:
            logger.error(f"Error loading overall leaderboard: {str(e)}")
            overall = {}  # Use empty dict as fallback
        
        # Load weekly leaderboard
        try:
            weekly = load_leaderboard(WEEKLY_LEADERBOARD_FILE)
            if weekly is None:
                logger.error("load_leaderboard returned None for weekly leaderboard")
                weekly = {}
        except Exception as e:
            logger.error(f"Error loading weekly leaderboard: {str(e)}")
            weekly = {}  # Use empty dict as fallback
        
        # Validate leaderboard data structures
        if not isinstance(overall, dict):
            logger.error(f"Invalid overall leaderboard type: {type(overall)}")
            overall = {}
            
        if not isinstance(weekly, dict):
            logger.error(f"Invalid weekly leaderboard type: {type(weekly)}")
            weekly = {}
        
        # Get user stats with validation
        overall_stats = overall.get(username, default_stats.copy())
        weekly_stats = weekly.get(username, default_stats.copy())
        
        # Validate stats structure
        for stats, board_name in [(overall_stats, "overall"), (weekly_stats, "weekly")]:
            if not isinstance(stats, dict):
                logger.error(f"Invalid {board_name} stats type for {username}: {type(stats)}")
                stats = default_stats.copy()
                
            # Ensure all required fields exist
            for field in default_stats:
                if field not in stats:
                    logger.warning(f"Missing {field} in {username}'s {board_name} stats, initializing to 0")
                    stats[field] = 0
                elif not isinstance(stats[field], int):
                    logger.warning(f"Invalid {field} type in {username}'s {board_name} stats: {type(stats[field])}, resetting to 0")
                    stats[field] = 0
        
        logger.info(f"Retrieved stats for user {username}")
        return overall_stats, weekly_stats
        
    except Exception as e:
        logger.error(f"Error getting user stats for {username}: {str(e)}")
        # Return default stats as fallback
        return default_stats.copy(), default_stats.copy()