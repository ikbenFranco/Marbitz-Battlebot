"""
Unit tests for the state module.
"""

import pytest
from unittest.mock import patch, MagicMock

from marbitz_battlebot.state import ChallengeManager

class TestChallengeManager:
    """Tests for the ChallengeManager class."""
    
    @patch('marbitz_battlebot.state.load_json_file')
    @patch('marbitz_battlebot.state.save_json_file')
    def test_singleton_pattern(self, mock_save, mock_load):
        """Test that ChallengeManager follows the singleton pattern."""
        # Arrange
        mock_load.return_value = {}
        
        # Act
        manager1 = ChallengeManager()
        manager2 = ChallengeManager()
        
        # Assert
        assert manager1 is manager2
    
    @patch('marbitz_battlebot.state.load_json_file')
    @patch('marbitz_battlebot.state.save_json_file')
    def test_create_challenge(self, mock_save, mock_load):
        """Test creating a challenge."""
        # Arrange
        mock_load.return_value = {}
        ChallengeManager._instance = None  # Reset singleton
        
        manager = ChallengeManager()
        challenger = "user1"
        challenged = "user2"
        wager_amount = 10
        
        # Act
        challenge_id = manager.create_challenge(challenger, challenged, wager_amount)
        
        # Assert
        assert challenge_id.startswith("challenge_")
        assert manager.get_challenge(challenge_id) is not None
        assert manager.get_challenge(challenge_id)['challenger_user'] == challenger
        assert manager.get_challenge(challenge_id)['challenged_user'] == challenged
        assert manager.get_challenge(challenge_id)['wager_amount'] == wager_amount
        assert 'timestamp' in manager.get_challenge(challenge_id)
        
        # Verify save was called
        mock_save.assert_called_once()
    
    @patch('marbitz_battlebot.state.load_json_file')
    @patch('marbitz_battlebot.state.save_json_file')
    def test_get_challenge(self, mock_save, mock_load):
        """Test getting a challenge."""
        # Arrange
        mock_load.return_value = {}
        ChallengeManager._instance = None  # Reset singleton
        
        manager = ChallengeManager()
        challenge_id = manager.create_challenge("user1", "user2", 10)
        
        # Act
        challenge = manager.get_challenge(challenge_id)
        
        # Assert
        assert challenge is not None
        assert challenge['challenger_user'] == "user1"
        assert challenge['challenged_user'] == "user2"
        assert challenge['wager_amount'] == 10