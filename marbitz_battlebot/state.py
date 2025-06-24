"""
State management module for Marbitz Battlebot.

This module provides a class-based approach to manage application state,
including active challenges and challenge counters.
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from marbitz_battlebot.storage import (
    load_json_file, save_json_file, CHALLENGES_FILE
)

# Enable logging
logger = logging.getLogger(__name__)

class ChallengeManager:
    """
    Manages the state of active challenges in the application.
    
    This class provides thread-safe access to challenge data and ensures
    that challenges are properly persisted to storage.
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        """Implement singleton pattern to ensure only one instance exists."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ChallengeManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize the challenge manager."""
        # Skip initialization if already initialized (singleton pattern)
        if self._initialized:
            return
            
        with self._lock:
            self._active_challenges = {}
            self._challenge_counter = 0
            self._initialized = True
            self._load_state()
    
    def _load_state(self) -> None:
        """Load challenge state from storage."""
        try:
            self._active_challenges = load_json_file(CHALLENGES_FILE)
            
            # Calculate the highest challenge counter
            challenge_ids = [k for k in self._active_challenges.keys() if k.startswith('challenge_')]
            if challenge_ids:
                counters = [int(cid.split('_')[1]) for cid in challenge_ids if cid.split('_')[1].isdigit()]
                self._challenge_counter = max(counters, default=0)
                
            logger.info(f"Loaded {len(self._active_challenges)} active challenges. Challenge counter: {self._challenge_counter}")
        except Exception as e:
            logger.error(f"Error loading challenge state: {e}")
            self._active_challenges = {}
            self._challenge_counter = 0
    
    def _save_state(self) -> None:
        """Save challenge state to storage."""
        try:
            save_json_file(self._active_challenges, CHALLENGES_FILE)
            logger.info(f"Saved {len(self._active_challenges)} active challenges")
        except Exception as e:
            logger.error(f"Error saving challenge state: {e}")
    
    def create_challenge(self, challenger: str, challenged: str, wager_amount: int = 0) -> str:
        """
        Create a new challenge.
        
        Args:
            challenger: Username of the challenger
            challenged: Username of the challenged user
            wager_amount: Number of marbles wagered (default: 0)
            
        Returns:
            Challenge ID
        """
        with self._lock:
            self._challenge_counter += 1
            challenge_id = f"challenge_{self._challenge_counter}"
            
            self._active_challenges[challenge_id] = {
                'challenger_user': challenger,
                'challenged_user': challenged,
                'wager_amount': wager_amount,
                'timestamp': datetime.now().isoformat()
            }
            
            self._save_state()
            
            logger.info(f"Challenge {challenge_id} created: {challenger} vs {challenged} with {wager_amount} marbles")
            return challenge_id
    
    def get_challenge(self, challenge_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a challenge by ID.
        
        Args:
            challenge_id: ID of the challenge
            
        Returns:
            Challenge data or None if not found
        """
        with self._lock:
            return self._active_challenges.get(challenge_id)
    
    def update_challenge(self, challenge_id: str, data: Dict[str, Any]) -> bool:
        """
        Update a challenge with new data.
        
        Args:
            challenge_id: ID of the challenge
            data: New challenge data
            
        Returns:
            True if the challenge was updated, False otherwise
        """
        with self._lock:
            if challenge_id not in self._active_challenges:
                logger.warning(f"Attempted to update non-existent challenge {challenge_id}")
                return False
            
            self._active_challenges[challenge_id].update(data)
            self._save_state()
            
            logger.info(f"Challenge {challenge_id} updated")
            return True
    
    def remove_challenge(self, challenge_id: str) -> bool:
        """
        Remove a challenge.
        
        Args:
            challenge_id: ID of the challenge
            
        Returns:
            True if the challenge was removed, False otherwise
        """
        with self._lock:
            if challenge_id not in self._active_challenges:
                logger.warning(f"Attempted to remove non-existent challenge {challenge_id}")
                return False
            
            del self._active_challenges[challenge_id]
            self._save_state()
            
            logger.info(f"Challenge {challenge_id} removed")
            return True
    
    def find_user_challenge(self, username: str) -> Optional[str]:
        """
        Find a challenge created by a user.
        
        Args:
            username: Username to find challenges for
            
        Returns:
            Challenge ID or None if not found
        """
        with self._lock:
            for challenge_id, data in self._active_challenges.items():
                if data.get('challenger_user', '').lower() == username.lower():
                    return challenge_id
            
            return None
    
    def cleanup_expired_challenges(self, expiry_hours: int = 24) -> List[str]:
        """
        Remove challenges older than the specified time.
        
        Args:
            expiry_hours: Number of hours after which a challenge expires
            
        Returns:
            List of removed challenge IDs
        """
        with self._lock:
            now = datetime.now()
            expired_ids = []
            
            for challenge_id, data in list(self._active_challenges.items()):
                try:
                    challenge_time = datetime.fromisoformat(data['timestamp'])
                    if (now - challenge_time).total_seconds() > expiry_hours * 3600:
                        expired_ids.append(challenge_id)
                        del self._active_challenges[challenge_id]
                except (ValueError, KeyError) as e:
                    logger.error(f"Error processing challenge {challenge_id} during cleanup: {e}")
                    # Remove malformed challenges
                    expired_ids.append(challenge_id)
                    del self._active_challenges[challenge_id]
            
            if expired_ids:
                self._save_state()
                logger.info(f"Cleaned up {len(expired_ids)} expired challenges")
            
            return expired_ids
    
    def get_all_challenges(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active challenges.
        
        Returns:
            Dictionary of all active challenges
        """
        with self._lock:
            # Return a copy to prevent external modification
            return dict(self._active_challenges)
    
    def get_challenge_count(self) -> int:
        """
        Get the number of active challenges.
        
        Returns:
            Number of active challenges
        """
        with self._lock:
            return len(self._active_challenges)
    
    def get_challenge_counter(self) -> int:
        """
        Get the current challenge counter.
        
        Returns:
            Current challenge counter value
        """
        with self._lock:
            return self._challenge_counter