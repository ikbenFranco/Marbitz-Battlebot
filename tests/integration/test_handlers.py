"""
Integration tests for the handlers module.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from telegram.ext import ConversationHandler

from marbitz_battlebot.handlers import (
    start_command, help_command
)

class TestHandlers:
    """Integration tests for the handlers module."""
    
    @pytest.mark.asyncio
    async def test_start_command(self, mock_update, mock_context):
        """Test the start command."""
        # Arrange
        mock_update.message.reply_text = AsyncMock()
        
        # Act
        await start_command(mock_update, mock_context)
        
        # Assert
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        assert "Welcome to Marbitz Battlebot" in args[0]
    
    @pytest.mark.asyncio
    async def test_help_command(self, mock_update, mock_context):
        """Test the help command."""
        # Arrange
        mock_update.message.reply_text = AsyncMock()
        
        # Act
        await help_command(mock_update, mock_context)
        
        # Assert
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        assert "Marbitz Battlebot Commands" in args[0]