"""
Battle module for Marbitz Battlebot.

This module handles battle mechanics including battle storylines and winner determination.
Challenge management is handled by the ChallengeManager class in the state module.
"""

import logging
import random
from datetime import datetime
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
    """
    return challenge_manager.create_challenge(challenger, challenged, wager_amount)

def get_challenge(challenge_id: str) -> Optional[Dict[str, Any]]:
    """Get a challenge by ID.
    
    Args:
        challenge_id: ID of the challenge
        
    Returns:
        Challenge data or None if not found
    """
    return challenge_manager.get_challenge(challenge_id)

def update_challenge(challenge_id: str, data: Dict[str, Any]) -> bool:
    """Update a challenge with new data.
    
    Args:
        challenge_id: ID of the challenge
        data: New challenge data
        
    Returns:
        True if the challenge was updated, False otherwise
    """
    return challenge_manager.update_challenge(challenge_id, data)

def remove_challenge(challenge_id: str) -> bool:
    """Remove a challenge.
    
    Args:
        challenge_id: ID of the challenge
        
    Returns:
        True if the challenge was removed, False otherwise
    """
    return challenge_manager.remove_challenge(challenge_id)

def find_user_challenge(username: str) -> Optional[str]:
    """Find a challenge created by a user.
    
    Args:
        username: Username to find challenges for
        
    Returns:
        Challenge ID or None if not found
    """
    return challenge_manager.find_user_challenge(username)

def cleanup_expired_challenges(expiry_hours: int = 24) -> List[str]:
    """Remove challenges older than the specified time.
    
    Args:
        expiry_hours: Number of hours after which a challenge expires
        
    Returns:
        List of removed challenge IDs
    """
    return challenge_manager.cleanup_expired_challenges(expiry_hours)

def generate_battle_story(challenger: str, challenged: str) -> Dict[str, Any]:
    """Generate a dramatic battle story.
    
    Args:
        challenger: Username of the challenger
        challenged: Username of the challenged user
        
    Returns:
        Dictionary containing battle story elements
    """
    battle_scenarios = [
        {
            "setup": f"🏛️ The arena falls silent as @{challenger} and @{challenged} face off...",
            "phases": [
                f"⚔️ @{challenger} charges forward with a fierce battle cry!",
                f"🛡️ @{challenged} deflects the attack and counters!",
                f"💥 The clash echoes through the marble halls!"
            ]
        },
        {
            "setup": f"🌩️ Lightning crackles as @{challenger} challenges @{challenged} to combat!",
            "phases": [
                f"🔥 @{challenger} unleashes a flurry of marble strikes!",
                f"❄️ @{challenged} responds with an icy defensive maneuver!",
                f"⚡ The elements collide in spectacular fashion!"
            ]
        },
        {
            "setup": f"🏴‍☠️ The battleground is set as @{challenger} draws their weapon against @{challenged}!",
            "phases": [
                f"🗡️ @{challenger} spins with deadly precision!",
                f"🛡️ @{challenged} parries and launches a counterattack!",
                f"💫 Sparks fly as marble meets marble!"
            ]
        },
        {
            "setup": f"🌋 The volcanic arena rumbles as @{challenger} and @{challenged} take their positions!",
            "phases": [
                f"🔥 @{challenger} launches a blazing offensive maneuver!",
                f"💨 @{challenged} creates a whirlwind defense, scattering the attack!",
                f"☄️ Molten marbles fly through the air as the battle intensifies!"
            ]
        },
        {
            "setup": f"🌊 Waves crash against the coastal arena as @{challenger} challenges @{challenged}!",
            "phases": [
                f"🌪️ @{challenger} summons a swirling vortex of marbles!",
                f"🧊 @{challenged} creates a frozen barrier, stopping the assault!",
                f"💦 The tide of battle shifts back and forth between the combatants!"
            ]
        }
    ]
    
    return random.choice(battle_scenarios)

def determine_winner(challenger: str, challenged: str) -> Tuple[str, str]:
    """Determine the winner of a battle.
    
    Args:
        challenger: Username of the challenger
        challenged: Username of the challenged user
        
    Returns:
        Tuple containing (winner, loser)
    """
    winner = random.choice([challenger, challenged])
    loser = challenged if winner == challenger else challenger
    
    logger.info(f"Battle result: {winner} defeated {loser}")
    return winner, loser

def generate_battle_story(challenger: str, challenged: str) -> Dict[str, Any]:
    """Generate a dramatic battle story.
    
    Args:
        challenger: Username of the challenger
        challenged: Username of the challenged user
        
    Returns:
        Dictionary containing battle story elements
    """
    battle_scenarios = [
        {
            "setup": f"🏛️ The arena falls silent as @{challenger} and @{challenged} face off...",
            "phases": [
                f"⚔️ @{challenger} charges forward with a fierce battle cry!",
                f"🛡️ @{challenged} deflects the attack and counters!",
                f"💥 The clash echoes through the marble halls!"
            ]
        },
        {
            "setup": f"🌩️ Lightning crackles as @{challenger} challenges @{challenged} to combat!",
            "phases": [
                f"🔥 @{challenger} unleashes a flurry of marble strikes!",
                f"❄️ @{challenged} responds with an icy defensive maneuver!",
                f"⚡ The elements collide in spectacular fashion!"
            ]
        },
        {
            "setup": f"🏴‍☠️ The battleground is set as @{challenger} draws their weapon against @{challenged}!",
            "phases": [
                f"🗡️ @{challenger} spins with deadly precision!",
                f"🛡️ @{challenged} parries and launches a counterattack!",
                f"💫 Sparks fly as marble meets marble!"
            ]
        },
        {
            "setup": f"🌋 The volcanic arena rumbles as @{challenger} and @{challenged} take their positions!",
            "phases": [
                f"🔥 @{challenger} launches a blazing offensive maneuver!",
                f"💨 @{challenged} creates a whirlwind defense, scattering the attack!",
                f"☄️ Molten marbles fly through the air as the battle intensifies!"
            ]
        },
        {
            "setup": f"🌊 Waves crash against the coastal arena as @{challenger} challenges @{challenged}!",
            "phases": [
                f"🌪️ @{challenger} summons a swirling vortex of marbles!",
                f"🧊 @{challenged} creates a frozen barrier, stopping the assault!",
                f"💦 The tide of battle shifts back and forth between the combatants!"
            ]
        }
    ]
    
    return random.choice(battle_scenarios)

def determine_winner(challenger: str, challenged: str) -> Tuple[str, str]:
    """Determine the winner of a battle.
    
    Args:
        challenger: Username of the challenger
        challenged: Username of the challenged user
        
    Returns:
        Tuple containing (winner, loser)
    """
    winner = random.choice([challenger, challenged])
    loser = challenged if winner == challenger else challenger
    
    logger.info(f"Battle result: {winner} defeated {loser}")
    return winner, loser