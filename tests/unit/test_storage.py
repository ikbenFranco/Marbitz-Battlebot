"""
Unit tests for the storage module.
"""

import os
import json
import pytest
from unittest.mock import patch, mock_open

from marbitz_battlebot.storage import load_json_file, save_json_file

class TestStorage:
    """Tests for the storage module."""
    
    def test_load_json_file_success(self, temp_dir):
        """Test loading a JSON file successfully."""
        # Arrange
        test_file = os.path.join(temp_dir, "test.json")
        test_data = {'user1': {'wins': 5, 'losses': 2, 'marbles': 30}}
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Act
        result = load_json_file(test_file)
        
        # Assert
        assert result == test_data
    
    def test_load_json_file_not_found(self):
        """Test loading a non-existent JSON file."""
        # Arrange
        test_file = 'nonexistent_file.json'
        
        # Act
        result = load_json_file(test_file)
        
        # Assert
        assert result == {}
    
    def test_save_json_file_success(self, temp_dir):
        """Test saving a JSON file successfully."""
        # Arrange
        test_file = os.path.join(temp_dir, "test.json")
        test_data = {'user1': {'wins': 5, 'losses': 2, 'marbles': 30}}
        
        # Act
        save_json_file(test_data, test_file)
        
        # Assert
        with open(test_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == test_data