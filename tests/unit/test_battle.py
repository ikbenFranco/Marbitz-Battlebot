"""
Unit tests for the battle module.
"""

import pytest
from unittest.mock import patch, MagicMock

from marbitz_battlebot.battle import (
    generate_battle_story, determine_winner
)

class TestBattle:
    """Tests for the battle module."""
    
    def test_generate_battle_story(self):
        """Test generating a battle story."""
        # Arrange
        challenger = "user1"
        challenged = "user2"
        
        # Act
        story = generate_battle_story(challenger, challenged)
        
        # Assert
        assert isinstance(story, dict)
        assert "setup" in story
        assert "phases" in story
        assert isinstance(story["phases"], list)
        assert len(story["phases"]) > 0
        assert challenger in story["setup"]
        assert challenged in story["setup"]
    
    def test_determine_winner(self):
        """Test determining a winner."""
        # Arrange
        challenger = "user1"
        challenged = "user2"
        
        # Act
        winner, loser = determine_winner(challenger, challenged)
        
        # Assert
        assert winner in [challenger, challenged]
        assert loser in [challenger, challenged]
        assert winner != loser