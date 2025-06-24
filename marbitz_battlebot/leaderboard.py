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
    reset_info = get_weekly_reset_info()
    reset_day = reset_info.get('reset_day', 'Monday')
    last_reset = reset_info.get('last_reset')
    
    now = datetime.now()
    current_weekday = now.strftime('%A')
    
    # If no previous reset, always reset on the reset day
    if last_reset is None and current_weekday == reset_day:
        return True
    
    # If we have a last reset date
    if last_reset:
        try:
            last_reset_date = datetime.fromisoformat(last_reset)
            
            # If it's the reset day and the last reset was not today
            if current_weekday == reset_day and last_reset_date.date() != now.date():
                # Check if the last reset was at least 6 days ago
                days_since_reset = (now - last_reset_date).days
                if days_since_reset >= 6:
                    return True
                
            # If it's been more than 7 days since the last reset (failsafe)
            if (now - last_reset_date).days >= 7:
                return True
                
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing last reset date: {e}")
            return current_weekday == reset_day  # Reset on the reset day if we can't parse the date
    
    return False

def reset_weekly_leaderboard() -> bool:
    """Reset the weekly leaderboard.
    
    Returns:
        True if the leaderboard was reset, False otherwise
    """
    if should_reset_weekly_leaderboard():
        try:
            # Clear weekly leaderboard
            save_leaderboard({}, WEEKLY_LEADERBOARD_FILE)
            
            # Update reset info
            reset_info = get_weekly_reset_info()
            reset_info['last_reset'] = datetime.now().isoformat()
            save_weekly_reset_info(reset_info)
            
            logger.info("Weekly leaderboard has been reset.")
            return True
        except Exception as e:
            logger.error(f"Error resetting weekly leaderboard: {e}")
            return False
    
    return False

def update_leaderboard(winner: str, loser: str, marble_change: int = 0) -> None:
    """Update both overall and weekly leaderboards.
    
    Args:
        winner: Username of the winner
        loser: Username of the loser
        marble_change: Number of marbles wagered
    """
    # Reset weekly leaderboard if needed
    reset_weekly_leaderboard()
    
    try:
        # Load leaderboards
        overall = load_leaderboard(OVERALL_LEADERBOARD_FILE)
        weekly = load_leaderboard(WEEKLY_LEADERBOARD_FILE)
        
        # Initialize user stats if they don't exist
        for leaderboard in [overall, weekly]:
            for user in [winner, loser]:
                if user not in leaderboard:
                    leaderboard[user] = {'wins': 0, 'losses': 0, 'marbles': 0}
        
        # Update stats
        overall[winner]['wins'] += 1
        overall[loser]['losses'] += 1
        weekly[winner]['wins'] += 1
        weekly[loser]['losses'] += 1
        
        # Update marble counts
        overall[winner]['marbles'] += marble_change
        overall[loser]['marbles'] -= marble_change
        weekly[winner]['marbles'] += marble_change
        weekly[loser]['marbles'] -= marble_change
        
        # Save updated leaderboards
        save_leaderboard(overall, OVERALL_LEADERBOARD_FILE)
        save_leaderboard(weekly, WEEKLY_LEADERBOARD_FILE)
        
        logger.info(f"Leaderboard updated: {winner} won against {loser} with {marble_change} marbles")
    except Exception as e:
        logger.error(f"Error updating leaderboard: {e}")
        raise

def format_leaderboard(leaderboard: Dict[str, Dict[str, int]], title: str) -> str:
    """Format leaderboard for display.
    
    Args:
        leaderboard: Dictionary containing leaderboard data
        title: Title for the leaderboard
        
    Returns:
        Formatted leaderboard text
    """
    if not leaderboard:
        return f"**{title}**\n\nNo battles yet! 🏆"
    
    try:
        # Sort by wins (primary), win rate (secondary), and marbles (tertiary)
        sorted_users = sorted(
            leaderboard.items(),
            key=lambda x: (
                x[1]['wins'],  # Primary sort by wins
                x[1]['wins'] / max(1, x[1]['wins'] + x[1]['losses']),  # Secondary sort by win rate
                x[1]['marbles']  # Tertiary sort by marbles (as a tiebreaker)
            ),
            reverse=True
        )
        
        text = f"**{title}**\n\n"
        for i, (user, stats) in enumerate(sorted_users[:10], 1):
            wins = stats['wins']
            losses = stats['losses']
            marbles = stats['marbles']
            total_battles = wins + losses
            win_rate = (wins / total_battles * 100) if total_battles > 0 else 0
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} @{user}: {wins}W-{losses}L ({win_rate:.1f}%) | {marbles:+d} marbles\n"
        
        return text
    except Exception as e:
        logger.error(f"Error formatting leaderboard: {e}")
        return f"**{title}**\n\nError formatting leaderboard. Please try again later."

def get_user_stats(username: str) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Get a user's stats from both overall and weekly leaderboards.
    
    Args:
        username: Username to get stats for
        
    Returns:
        Tuple containing overall and weekly stats
    """
    overall = load_leaderboard(OVERALL_LEADERBOARD_FILE)
    weekly = load_leaderboard(WEEKLY_LEADERBOARD_FILE)
    
    overall_stats = overall.get(username, {'wins': 0, 'losses': 0, 'marbles': 0})
    weekly_stats = weekly.get(username, {'wins': 0, 'losses': 0, 'marbles': 0})
    
    return overall_stats, weekly_stats