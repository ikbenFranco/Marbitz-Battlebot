"""
Pytest configuration and fixtures for Marbitz Battlebot tests.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def mock_update():
    """Create a mock Update object for testing handlers."""
    update = MagicMock()
    update.effective_user.username = "test_user"
    update.effective_user.id = 12345
    update.message.chat_id = 67890
    update.message.text = "Test message"
    
    return update

@pytest.fixture
def mock_context():
    """Create a mock Context object for testing handlers."""
    context = MagicMock()
    context.user_data = {}
    context.args = []
    
    return context