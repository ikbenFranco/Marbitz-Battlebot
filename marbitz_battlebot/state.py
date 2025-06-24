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
    
    def _save_state(self) -> bool:
        """
        Save challenge state to storage.
        
        Returns:
            True if save was successful, False otherwise
        """
        try:
            success = save_json_file(self._active_challenges, CHALLENGES_FILE)
            if success:
                logger.info(f"Saved {len(self._active_challenges)} active challenges")
            else:
                logger.error("Failed to save challenge state")
            return success
        except Exception as e:
            logger.error(f"Error saving challenge state: {e}")
            return False
    
    def create_challenge(self, challenger: str, challenged: str, wager_amount: int = 0) -> str:
        """
        Create a new challenge.
        
        Args:
            challenger: Username of the challenger
            challenged: Username of the challenged user
            wager_amount: Number of marbles wagered (default: 0)
            
        Returns:
            Challenge ID
            
        Raises:
            ValueError: If input parameters are invalid
        """
        # Validate inputs
        if not challenger:
            logger.error("Empty challenger username provided")
            raise ValueError("Challenger username cannot be empty")
            
        if not challenged:
            logger.error("Empty challenged username provided")
            raise ValueError("Challenged username cannot be empty")
            
        if challenger.lower() == challenged.lower():
            logger.error(f"User {challenger} attempted to challenge themselves")
            raise ValueError("Users cannot challenge themselves")
            
        try:
            wager_amount = int(wager_amount)
            if wager_amount < 0:
                logger.warning(f"Negative wager amount ({wager_amount}) provided, setting to 0")
                wager_amount = 0
        except (ValueError, TypeError):
            logger.warning(f"Invalid wager amount ({wager_amount}) provided, setting to 0")
            wager_amount = 0
            
        # Check if user already has an active challenge
        existing_challenge = self.find_user_challenge(challenger)
        if existing_challenge:
            logger.warning(f"User {challenger} already has an active challenge: {existing_challenge}")
            raise ValueError(f"User already has an active challenge: {existing_challenge}")
        
        with self._lock:
            self._challenge_counter += 1
            challenge_id = f"challenge_{self._challenge_counter}"
            
            self._active_challenges[challenge_id] = {
                'challenger_user': challenger,
                'challenged_user': challenged,
                'wager_amount': wager_amount,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'  # Add a status field for better tracking
            }
            
            save_success = self._save_state()
            if not save_success:
                logger.warning(f"Failed to save state after creating challenge {challenge_id}")
            
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
            
        Raises:
            ValueError: If data is not a dictionary
        """
        if not challenge_id:
            logger.error("Empty challenge_id provided to update_challenge")
            return False
            
        if not isinstance(data, dict):
            logger.error(f"Invalid data type provided to update_challenge: {type(data)}")
            raise ValueError("Data must be a dictionary")
            
        # Validate specific fields if present
        if 'wager_amount' in data:
            try:
                data['wager_amount'] = int(data['wager_amount'])
                if data['wager_amount'] < 0:
                    logger.warning(f"Negative wager amount ({data['wager_amount']}) provided, setting to 0")
                    data['wager_amount'] = 0
            except (ValueError, TypeError):
                logger.warning(f"Invalid wager amount ({data['wager_amount']}) provided, setting to 0")
                data['wager_amount'] = 0
                
        if 'status' in data and data['status'] not in ['pending', 'accepted', 'declined', 'completed', 'expired']:
            logger.warning(f"Invalid status value: {data['status']}, ignoring")
            del data['status']
        
        with self._lock:
            if challenge_id not in self._active_challenges:
                logger.warning(f"Attempted to update non-existent challenge {challenge_id}")
                return False
            
            # Keep a copy of the original data for logging
            original_data = dict(self._active_challenges[challenge_id])
            
            # Update the challenge
            self._active_challenges[challenge_id].update(data)
            
            # Save the state
            save_success = self._save_state()
            if not save_success:
                logger.warning(f"Failed to save state after updating challenge {challenge_id}")
                # Revert the changes if save failed
                self._active_challenges[challenge_id] = original_data
                return False
            
            logger.info(f"Challenge {challenge_id} updated: {data}")
            return True
    
    def remove_challenge(self, challenge_id: str) -> bool:
        """
        Remove a challenge.
        
        Args:
            challenge_id: ID of the challenge
            
        Returns:
            True if the challenge was removed, False otherwise
        """
        if not challenge_id:
            logger.error("Empty challenge_id provided to remove_challenge")
            return False
            
        with self._lock:
            if challenge_id not in self._active_challenges:
                logger.warning(f"Attempted to remove non-existent challenge {challenge_id}")
                return False
            
            # Keep a copy of the challenge for logging and potential recovery
            removed_challenge = dict(self._active_challenges[challenge_id])
            
            # Remove the challenge
            del self._active_challenges[challenge_id]
            
            # Save the state
            save_success = self._save_state()
            if not save_success:
                logger.warning(f"Failed to save state after removing challenge {challenge_id}")
                # Revert the removal if save failed
                self._active_challenges[challenge_id] = removed_challenge
                return False
            
            logger.info(f"Challenge {challenge_id} removed: {removed_challenge}")
            return True
    
    def find_user_challenge(self, username: str) -> Optional[str]:
        """
        Find a challenge created by a user.
        
        Args:
            username: Username to find challenges for
            
        Returns:
            Challenge ID or None if not found
            
        Raises:
            ValueError: If username is empty or None
        """
        if not username:
            logger.error("Empty username provided to find_user_challenge")
            raise ValueError("Username cannot be empty")
            
        username = username.lower().strip()
        if username.startswith('@'):
            username = username[1:]  # Remove @ prefix if present
            
        with self._lock:
            for challenge_id, data in self._active_challenges.items():
                challenger = data.get('challenger_user', '').lower().strip()
                if challenger.startswith('@'):
                    challenger = challenger[1:]  # Remove @ prefix if present
                    
                if challenger == username:
                    logger.debug(f"Found challenge {challenge_id} for user {username}")
                    return challenge_id
            
            logger.debug(f"No active challenges found for user {username}")
            return None
    
    def cleanup_expired_challenges(self, expiry_hours: int = 24) -> List[str]:
        """
        Remove challenges older than the specified time.
        
        Args:
            expiry_hours: Number of hours after which a challenge expires
            
        Returns:
            List of removed challenge IDs
        """
        if expiry_hours <= 0:
            logger.warning(f"Invalid expiry_hours value: {expiry_hours}, using default of 24")
            expiry_hours = 24
            
        with self._lock:
            now = datetime.now()
            expired_ids = []
            removed_challenges = {}
            
            for challenge_id, data in list(self._active_challenges.items()):
                try:
                    # Skip challenges that don't have a timestamp
                    if 'timestamp' not in data:
                        logger.warning(f"Challenge {challenge_id} has no timestamp, marking for removal")
                        expired_ids.append(challenge_id)
                        removed_challenges[challenge_id] = dict(data)
                        del self._active_challenges[challenge_id]
                        continue
                        
                    # Parse the timestamp
                    try:
                        challenge_time = datetime.fromisoformat(data['timestamp'])
                    except (ValueError, TypeError):
                        logger.warning(f"Challenge {challenge_id} has invalid timestamp: {data.get('timestamp')}, marking for removal")
                        expired_ids.append(challenge_id)
                        removed_challenges[challenge_id] = dict(data)
                        del self._active_challenges[challenge_id]
                        continue
                    
                    # Check if the challenge has expired
                    if (now - challenge_time).total_seconds() > expiry_hours * 3600:
                        logger.debug(f"Challenge {challenge_id} has expired (created: {challenge_time})")
                        expired_ids.append(challenge_id)
                        removed_challenges[challenge_id] = dict(data)
                        del self._active_challenges[challenge_id]
                        
                except Exception as e:
                    logger.error(f"Error processing challenge {challenge_id} during cleanup: {e}")
                    # Remove malformed challenges
                    expired_ids.append(challenge_id)
                    removed_challenges[challenge_id] = dict(data)
                    del self._active_challenges[challenge_id]
            
            if expired_ids:
                save_success = self._save_state()
                if not save_success:
                    logger.warning("Failed to save state after cleaning up expired challenges")
                    # Revert the removals if save failed
                    for challenge_id, data in removed_challenges.items():
                        self._active_challenges[challenge_id] = data
                    return []
                    
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