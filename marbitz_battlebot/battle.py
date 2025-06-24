"""
Battle module for Marbitz Battlebot.

This module handles battle mechanics including battle storylines and winner determination.
Challenge management is handled by the ChallengeManager class in the state module.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from marbitz_battlebot.state import ChallengeManager

# Enable logging
logger = logging.getLogger(__name__)

# Get the challenge manager instance
challenge_manager = ChallengeManager()

def initialize_battle_system() -> None:
    """Initialize the battle system."""
    # The ChallengeManager initializes itself when instantiated
    logger.info(f"Battle system initialized with {challenge_manager.get_challenge_count()} active challenges")

def create_challenge(challenger: str, challenged: str, wager_amount: int = 0) -> str:
    """Create a new challenge.
    
    Args:
        challenger: Username of the challenger
        challenged: Username of the challenged user
        wager_amount: Number of marbles wagered (default: 0)
        
    Returns:
        Challenge ID
        
    Raises:
        ValueError: If input parameters are invalid
    """
    # Validate inputs before passing to challenge manager
    if not challenger:
        logger.error("Empty challenger username provided")
        raise ValueError("Challenger username cannot be empty")
        
    if not challenged:
        logger.error("Empty challenged username provided")
        raise ValueError("Challenged username cannot be empty")
    
    # Remove @ prefix if present
    if challenger.startswith('@'):
        challenger = challenger[1:]
        
    if challenged.startswith('@'):
        challenged = challenged[1:]
    
    # Validate wager amount
    try:
        wager_amount = int(wager_amount)
    except (ValueError, TypeError):
        logger.warning(f"Invalid wager amount: {wager_amount}, setting to 0")
        wager_amount = 0
    
    try:
        return challenge_manager.create_challenge(challenger, challenged, wager_amount)
    except ValueError as e:
        logger.error(f"Error creating challenge: {str(e)}")
        raise

def get_challenge(challenge_id: str) -> Optional[Dict[str, Any]]:
    """Get a challenge by ID.
    
    Args:
        challenge_id: ID of the challenge
        
    Returns:
        Challenge data or None if not found
    """
    return challenge_manager.get_challenge(challenge_id)

def get_challenge_status(challenge_id: str, expiry_hours: int = 6) -> Dict[str, Any]:
    """Get the status of a challenge including expiry information.
    
    Args:
        challenge_id: ID of the challenge
        expiry_hours: Number of hours after which a challenge expires
        
    Returns:
        Dictionary containing challenge status information
        
    Raises:
        ValueError: If challenge_id is empty or challenge not found
    """
    if not challenge_id:
        logger.error("Empty challenge_id provided to get_challenge_status")
        raise ValueError("Challenge ID cannot be empty")
    
    challenge_data = get_challenge(challenge_id)
    if not challenge_data:
        logger.error(f"Challenge {challenge_id} not found in get_challenge_status")
        raise ValueError(f"Challenge {challenge_id} not found")
    
    result = {
        'challenge_id': challenge_id,
        'challenger': challenge_data.get('challenger_user', 'Unknown'),
        'challenged': challenge_data.get('challenged_user', 'Unknown'),
        'wager_amount': challenge_data.get('wager_amount', 0),
        'status': challenge_data.get('status', 'pending')
    }
    
    # Calculate expiry information
    try:
        if 'timestamp' in challenge_data:
            created_time = datetime.fromisoformat(challenge_data['timestamp'])
            now = datetime.now()
            time_elapsed = now - created_time
            expiry_time = created_time + timedelta(hours=expiry_hours)
            time_remaining = expiry_time - now
            
            result['created_at'] = created_time.strftime('%Y-%m-%d %H:%M:%S')
            result['expires_at'] = expiry_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Format time remaining in a user-friendly way
            if time_remaining.total_seconds() > 0:
                hours, remainder = divmod(int(time_remaining.total_seconds()), 3600)
                minutes = remainder // 60
                result['time_remaining'] = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                result['expired'] = False
            else:
                result['time_remaining'] = "Expired"
                result['expired'] = True
                
            # Calculate percentage of time elapsed
            total_seconds = expiry_hours * 3600
            elapsed_seconds = min(time_elapsed.total_seconds(), total_seconds)
            result['expiry_percentage'] = int((elapsed_seconds / total_seconds) * 100)
        else:
            result['created_at'] = "Unknown"
            result['expires_at'] = "Unknown"
            result['time_remaining'] = "Unknown"
            result['expired'] = False
            result['expiry_percentage'] = 0
    except Exception as e:
        logger.error(f"Error calculating expiry information: {str(e)}")
        result['created_at'] = "Error"
        result['expires_at'] = "Error"
        result['time_remaining'] = "Error"
        result['expired'] = False
        result['expiry_percentage'] = 0
    
    return result

def update_challenge(challenge_id: str, data: Dict[str, Any]) -> bool:
    """Update a challenge with new data.
    
    Args:
        challenge_id: ID of the challenge
        data: New challenge data
        
    Returns:
        True if the challenge was updated, False otherwise
        
    Raises:
        ValueError: If data is not a dictionary or challenge_id is empty
    """
    if not challenge_id:
        logger.error("Empty challenge_id provided to update_challenge")
        raise ValueError("Challenge ID cannot be empty")
        
    if not isinstance(data, dict):
        logger.error(f"Invalid data type provided to update_challenge: {type(data)}")
        raise ValueError("Data must be a dictionary")
    
    try:
        return challenge_manager.update_challenge(challenge_id, data)
    except Exception as e:
        logger.error(f"Error updating challenge {challenge_id}: {str(e)}")
        return False

def remove_challenge(challenge_id: str) -> bool:
    """Remove a challenge.
    
    Args:
        challenge_id: ID of the challenge
        
    Returns:
        True if the challenge was removed, False otherwise
        
    Raises:
        ValueError: If challenge_id is empty
    """
    if not challenge_id:
        logger.error("Empty challenge_id provided to remove_challenge")
        raise ValueError("Challenge ID cannot be empty")
    
    try:
        return challenge_manager.remove_challenge(challenge_id)
    except Exception as e:
        logger.error(f"Error removing challenge {challenge_id}: {str(e)}")
        return False

def find_user_challenge(username: str) -> Optional[str]:
    """Find a challenge created by a user.
    
    Args:
        username: Username to find challenges for
        
    Returns:
        Challenge ID or None if not found
        
    Raises:
        ValueError: If username is empty
    """
    if not username:
        logger.error("Empty username provided to find_user_challenge")
        raise ValueError("Username cannot be empty")
    
    # Remove @ prefix if present
    if username.startswith('@'):
        username = username[1:]
    
    try:
        return challenge_manager.find_user_challenge(username)
    except Exception as e:
        logger.error(f"Error finding challenge for user {username}: {str(e)}")
        return None

def get_all_challenges() -> Dict[str, Dict[str, Any]]:
    """Get all active challenges.
    
    Returns:
        Dictionary of all active challenges
    """
    return challenge_manager.get_all_challenges()

def cleanup_expired_challenges(expiry_hours: int = 6) -> List[str]:
    """Remove challenges older than the specified time.
    
    Args:
        expiry_hours: Number of hours after which a challenge expires (default: 6)
        
    Returns:
        List of removed challenge IDs
    """
    if expiry_hours <= 0:
        logger.warning(f"Invalid expiry_hours value: {expiry_hours}, using default of 6")
        expiry_hours = 6
        
    return challenge_manager.cleanup_expired_challenges(expiry_hours)

def generate_battle_story(challenger: str, challenged: str) -> Dict[str, Any]:
    """Generate a dramatic battle story.
    
    Args:
        challenger: Username of the challenger
        challenged: Username of the challenged user
        
    Returns:
        Dictionary containing battle story elements
        
    Raises:
        ValueError: If usernames are empty
    """
    if not challenger:
        logger.error("Empty challenger username provided to generate_battle_story")
        raise ValueError("Challenger username cannot be empty")
        
    if not challenged:
        logger.error("Empty challenged username provided to generate_battle_story")
        raise ValueError("Challenged username cannot be empty")
    
    # Ensure usernames have @ prefix
    if not challenger.startswith('@'):
        challenger = f"@{challenger}"
        
    if not challenged.startswith('@'):
        challenged = f"@{challenged}"
    
    # Sanitize usernames to prevent injection
    challenger = challenger.replace('\n', ' ').replace('\r', ' ')
    challenged = challenged.replace('\n', ' ').replace('\r', ' ')
    
    battle_scenarios = [
        {
            "setup": f"🏛️ The arena falls silent as {challenger} and {challenged} face off...",
            "phases": [
                f"⚔️ {challenger} charges forward with a fierce battle cry!",
                f"🛡️ {challenged} deflects the attack and counters!",
                f"💥 The clash echoes through the marble halls!"
            ]
        },
        {
            "setup": f"🌩️ Lightning crackles as {challenger} challenges {challenged} to combat!",
            "phases": [
                f"🔥 {challenger} unleashes a flurry of marble strikes!",
                f"❄️ {challenged} responds with an icy defensive maneuver!",
                f"⚡ The elements collide in spectacular fashion!"
            ]
        },
        {
            "setup": f"🏴‍☠️ The battleground is set as {challenger} draws their weapon against {challenged}!",
            "phases": [
                f"🗡️ {challenger} spins with deadly precision!",
                f"🛡️ {challenged} parries and launches a counterattack!",
                f"💫 Sparks fly as marble meets marble!"
            ]
        },
        {
            "setup": f"🌋 The volcanic arena rumbles as {challenger} and {challenged} take their positions!",
            "phases": [
                f"🔥 {challenger} launches a blazing offensive maneuver!",
                f"💨 {challenged} creates a whirlwind defense, scattering the attack!",
                f"☄️ Molten marbles fly through the air as the battle intensifies!"
            ]
        },
        {
            "setup": f"🌊 Waves crash against the coastal arena as {challenger} challenges {challenged}!",
            "phases": [
                f"🌪️ {challenger} summons a swirling vortex of marbles!",
                f"🧊 {challenged} creates a frozen barrier, stopping the assault!",
                f"💦 The tide of battle shifts back and forth between the combatants!"
            ]
        }
    ]
    
    try:
        return random.choice(battle_scenarios)
    except IndexError:
        # Fallback scenario in case the list is empty (should never happen)
        logger.error("Battle scenarios list is empty, using fallback scenario")
        return {
            "setup": f"⚔️ {challenger} and {challenged} face off in an epic battle!",
            "phases": [
                f"{challenger} attacks!",
                f"{challenged} defends!",
                f"The battle rages on!"
            ]
        }

def determine_winner(challenger: str, challenged: str) -> Tuple[str, str]:
    """Determine the winner of a battle.
    
    Args:
        challenger: Username of the challenger
        challenged: Username of the challenged user
        
    Returns:
        Tuple containing (winner, loser)
        
    Raises:
        ValueError: If usernames are empty
    """
    if not challenger:
        logger.error("Empty challenger username provided to determine_winner")
        raise ValueError("Challenger username cannot be empty")
        
    if not challenged:
        logger.error("Empty challenged username provided to determine_winner")
        raise ValueError("Challenged username cannot be empty")
    
    # Sanitize usernames to prevent injection
    challenger = challenger.replace('\n', ' ').replace('\r', ' ')
    challenged = challenged.replace('\n', ' ').replace('\r', ' ')
    
    winner = random.choice([challenger, challenged])
    loser = challenged if winner == challenger else challenger
    
    logger.info(f"Battle result: {winner} defeated {loser}")
    return winner, loser