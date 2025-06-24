"""
Simplified handlers without conversation handler for testing.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from marbitz_battlebot.battle import (
    create_challenge, get_challenge, update_challenge, remove_challenge, 
    find_user_challenge, generate_battle_story, determine_winner
)

logger = logging.getLogger(__name__)

async def simple_challenge_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simple challenge command without conversation handler."""
    logger.info(f"Simple challenge command received from user: {update.effective_user.username if update.effective_user else 'Unknown'}")
    
    try:
        # Check if the command has arguments
        if not context.args or not context.args[0]:
            await update.message.reply_text(
                "⚠️ Usage: /challenge @username\n\n"
                "Example: /challenge @MarbleWarrior"
            )
            return
        
        # Validate challenger has a username
        challenger = update.effective_user.username
        if not challenger:
            await update.message.reply_text(
                "⚠️ You need a username to participate in battles!\n\n"
                "Please set a username in your Telegram profile settings and try again."
            )
            return
        
        # Validate and sanitize challenged username
        challenged_input = context.args[0].lstrip('@').strip()
        
        # Check if challenged username is empty after stripping
        if not challenged_input:
            await update.message.reply_text(
                "⚠️ Invalid username format.\n\n"
                "Usage: /challenge @username"
            )
            return
        
        # Check if user is challenging themselves
        if challenged_input.lower() == challenger.lower():
            await update.message.reply_text("⚠️ You can't challenge yourself! 😅")
            return
        
        # Check if user already has an active challenge
        existing_challenge = find_user_challenge(challenger)
        if existing_challenge:
            await update.message.reply_text(
                "⚠️ You already have an active challenge!\n\n"
                "Please wait for your current challenge to complete or use /cancel_challenge to cancel it."
            )
            return
        
        # Create a new challenge with no wager for simplicity
        try:
            challenge_id = create_challenge(challenger, challenged_input, 0)
            logger.info(f"Challenge created: {challenger} vs {challenged_input} (ID: {challenge_id})")
        except ValueError as e:
            await update.message.reply_text(f"⚠️ Error creating challenge: {str(e)}")
            return
        except Exception as e:
            logger.error(f"Unexpected error in challenge_command: {str(e)}")
            await update.message.reply_text(
                "⚠️ An unexpected error occurred while creating the challenge. Please try again later."
            )
            return
        
        # Create accept/decline buttons
        keyboard = [
            [InlineKeyboardButton("Accept Battle! ⚔️", callback_data=f"accept_{challenge_id}")],
            [InlineKeyboardButton("Decline 😔", callback_data=f"decline_{challenge_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"⚔️ @{challenger} challenges @{challenged_input} to a marble battle!\n\n"
            f"@{challenged_input}, do you accept this challenge?",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Unhandled exception in simple_challenge_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ An error occurred while processing your command. Please try again later."
        )

async def simple_challenge_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simple challenge response handler."""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    logger.info(f"Simple challenge response received - Data: '{query.data}', User: {query.from_user.username if query.from_user else 'Unknown'}")
    
    try:
        # Parse callback data
        callback_data = query.data.split("_", 1)
        if len(callback_data) < 2:
            logger.error(f"Invalid callback data format: {query.data}")
            await query.edit_message_text("⚠️ An error occurred. Please try again with /challenge @username.")
            return
            
        action, challenge_id = callback_data[0], callback_data[1]
        
        # Get challenge data
        challenge_data = get_challenge(challenge_id)
        if not challenge_data:
            logger.warning(f"Challenge ID '{challenge_id}' not found")
            await query.edit_message_text(
                "⚠️ This challenge is no longer active or has expired.\n\n"
                "Please create a new challenge with /challenge @username."
            )
            return
        
        challenger = challenge_data['challenger_user']
        challenged = challenge_data['challenged_user']
        
        # Verify user authorization (simplified)
        user_clicking = query.from_user.username
        if not user_clicking:
            await query.edit_message_text("⚠️ You need a username to respond to challenges.")
            return
        
        if user_clicking.lower() != challenged.lower():
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"⚠️ Sorry @{user_clicking}, only @{challenged} can accept or decline this battle."
            )
            return
        
        # Remove challenge
        remove_challenge(challenge_id)
        
        if action == 'accept':
            # Simple battle without story for testing
            import random
            winner = random.choice([challenger, challenged])
            loser = challenged if winner == challenger else challenger
            
            await query.edit_message_text(
                f"🏆 **VICTORY!** @{winner} emerges triumphant over @{loser}!\n\n"
                f"Battle completed successfully! 🎉"
            )
            
        else:  # decline
            await query.edit_message_text(
                f"😔 @{challenged} has declined the challenge from @{challenger}.\n"
                f"Maybe next time! 🏛️"
            )
        
    except Exception as e:
        logger.error(f"Error in simple_challenge_response: {str(e)}")
        await query.edit_message_text("⚠️ An error occurred while processing your response.")