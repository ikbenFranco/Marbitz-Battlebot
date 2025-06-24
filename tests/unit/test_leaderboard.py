"""
Unit tests for the leaderboard module.
"""

import pytest
from unittest.mock import patch, MagicMock

from marbitz_battlebot.leaderboard import format_leaderboard

class TestLeaderboard:
    """Tests for the leaderboard module."""
    
    def test_format_leaderboard_empty(self):
        """Test format_leaderboard with an empty leaderboard."""
        # Arrange
        leaderboard = {}
        title = "Test Leaderboard"
        
        # Act
        result = format_leaderboard(leaderboard, title)
        
        # Assert
        assert "Test Leaderboard" in result
        assert "No battles yet!" in result
    
    def test_format_leaderboard(self):
        """Test format_leaderboard with data."""
        # Arrange
        leaderboard = {
            "user1": {"wins": 10, "losses": 2, "marbles": 50},
            "user2": {"wins": 8, "losses": 5, "marbles": 30},
            "user3": {"wins": 5, "losses": 10, "marbles": -20}
        }
        title = "Test Leaderboard"
        
        # Act
        result = format_leaderboard(leaderboard, title)
        
        # Assert
        assert "Test Leaderboard" in result
        assert "@user1" in result
        assert "@user2" in result
        assert "@user3" in result
        assert "10W-2L" in result  # user1's record
        assert "83.3%" in result  # user1's win rate (10/12 * 100)