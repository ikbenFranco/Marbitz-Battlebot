"""
Handlers module for Marbitz Battlebot.

This module contains the command handlers for the Telegram bot.
"""

import os
import logging
import asyncio
import random
from typing import Dict, Any, Optional, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from marbitz_battlebot.battle import (
    create_challenge, get_challenge, update_challenge, remove_challenge, 
    find_user_challenge, generate_battle_story, determine_winner,
    get_challenge_status
)
from marbitz_battlebot.leaderboard import (
    update_leaderboard, format_leaderboard, get_user_stats,
    OVERALL_LEADERBOARD_FILE, WEEKLY_LEADERBOARD_FILE
)
from marbitz_battlebot.storage import load_leaderboard

# Enable logging
logger = logging.getLogger(__name__)

# States for conversation handler
WAGER_AMOUNT, CHALLENGE_CONFIRMATION = range(2)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    logger.info(f"Start command received from user: {update.effective_user.username if update.effective_user else 'Unknown'}")
    
    welcome_text = (
        "🏛️ **Welcome to Marbitz Battlebot!** ⚔️\n\n"
        "Ready to battle for marble supremacy? Here's how to play:\n\n"
        "**Commands:**\n"
        "• `/challenge @username` - Challenge someone to battle\n"
        "• `/status` - Check your active challenge status\n"
        "• `/leaderboard` - View overall rankings\n"
        "• `/weekly` - View weekly rankings\n"
        "• `/stats [@username]` - View your stats or someone else's\n"
        "• `/my_stats` - View your personal stats\n"
        "• `/cancel_challenge` - Cancel your active challenge\n\n"
        "May the best marble warrior win! 🏆"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = (
        "🏛️ **Marbitz Battlebot Commands** ⚔️\n\n"
        "• `/challenge @username` - Challenge someone to battle\n"
        "• `/status` - Check your active challenge status\n"
        "• `/leaderboard` - View overall rankings\n"
        "• `/weekly` - View weekly rankings\n"
        "• `/stats [@username]` - View your stats or someone else's\n"
        "• `/my_stats` - View your personal stats\n"
        "• `/cancel_challenge` - Cancel your active challenge\n"
        "• `/help` - Show this help message\n\n"
        "**How to Battle:**\n"
        "1. Challenge someone with `/challenge @username`\n"
        "2. Choose whether to wager marbles\n"
        "3. The challenged user must accept or decline\n"
        "4. Watch the battle unfold!\n\n"
        "**Challenge Expiration:**\n"
        "- Challenges expire after 6 hours if not accepted\n"
        "- Use `/status` to check remaining time\n"
        "- You'll receive a notification when your challenge is about to expire\n\n"
        "**Leaderboards:**\n"
        "- Overall leaderboard tracks all-time performance\n"
        "- Weekly leaderboard resets every Monday\n\n"
        "Need more help? Contact @ikbenFranco"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def challenge_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /challenge command (simplified version without conversation handler)."""
    logger.info(f"Challenge command received from user: {update.effective_user.username if update.effective_user else 'Unknown'}")
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
        
        # Check if user is challenging themselves (temporarily allow for testing)
        debug_mode = os.getenv('DEBUG_MODE', 'true').lower() == 'true'  # Default to true for testing
        logger.info(f"DEBUG: debug_mode={debug_mode}, challenger={challenger}, challenged_input={challenged_input}")
        
        if challenged_input.lower() == challenger.lower():
            if debug_mode:
                logger.info(f"DEBUG MODE: Allowing self-challenge from @{challenger}")
                await update.message.reply_text("🐛 DEBUG MODE: Self-challenge allowed for testing!")
            else:
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
        
        # Create a new challenge with no wager (simplified)
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
        logger.error(f"Unhandled exception in challenge_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ An error occurred while processing your command. Please try again later."
        )

async def wager_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle wager decision callback."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data.split("_", 2)
    if len(callback_data) < 3:
        logger.error(f"Invalid callback data format: {query.data}")
        await query.edit_message_text("An error occurred. Please try again.")
        return ConversationHandler.END
    
    action, challenge_id = callback_data[1], callback_data[2]
    
    if action == "yes":
        await query.edit_message_text(
            "💰 How many marbles do you want to wager?\n"
            "Type a number (e.g., 10) or type 'cancel' to cancel the challenge."
        )
        return WAGER_AMOUNT
    else:
        # No wager, proceed directly to challenge confirmation
        challenge_data = get_challenge(challenge_id)
        if not challenge_data:
            await query.edit_message_text("This challenge is no longer active.")
            return ConversationHandler.END
            
        challenger = challenge_data['challenger_user']
        challenged = challenge_data['challenged_user']
        
        # Update challenge with zero wager
        update_challenge(challenge_id, {'wager_amount': 0})
        
        keyboard = [
            [InlineKeyboardButton("Accept Battle! ⚔️", callback_data=f"accept_{challenge_id}")],
            [InlineKeyboardButton("Decline 😔", callback_data=f"decline_{challenge_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⚔️ @{challenger} challenges @{challenged} to a marble battle!\n\n"
            f"@{challenged}, do you accept this challenge?",
            reply_markup=reply_markup
        )
        
        return CHALLENGE_CONFIRMATION

async def wager_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle wager amount input."""
    try:
        # Validate message exists and has text
        if not update.message or not update.message.text:
            await update.effective_chat.send_message(
                "⚠️ Invalid input. Please enter a number or type 'cancel' to cancel the challenge."
            )
            return WAGER_AMOUNT
            
        # Get and sanitize text input
        text = update.message.text.strip().lower()
        
        # Handle cancellation
        if text in ['cancel', 'quit', 'exit', 'stop']:
            try:
                if 'challenge_id' in context.user_data:
                    challenge_id = context.user_data['challenge_id']
                    if remove_challenge(challenge_id):
                        logger.info(f"Challenge {challenge_id} cancelled by user")
                    else:
                        logger.warning(f"Failed to remove challenge {challenge_id} during cancellation")
                context.user_data.clear()
                await update.message.reply_text("✅ Challenge cancelled! 😔")
            except Exception as e:
                logger.error(f"Error cancelling challenge: {str(e)}")
                await update.message.reply_text("✅ Challenge cancelled, but there was an error in cleanup.")
            return ConversationHandler.END
        
        # Validate wager amount
        try:
            # Check if input is a valid number
            if not text.isdigit() and not (text.startswith('-') and text[1:].isdigit()):
                await update.message.reply_text(
                    "⚠️ Please enter a valid number for the wager!\n\n"
                    "Example: 50"
                )
                return WAGER_AMOUNT
                
            wager_amount = int(text)
            
            # Check if wager is positive
            if wager_amount <= 0:
                await update.message.reply_text(
                    "⚠️ Please enter a positive number for the wager!\n\n"
                    "Example: 50"
                )
                return WAGER_AMOUNT
                
            # Check if wager is within limits
            MAX_WAGER = 1000  # Maximum wager limit
            if wager_amount > MAX_WAGER:
                await update.message.reply_text(
                    f"⚠️ Maximum wager is {MAX_WAGER} marbles!\n\n"
                    f"Please enter a number between 1 and {MAX_WAGER}."
                )
                return WAGER_AMOUNT
                
        except ValueError:
            await update.message.reply_text(
                "⚠️ Please enter a valid number for the wager!\n\n"
                "Example: 50"
            )
            return WAGER_AMOUNT
        
        # Validate challenge exists
        challenge_id = context.user_data.get('challenge_id')
        if not challenge_id:
            logger.error("Challenge ID not found in user_data during wager input")
            await update.message.reply_text(
                "⚠️ Challenge not found. Please create a new challenge with /challenge @username."
            )
            return ConversationHandler.END
        
        # Get challenge data
        challenge_data = get_challenge(challenge_id)
        if not challenge_data:
            logger.warning(f"Challenge {challenge_id} not found during wager input")
            await update.message.reply_text(
                "⚠️ This challenge is no longer active. Please create a new challenge with /challenge @username."
            )
            context.user_data.clear()  # Clean up user data
            return ConversationHandler.END
            
        # Extract usernames
        challenger = challenge_data.get('challenger_user', 'Unknown')
        challenged = challenge_data.get('challenged_user', 'Unknown')
        
        # Validate usernames
        if not challenger or not challenged:
            logger.error(f"Invalid usernames in challenge {challenge_id}: {challenger} vs {challenged}")
            await update.message.reply_text(
                "⚠️ Invalid challenge data. Please create a new challenge."
            )
            remove_challenge(challenge_id)  # Remove invalid challenge
            context.user_data.clear()
            return ConversationHandler.END
        
        # Update challenge with wager amount
        try:
            if not update_challenge(challenge_id, {'wager_amount': wager_amount}):
                logger.error(f"Failed to update challenge {challenge_id} with wager amount {wager_amount}")
                await update.message.reply_text(
                    "⚠️ Failed to update challenge with wager amount. Please try again."
                )
                return WAGER_AMOUNT
            
            logger.info(f"Challenge {challenge_id} updated with wager amount: {wager_amount}")
        except Exception as e:
            logger.error(f"Error updating challenge {challenge_id} with wager: {str(e)}")
            await update.message.reply_text(
                "⚠️ An error occurred while setting the wager amount. Please try again."
            )
            return WAGER_AMOUNT
        
        keyboard = [
            [InlineKeyboardButton("Accept Battle! ⚔️", callback_data=f"accept_{challenge_id}")],
            [InlineKeyboardButton("Decline 😔", callback_data=f"decline_{challenge_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        wager_text = f" with {wager_amount} marbles on the line" if wager_amount > 0 else ""
        
        await update.message.reply_text(
            f"⚔️ @{challenger} challenges @{challenged} to a marble battle{wager_text}!\n\n"
            f"@{challenged}, do you accept this challenge?",
            reply_markup=reply_markup
        )
        
        return CHALLENGE_CONFIRMATION
    except Exception as e:
        # Catch-all for any other exceptions
        logger.error(f"Unhandled exception in wager_amount_handler: {str(e)}")
        await update.message.reply_text(
            "⚠️ An error occurred while processing your wager. Please try again later."
        )
        return ConversationHandler.END

async def challenge_response_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle challenge acceptance/decline."""
    try:
        # Validate callback query
        query = update.callback_query
        if not query:
            logger.error("Received empty callback query in challenge_response_callback")
            return ConversationHandler.END
            
        await query.answer()

        # Log the callback data with more details
        logger.info(f"Challenge_response_callback: Received callback_query with data: '{query.data}'")
        logger.info(f"Challenge_response_callback: User: {query.from_user.username if query.from_user else 'Unknown'} (ID: {query.from_user.id if query.from_user else 'Unknown'})")
        logger.info(f"Challenge_response_callback: Chat: {query.message.chat.id if query.message else 'Unknown'}")

        # Parse callback data
        try:
            callback_data = query.data.split("_", 1)
            if len(callback_data) < 2:
                logger.error(f"Invalid callback data format: {query.data}")
                await query.edit_message_text("⚠️ An error occurred. Please try again with /challenge @username.")
                return ConversationHandler.END
                
            action, challenge_id = callback_data[0], callback_data[1]
            
            # Validate action
            if action not in ['accept', 'decline']:
                logger.error(f"Invalid action in callback data: {action}")
                await query.edit_message_text("⚠️ Invalid action. Please try again with /challenge @username.")
                return ConversationHandler.END
                
            logger.info(f"Challenge_response_callback: Action: '{action}', Extracted Challenge ID: '{challenge_id}'")
        except Exception as e:
            logger.error(f"Error parsing callback data: {str(e)}")
            await query.edit_message_text("⚠️ An error occurred processing your response. Please try again.")
            return ConversationHandler.END

        # Get challenge data
        try:
            challenge_data = get_challenge(challenge_id)
            if not challenge_data:
                logger.warning(f"Challenge_response_callback: Challenge ID '{challenge_id}' not found")
                await query.edit_message_text(
                    "⚠️ This challenge is no longer active or has expired.\n\n"
                    "Please create a new challenge with /challenge @username."
                )
                return ConversationHandler.END
                
            # Validate challenge data structure
            required_fields = ['challenger_user', 'challenged_user', 'wager_amount']
            for field in required_fields:
                if field not in challenge_data:
                    logger.error(f"Challenge {challenge_id} missing required field: {field}")
                    await query.edit_message_text(
                        "⚠️ Invalid challenge data. Please create a new challenge with /challenge @username."
                    )
                    remove_challenge(challenge_id)  # Remove invalid challenge
                    return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error retrieving challenge data: {str(e)}")
            await query.edit_message_text("⚠️ An error occurred retrieving challenge data. Please try again.")
            return ConversationHandler.END
        
        # Extract and validate challenged username
        challenged_user_stored_username = challenge_data['challenged_user']
        if not challenged_user_stored_username:
            logger.error(f"Empty challenged username in challenge {challenge_id}")
            await query.edit_message_text("⚠️ Invalid challenge data (missing challenged username). Please try again.")
            remove_challenge(challenge_id)  # Remove invalid challenge
            return ConversationHandler.END

        # Get user information
        user_clicking_callback = query.from_user
        if not user_clicking_callback:
            logger.error("Missing user information in callback query")
            await query.edit_message_text("⚠️ Could not identify user. Please try again.")
            return ConversationHandler.END
            
        clicker_actual_username = user_clicking_callback.username  # This can be None
        clicker_id = user_clicking_callback.id
        clicker_display_name = user_clicking_callback.username or user_clicking_callback.first_name or "Unknown User"

        logger.info(
            f"Challenge_response_callback: Clicker details - "
            f"Username: @{clicker_actual_username}, DisplayName: @{clicker_display_name}, "
            f"ID: {clicker_id}. Expected challenged username: @{challenged_user_stored_username}"
        )

        # Verify user authorization (allow bypass in debug mode)
        debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        can_respond = False
        
        if debug_mode:
            can_respond = True
            logger.info(f"Challenge_response_callback: DEBUG MODE - Allowing response from @{clicker_actual_username}")
        elif clicker_actual_username:  # Only if the clicker HAS a Telegram username
            # Normalize usernames for comparison (remove @ prefix and convert to lowercase)
            normalized_clicker = clicker_actual_username.lower().lstrip('@')
            normalized_challenged = challenged_user_stored_username.lower().lstrip('@')
            
            if normalized_clicker == normalized_challenged:
                can_respond = True
                logger.info(
                    f"Challenge_response_callback: Username match successful for "
                    f"@{clicker_actual_username} against stored @{challenged_user_stored_username}."
                )
            else:
                logger.warning(
                    f"Challenge_response_callback: Username mismatch. "
                    f"Clicker: @{clicker_actual_username} (normalized: {normalized_clicker}), "
                    f"Expected: @{challenged_user_stored_username} (normalized: {normalized_challenged})"
                )
        else:
            logger.warning(
                f"Challenge_response_callback: User @{clicker_display_name} (ID: {clicker_id}) "
                f"who clicked the button has NO Telegram username set. "
                f"Cannot verify against stored challenged username @{challenged_user_stored_username}."
            )
        
        # Handle unauthorized response
        if not can_respond:
            logger.warning(
                f"Challenge_response_callback: Unauthorized attempt to respond to challenge. "
                f"Challenge ID: {challenge_id}. Expected: @{challenged_user_stored_username}. "
                f"Clicked by: @{clicker_actual_username if clicker_actual_username else '[No Username]'} (ID: {clicker_id})."
            )

            try:
                # Send a new message instead of editing
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=(
                        f"⚠️ Sorry @{clicker_display_name}, only @{challenged_user_stored_username} "
                        f"(the one who was challenged) can accept or decline this battle."
                    )
                )
            except Exception as e:
                logger.error(f"Challenge_response_callback: Error sending 'unauthorized' message: {str(e)}")

            # Keep the conversation open for the correct user to respond
            return CHALLENGE_CONFIRMATION
            
    except Exception as e:
        # Catch-all for any other exceptions
        logger.error(f"Unhandled exception in challenge_response_callback: {str(e)}")
        try:
            await query.edit_message_text("⚠️ An unexpected error occurred. Please try again later.")
        except:
            pass  # Ignore errors in the error handler
        return ConversationHandler.END
    
    # User is authorized to respond
    responding_user_name = user_clicking_callback.username or user_clicking_callback.first_name or "Unknown User"
    user_id = user_clicking_callback.id
    logger.info(
        f"User @{responding_user_name} (ID: {user_id}) is responding to challenge ID {challenge_id} for @{challenged_user_stored_username}."
    )
    
    if action == 'accept':
        try:
            # Extract challenge data
            challenger = challenge_data['challenger_user']
            challenged = challenge_data['challenged_user']
            wager_amount = challenge_data.get('wager_amount', 0)
            
            # Validate usernames
            if not challenger or not challenged:
                logger.error(f"Invalid usernames in challenge {challenge_id}: {challenger} vs {challenged}")
                await query.edit_message_text(
                    "⚠️ Invalid challenge data. Please create a new challenge with /challenge @username."
                )
                remove_challenge(challenge_id)
                return ConversationHandler.END
            
            # Ensure wager amount is valid
            try:
                wager_amount = int(wager_amount)
                if wager_amount < 0:
                    logger.warning(f"Negative wager amount ({wager_amount}) in challenge {challenge_id}, setting to 0")
                    wager_amount = 0
            except (ValueError, TypeError):
                logger.warning(f"Invalid wager amount ({wager_amount}) in challenge {challenge_id}, setting to 0")
                wager_amount = 0
            
            # Remove from active challenges
            if not remove_challenge(challenge_id):
                logger.warning(f"Failed to remove challenge {challenge_id} after acceptance")
            
            # Clear user_data
            if context.user_data:
                context.user_data.clear()
            
            # Generate battle story
            try:
                story = generate_battle_story(challenger, challenged)
                
                # Validate story structure
                if not isinstance(story, dict) or 'setup' not in story or 'phases' not in story:
                    logger.error(f"Invalid battle story structure: {story}")
                    story = {
                        "setup": f"⚔️ @{challenger} and @{challenged} face off in an epic battle!",
                        "phases": [
                            f"@{challenger} attacks!",
                            f"@{challenged} defends!",
                            f"The battle rages on!"
                        ]
                    }
            except Exception as e:
                logger.error(f"Error generating battle story: {str(e)}")
                story = {
                    "setup": f"⚔️ @{challenger} and @{challenged} face off in an epic battle!",
                    "phases": [
                        f"@{challenger} attacks!",
                        f"@{challenged} defends!",
                        f"The battle rages on!"
                    ]
                }
            
            # Start the battle sequence
            try:
                await query.edit_message_text(story["setup"])
            except Exception as e:
                logger.error(f"Error editing message with battle setup: {str(e)}")
                # Try sending a new message if editing fails
                try:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=story["setup"]
                    )
                except Exception as e2:
                    logger.error(f"Error sending battle setup message: {str(e2)}")
            
            # Add dramatic pauses between phases
            for phase in story["phases"]:
                try:
                    await asyncio.sleep(random.uniform(1.5, 3))  # Slightly shorter pauses for better UX
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=phase,
                        reply_to_message_id=query.message.message_id
                    )
                except Exception as e:
                    logger.error(f"Error sending battle phase message: {str(e)}")
                    # Continue with the battle even if one phase fails
            
            # Final pause before revealing winner
            await asyncio.sleep(random.uniform(2, 4))
            
            # Determine winner
            try:
                winner, loser = determine_winner(challenger, challenged)
            except Exception as e:
                logger.error(f"Error determining winner: {str(e)}")
                # Fallback to random selection if determine_winner fails
                winner = random.choice([challenger, challenged])
                loser = challenged if winner == challenger else challenger
            
            # Update leaderboards
            try:
                update_leaderboard(winner, loser, wager_amount)
                logger.info(f"Leaderboard updated: {winner} (W) vs {loser} (L) with {wager_amount} marbles")
            except Exception as e:
                logger.error(f"Error updating leaderboard: {str(e)}")
            
            # Victory message
            victory_text = f"🏆 **VICTORY!** @{winner} emerges triumphant!"
            if wager_amount > 0:
                victory_text += f"\n💰 @{winner} wins {wager_amount} marbles from @{loser}!"
                
        except Exception as e:
            logger.error(f"Unexpected error in challenge acceptance: {str(e)}")
            await query.edit_message_text(
                "⚠️ An error occurred while processing the battle. Please try again with /challenge @username."
            )
            return ConversationHandler.END
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=victory_text,
            reply_to_message_id=query.message.message_id,
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    else:  # action == 'decline'
        try:
            # Extract challenge data
            challenger = challenge_data.get('challenger_user', 'Unknown')
            challenged = challenge_data.get('challenged_user', 'Unknown')
            
            # Validate usernames
            if not challenger or not challenged:
                logger.error(f"Invalid usernames in challenge {challenge_id}: {challenger} vs {challenged}")
                await query.edit_message_text(
                    "⚠️ Invalid challenge data. The challenge has been cancelled."
                )
                remove_challenge(challenge_id)
                return ConversationHandler.END
            
            # Remove from active challenges
            if not remove_challenge(challenge_id):
                logger.warning(f"Failed to remove challenge {challenge_id} after decline")
            
            # Clear user_data
            if context.user_data:
                context.user_data.clear()
            
            # Ensure usernames have @ prefix for display
            if not challenger.startswith('@'):
                challenger = f"@{challenger}"
            if not challenged.startswith('@'):
                challenged = f"@{challenged}"
            
            # Send decline message
            try:
                await query.edit_message_text(
                    f"😔 {challenged} has declined the challenge from {challenger}.\n"
                    f"Maybe next time! 🏛️"
                )
            except Exception as e:
                logger.error(f"Error editing message after decline: {str(e)}")
                # Try sending a new message if editing fails
                try:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=f"😔 {challenged} has declined the challenge from {challenger}.\n"
                             f"Maybe next time! 🏛️"
                    )
                except Exception as e2:
                    logger.error(f"Error sending decline message: {str(e2)}")
            
            logger.info(f"Challenge {challenge_id} declined: {challenged} declined {challenger}'s challenge")
            
        except Exception as e:
            logger.error(f"Unexpected error in challenge decline: {str(e)}")
            try:
                await query.edit_message_text(
                    "⚠️ An error occurred while processing the decline. The challenge has been cancelled."
                )
            except:
                pass  # Ignore errors in the error handler
            
        return ConversationHandler.END

async def cancel_challenge_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel_challenge command."""
    try:
        # Validate user has a username
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        if not username:
            await update.message.reply_text(
                "⚠️ You need a username to participate in battles!\n\n"
                "Please set a username in your Telegram profile settings and try again."
            )
            return
        
        # Find user's active challenge
        try:
            user_challenge_id = find_user_challenge(username)
        except ValueError as e:
            logger.error(f"Error in find_user_challenge: {str(e)}")
            await update.message.reply_text(f"⚠️ Error: {str(e)}")
            return
        except Exception as e:
            logger.error(f"Unexpected error in find_user_challenge: {str(e)}")
            await update.message.reply_text("⚠️ An error occurred while looking for your challenges. Please try again.")
            return
        
        if not user_challenge_id:
            await update.message.reply_text(
                "ℹ️ You don't have any active challenges to cancel.\n\n"
                "You can create a new challenge with /challenge @username."
            )
            return
        
        # Get challenge data
        try:
            challenge_data = get_challenge(user_challenge_id)
            if not challenge_data:
                logger.error(f"Challenge {user_challenge_id} not found for user {username}")
                await update.message.reply_text(
                    "⚠️ Error retrieving challenge data. The challenge may have expired or been removed."
                )
                return
                
            # Validate challenge data
            if 'challenged_user' not in challenge_data:
                logger.error(f"Invalid challenge data for {user_challenge_id}: missing challenged_user")
                await update.message.reply_text("⚠️ Invalid challenge data. The challenge has been removed.")
                remove_challenge(user_challenge_id)
                return
                
            challenged_user = challenge_data['challenged_user']
            
            # Remove the challenge
            if remove_challenge(user_challenge_id):
                logger.info(f"Challenge {user_challenge_id} cancelled by user {username}")
                
                # Clear user_data if it belongs to this user
                if context.user_data.get('challenger_id') == user_id:
                    context.user_data.clear()
                
                # Ensure usernames have @ prefix for display
                display_username = username
                display_challenged = challenged_user
                if not display_username.startswith('@'):
                    display_username = f"@{display_username}"
                if not display_challenged.startswith('@'):
                    display_challenged = f"@{display_challenged}"
                
                await update.message.reply_text(
                    f"❌ {display_username} has cancelled their challenge against {display_challenged}."
                )
            else:
                logger.warning(f"Failed to remove challenge {user_challenge_id} for user {username}")
                await update.message.reply_text(
                    "⚠️ Failed to cancel the challenge. Please try again or contact support."
                )
        except Exception as e:
            logger.error(f"Error processing challenge cancellation for {username}: {str(e)}")
            await update.message.reply_text(
                "⚠️ An error occurred while cancelling your challenge. Please try again."
            )
    except Exception as e:
        # Catch-all for any other exceptions
        logger.error(f"Unhandled exception in cancel_challenge_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ An unexpected error occurred. Please try again later."
        )

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /leaderboard command."""
    try:
        # Load the leaderboard data
        try:
            overall = load_leaderboard(OVERALL_LEADERBOARD_FILE)
            if overall is None:
                logger.error("load_leaderboard returned None for overall leaderboard")
                overall = {}
        except Exception as e:
            logger.error(f"Error loading overall leaderboard: {str(e)}")
            await update.message.reply_text(
                "⚠️ An error occurred while loading the leaderboard. Please try again later."
            )
            return
        
        # Format the leaderboard
        try:
            text = format_leaderboard(overall, "🏆 Overall Leaderboard")
        except Exception as e:
            logger.error(f"Error formatting leaderboard: {str(e)}")
            await update.message.reply_text(
                "⚠️ An error occurred while formatting the leaderboard. Please try again later."
            )
            return
        
        # Send the leaderboard
        try:
            await update.message.reply_text(text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error sending leaderboard message: {str(e)}")
            # Try without Markdown if that might be the issue
            try:
                await update.message.reply_text(
                    "⚠️ Error displaying formatted leaderboard. Here's a simple version:\n\n" + 
                    text.replace('*', '').replace('_', '')
                )
            except Exception as e2:
                logger.error(f"Error sending plain leaderboard message: {str(e2)}")
                await update.message.reply_text(
                    "⚠️ An error occurred while sending the leaderboard. Please try again later."
                )
    except Exception as e:
        # Catch-all for any other exceptions
        logger.error(f"Unhandled exception in leaderboard_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ An unexpected error occurred. Please try again later."
        )

async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /weekly command."""
    try:
        # Load the weekly leaderboard data
        try:
            weekly = load_leaderboard(WEEKLY_LEADERBOARD_FILE)
            if weekly is None:
                logger.error("load_leaderboard returned None for weekly leaderboard")
                weekly = {}
        except Exception as e:
            logger.error(f"Error loading weekly leaderboard: {str(e)}")
            await update.message.reply_text(
                "⚠️ An error occurred while loading the weekly leaderboard. Please try again later."
            )
            return
        
        # Format the leaderboard
        try:
            text = format_leaderboard(weekly, "📅 Weekly Leaderboard")
        except Exception as e:
            logger.error(f"Error formatting weekly leaderboard: {str(e)}")
            await update.message.reply_text(
                "⚠️ An error occurred while formatting the weekly leaderboard. Please try again later."
            )
            return
        
        # Send the leaderboard
        try:
            await update.message.reply_text(text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error sending weekly leaderboard message: {str(e)}")
            # Try without Markdown if that might be the issue
            try:
                await update.message.reply_text(
                    "⚠️ Error displaying formatted weekly leaderboard. Here's a simple version:\n\n" + 
                    text.replace('*', '').replace('_', '')
                )
            except Exception as e2:
                logger.error(f"Error sending plain weekly leaderboard message: {str(e2)}")
                await update.message.reply_text(
                    "⚠️ An error occurred while sending the weekly leaderboard. Please try again later."
                )
    except Exception as e:
        # Catch-all for any other exceptions
        logger.error(f"Unhandled exception in weekly_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ An unexpected error occurred. Please try again later."
        )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command."""
    try:
        # Parse target username
        try:
            if context.args and context.args[0].startswith('@'):
                target_user = context.args[0][1:]  # Remove @
            elif context.args:
                target_user = context.args[0]
            else:
                target_user = update.effective_user.username
            
            # Validate username
            if not target_user:
                await update.message.reply_text(
                    "⚠️ Please specify a username or make sure you have a username set!\n\n"
                    "Usage: /stats @username or /stats username"
                )
                return
                
            # Sanitize username
            target_user = target_user.strip()
        except Exception as e:
            logger.error(f"Error parsing username in stats_command: {str(e)}")
            await update.message.reply_text(
                "⚠️ Error parsing username. Please use the format: /stats @username"
            )
            return
        
        # Get user stats
        try:
            overall_stats, weekly_stats = get_user_stats(target_user)
            
            # Validate stats structure
            required_fields = ['wins', 'losses', 'marbles']
            for field in required_fields:
                if field not in overall_stats or field not in weekly_stats:
                    logger.error(f"Missing field {field} in stats for user {target_user}")
                    await update.message.reply_text(
                        f"⚠️ Error retrieving complete stats for user @{target_user}. Please try again."
                    )
                    return
        except Exception as e:
            logger.error(f"Error getting stats for user {target_user}: {str(e)}")
            await update.message.reply_text(
                f"⚠️ Error retrieving stats for user @{target_user}. Please try again."
            )
            return
        
        # Calculate totals and win rates
        try:
            overall_total = overall_stats['wins'] + overall_stats['losses']
            weekly_total = weekly_stats['wins'] + weekly_stats['losses']
            
            overall_winrate = (overall_stats['wins'] / overall_total * 100) if overall_total > 0 else 0
            weekly_winrate = (weekly_stats['wins'] / weekly_total * 100) if weekly_total > 0 else 0
        except Exception as e:
            logger.error(f"Error calculating win rates for user {target_user}: {str(e)}")
            await update.message.reply_text(
                f"⚠️ Error calculating statistics for user @{target_user}. Please try again."
            )
            return
        
        # Format stats text
        try:
            # Ensure username has @ prefix for display
            display_username = target_user
            if not display_username.startswith('@'):
                display_username = f"@{display_username}"
                
            stats_text = f"📊 **Stats for {display_username}**\n\n"
            stats_text += f"**Overall:**\n"
            stats_text += f"• Battles: {overall_total} ({overall_stats['wins']}W-{overall_stats['losses']}L)\n"
            stats_text += f"• Win Rate: {overall_winrate:.1f}%\n"
            stats_text += f"• Marbles: {overall_stats['marbles']:+d}\n\n"
            stats_text += f"**This Week:**\n"
            stats_text += f"• Battles: {weekly_total} ({weekly_stats['wins']}W-{weekly_stats['losses']}L)\n"
            stats_text += f"• Win Rate: {weekly_winrate:.1f}%\n"
            stats_text += f"• Marbles: {weekly_stats['marbles']:+d}"
        except Exception as e:
            logger.error(f"Error formatting stats for user {target_user}: {str(e)}")
            await update.message.reply_text(
                f"⚠️ Error formatting statistics for user @{target_user}. Please try again."
            )
            return
        
        # Send stats message
        try:
            await update.message.reply_text(stats_text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error sending stats message: {str(e)}")
            # Try without Markdown if that might be the issue
            try:
                await update.message.reply_text(
                    "⚠️ Error displaying formatted stats. Here's a simple version:\n\n" + 
                    stats_text.replace('*', '').replace('_', '')
                )
            except Exception as e2:
                logger.error(f"Error sending plain stats message: {str(e2)}")
                await update.message.reply_text(
                    f"⚠️ An error occurred while sending stats for @{target_user}. Please try again later."
                )
    except Exception as e:
        # Catch-all for any other exceptions
        logger.error(f"Unhandled exception in stats_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ An unexpected error occurred. Please try again later."
        )

async def my_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /my_stats command."""
    try:
        # Validate user has a username
        username = update.effective_user.username
        if not username:
            await update.message.reply_text(
                "⚠️ You need a username to view your stats!\n\n"
                "Please set a username in your Telegram profile settings and try again."
            )
            return
        
        # Use the stats command logic with the user's username
        try:
            context.args = [username]
            await stats_command(update, context)
        except Exception as e:
            logger.error(f"Error calling stats_command from my_stats_command: {str(e)}")
            await update.message.reply_text(
                "⚠️ An error occurred while retrieving your stats. Please try again later."
            )
    except Exception as e:
        # Catch-all for any other exceptions
        logger.error(f"Unhandled exception in my_stats_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ An unexpected error occurred. Please try again later."
        )

async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show debug information."""
    debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    webhook_url = os.getenv('WEBHOOK_URL', 'Not set')
    port = os.getenv('PORT', 'Not set')
    
    debug_info = (
        f"🐛 **Debug Information:**\n\n"
        f"• Debug Mode: `{debug_mode}`\n"
        f"• Webhook URL: `{webhook_url}`\n"
        f"• Port: `{port}`\n"
        f"• Your Username: `@{update.effective_user.username if update.effective_user.username else 'No username'}`\n"
        f"• User ID: `{update.effective_user.id if update.effective_user else 'Unknown'}`"
    )
    
    await update.message.reply_text(debug_info, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command to check challenge status and expiry time."""
    try:
        # Validate user has a username
        username = update.effective_user.username
        user_id = update.effective_user.id
        
        if not username:
            await update.message.reply_text(
                "⚠️ You need a username to check challenge status!\n\n"
                "Please set a username in your Telegram profile settings and try again."
            )
            return
        
        # Find user's active challenge
        try:
            challenge_id = find_user_challenge(username)
        except ValueError as e:
            logger.error(f"Error in find_user_challenge: {str(e)}")
            await update.message.reply_text(f"⚠️ Error: {str(e)}")
            return
        except Exception as e:
            logger.error(f"Unexpected error in find_user_challenge: {str(e)}")
            await update.message.reply_text("⚠️ An error occurred while looking for your challenges. Please try again.")
            return
        
        # If no active challenge found
        if not challenge_id:
            # Check if user is a challenged user in any active challenge
            from marbitz_battlebot.battle import get_all_challenges
            all_challenges = get_all_challenges()
            
            pending_challenges = []
            for cid, data in all_challenges.items():
                challenged = data.get('challenged_user', '')
                if challenged.lower().strip() == username.lower().strip() or (challenged.startswith('@') and challenged[1:].lower().strip() == username.lower().strip()):
                    pending_challenges.append((cid, data.get('challenger_user', 'Unknown')))
            
            if pending_challenges:
                text = "🔍 You have pending challenges from:\n\n"
                for cid, challenger in pending_challenges:
                    if not challenger.startswith('@'):
                        challenger = f"@{challenger}"
                    text += f"• {challenger} - Use /challenge @{username} to respond\n"
                await update.message.reply_text(text)
            else:
                await update.message.reply_text(
                    "ℹ️ You don't have any active challenges.\n\n"
                    "You can create a new challenge with /challenge @username."
                )
            return
        
        # Get challenge status with expiry information
        try:
            status = get_challenge_status(challenge_id, expiry_hours=6)
        except ValueError as e:
            logger.error(f"Error in get_challenge_status: {str(e)}")
            await update.message.reply_text(f"⚠️ Error: {str(e)}")
            return
        except Exception as e:
            logger.error(f"Unexpected error in get_challenge_status: {str(e)}")
            await update.message.reply_text("⚠️ An error occurred while retrieving challenge status. Please try again.")
            return
        
        # Format challenger and challenged usernames
        challenger = status['challenger']
        challenged = status['challenged']
        if not challenger.startswith('@'):
            challenger = f"@{challenger}"
        if not challenged.startswith('@'):
            challenged = f"@{challenged}"
        
        # Create status message
        status_text = f"🔍 **Challenge Status**\n\n"
        status_text += f"• Challenger: {challenger}\n"
        status_text += f"• Challenged: {challenged}\n"
        
        if status['wager_amount'] > 0:
            status_text += f"• Wager: {status['wager_amount']} marbles\n"
        
        status_text += f"• Status: {status['status'].capitalize()}\n"
        status_text += f"• Created: {status['created_at']}\n"
        
        # Add expiry information
        if status['expired']:
            status_text += f"• Expiry: **EXPIRED**\n"
            status_text += "\n⚠️ This challenge has expired and will be automatically removed soon."
        else:
            status_text += f"• Expires: {status['expires_at']}\n"
            status_text += f"• Time left: {status['time_remaining']}\n"
            
            # Add progress bar for expiry
            progress = status['expiry_percentage']
            bar_length = 10
            filled_length = int(bar_length * progress // 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            status_text += f"\n`[{bar}]` {progress}% expired\n"
            
            if progress >= 75:
                status_text += "\n⚠️ This challenge will expire soon! Respond quickly."
        
        # Add action buttons
        keyboard = []
        if status['status'] == 'pending':
            # Add cancel button for challenger
            keyboard.append([InlineKeyboardButton("❌ Cancel Challenge", callback_data=f"cancel_{challenge_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        # Send status message
        await update.message.reply_text(status_text, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        # Catch-all for any other exceptions
        logger.error(f"Unhandled exception in status_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ An unexpected error occurred. Please try again later."
        )

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation."""
    try:
        # If there's an active challenge in user_data, remove it
        if context.user_data and 'challenge_id' in context.user_data:
            challenge_id = context.user_data['challenge_id']
            try:
                if remove_challenge(challenge_id):
                    logger.info(f"Challenge {challenge_id} removed during conversation cancellation")
                else:
                    logger.warning(f"Failed to remove challenge {challenge_id} during conversation cancellation")
            except Exception as e:
                logger.error(f"Error removing challenge during conversation cancellation: {str(e)}")
        
        # Clear user data
        try:
            if context.user_data:
                context.user_data.clear()
        except Exception as e:
            logger.error(f"Error clearing user_data during conversation cancellation: {str(e)}")
        
        # Send confirmation message
        try:
            await update.message.reply_text("✅ Operation cancelled!")
        except Exception as e:
            logger.error(f"Error sending cancellation confirmation: {str(e)}")
            
        return ConversationHandler.END
    except Exception as e:
        # Catch-all for any other exceptions
        logger.error(f"Unhandled exception in cancel_conversation: {str(e)}")
        try:
            await update.message.reply_text("✅ Operation cancelled, but there was an error in cleanup.")
        except:
            pass  # Ignore errors in the error handler
        return ConversationHandler.END

async def debug_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Debug handler to catch all callback queries."""
    query = update.callback_query
    if query:
        logger.info(f"DEBUG: Callback query received - Data: '{query.data}', User: {query.from_user.username if query.from_user else 'Unknown'}")
        # Don't answer the query here, let other handlers process it

async def cancel_challenge_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cancel challenge callback from status command."""
    query = update.callback_query
    
    try:
        await query.answer()
        
        # Extract challenge ID from callback data
        try:
            callback_data = query.data.split("_", 1)
            if len(callback_data) < 2 or callback_data[0] != 'cancel':
                logger.error(f"Invalid cancel callback data format: {query.data}")
                await query.edit_message_text("⚠️ An error occurred. Please try using /cancel_challenge instead.")
                return
                
            challenge_id = callback_data[1]
            logger.info(f"Cancel_challenge_callback: Challenge ID: '{challenge_id}'")
        except Exception as e:
            logger.error(f"Error parsing cancel callback data: {str(e)}")
            await query.edit_message_text("⚠️ An error occurred processing your request. Please try again.")
            return
        
        # Get challenge data
        try:
            challenge_data = get_challenge(challenge_id)
            if not challenge_data:
                logger.warning(f"Cancel_challenge_callback: Challenge ID '{challenge_id}' not found")
                await query.edit_message_text(
                    "⚠️ This challenge is no longer active or has expired."
                )
                return
        except Exception as e:
            logger.error(f"Error retrieving challenge data for cancellation: {str(e)}")
            await query.edit_message_text("⚠️ An error occurred retrieving challenge data. Please try again.")
            return
        
        # Verify that the user is the challenger
        challenger = challenge_data.get('challenger_user', '')
        username = update.effective_user.username
        
        if not username:
            await query.edit_message_text("⚠️ You need a username to cancel challenges.")
            return
        
        # Normalize usernames for comparison
        normalized_challenger = challenger.lower().lstrip('@')
        normalized_username = username.lower()
        
        if normalized_username != normalized_challenger:
            logger.warning(f"Unauthorized cancel attempt: User {username} tried to cancel challenge created by {challenger}")
            await query.edit_message_text("⚠️ You can only cancel challenges that you created.")
            return
        
        # Remove the challenge
        try:
            if remove_challenge(challenge_id):
                # Format usernames for display
                challenger_display = challenger
                challenged_display = challenge_data.get('challenged_user', 'Unknown')
                
                if not challenger_display.startswith('@'):
                    challenger_display = f"@{challenger_display}"
                if not challenged_display.startswith('@'):
                    challenged_display = f"@{challenged_display}"
                
                await query.edit_message_text(
                    f"✅ Challenge cancelled!\n\n"
                    f"{challenger_display} has cancelled their challenge against {challenged_display}."
                )
                logger.info(f"Challenge {challenge_id} cancelled via status command by {username}")
            else:
                await query.edit_message_text("⚠️ Failed to cancel the challenge. Please try again or use /cancel_challenge.")
                logger.error(f"Failed to remove challenge {challenge_id} via cancel callback")
        except Exception as e:
            logger.error(f"Error cancelling challenge {challenge_id}: {str(e)}")
            await query.edit_message_text("⚠️ An error occurred while cancelling the challenge. Please try again.")
    except Exception as e:
        logger.error(f"Unhandled exception in cancel_challenge_callback: {str(e)}")
        try:
            await query.edit_message_text("⚠️ An unexpected error occurred. Please try again later.")
        except:
            pass  # Ignore errors in the error handler