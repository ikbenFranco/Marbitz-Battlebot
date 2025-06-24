"""
Handlers module for Marbitz Battlebot.

This module contains the command handlers for the Telegram bot.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from marbitz_battlebot.battle import (
    create_challenge, get_challenge, update_challenge, remove_challenge, 
    find_user_challenge, generate_battle_story, determine_winner
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
    welcome_text = (
        "🏛️ **Welcome to Marbitz Battlebot!** ⚔️\n\n"
        "Ready to battle for marble supremacy? Here's how to play:\n\n"
        "**Commands:**\n"
        "• `/challenge @username` - Challenge someone to battle\n"
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
        "**Leaderboards:**\n"
        "- Overall leaderboard tracks all-time performance\n"
        "- Weekly leaderboard resets every Monday\n\n"
        "Need more help? Contact @ikbenFranco"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def challenge_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /challenge command."""
    if not context.args:
        await update.message.reply_text("Usage: /challenge @username")
        return ConversationHandler.END
    
    challenger = update.effective_user.username
    if not challenger:
        await update.message.reply_text("You need a username to participate in battles!")
        return ConversationHandler.END
    
    challenged_input = context.args[0].lstrip('@')
    
    if challenged_input.lower() == challenger.lower():
        await update.message.reply_text("You can't challenge yourself! 😅")
        return ConversationHandler.END
    
    # Create a new challenge
    challenge_id = create_challenge(challenger, challenged_input)
    
    # Store challenge data in user_data
    context.user_data['challenge_id'] = challenge_id
    context.user_data['challenger'] = challenger
    context.user_data['challenged'] = challenged_input
    context.user_data['challenger_id'] = update.effective_user.id
    
    # Ask about wagering
    keyboard = [
        [InlineKeyboardButton("Yes, let's wager!", callback_data=f"wager_yes_{challenge_id}")],
        [InlineKeyboardButton("No wager, just battle!", callback_data=f"wager_no_{challenge_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚔️ @{challenger} wants to challenge @{challenged_input}!\n\n"
        f"Do you want to wager marbles on this battle?",
        reply_markup=reply_markup
    )
    
    return WAGER_AMOUNT

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
    if not update.message or not update.message.text:
        await update.effective_chat.send_message("Invalid input. Please enter a number or 'cancel'.")
        return WAGER_AMOUNT
        
    text = update.message.text.strip().lower()
    
    if text == 'cancel':
        if 'challenge_id' in context.user_data:
            remove_challenge(context.user_data['challenge_id'])
        context.user_data.clear()
        await update.message.reply_text("Challenge cancelled! 😔")
        return ConversationHandler.END
    
    try:
        wager_amount = int(text)
        if wager_amount <= 0:
            await update.message.reply_text("Please enter a positive number for the wager!")
            return WAGER_AMOUNT
        if wager_amount > 1000:  # Example maximum wager limit
            await update.message.reply_text("Maximum wager is 1000 marbles!")
            return WAGER_AMOUNT
    except ValueError:
        await update.message.reply_text("Please enter a valid number!")
        return WAGER_AMOUNT
    
    challenge_id = context.user_data.get('challenge_id')
    if not challenge_id:
        await update.message.reply_text("Challenge not found. Please try again.")
        return ConversationHandler.END
    
    challenge_data = get_challenge(challenge_id)
    if not challenge_data:
        await update.message.reply_text("This challenge is no longer active.")
        return ConversationHandler.END
        
    challenger = challenge_data['challenger_user']
    challenged = challenge_data['challenged_user']
    
    # Update challenge with wager amount
    challenge_data['wager_amount'] = wager_amount
    
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

async def challenge_response_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle challenge acceptance/decline."""
    query = update.callback_query
    await query.answer()

    logger.info(f"Challenge_response_callback: Received callback_query with data: '{query.data}'")

    callback_data = query.data.split("_", 1)
    if len(callback_data) < 2:
        logger.error(f"Invalid callback data format: {query.data}")
        await query.edit_message_text("An error occurred. Please try again.")
        return ConversationHandler.END
        
    action, challenge_id = callback_data[0], callback_data[1]
    logger.info(f"Challenge_response_callback: Action: '{action}', Extracted Challenge ID: '{challenge_id}'")

    challenge_data = get_challenge(challenge_id)
    if not challenge_data:
        logger.warning(f"Challenge_response_callback: Challenge ID '{challenge_id}' not found")
        try:
            await query.edit_message_text("This challenge is no longer active or has expired.")
        except Exception as e:
            logger.error(f"Challenge_response_callback: Error editing message for expired challenge: {e}")
        return ConversationHandler.END
    
    challenged_user_stored_username = challenge_data['challenged_user'] # Username string as typed in /challenge

    user_clicking_callback = query.from_user
    clicker_actual_username = user_clicking_callback.username # This can be None
    clicker_id = user_clicking_callback.id
    clicker_display_name = user_clicking_callback.username or user_clicking_callback.first_name

    logger.info(f"Challenge_response_callback: Clicker details - Username: @{clicker_actual_username}, DisplayName: @{clicker_display_name}, ID: {clicker_id}. Expected challenged username: @{challenged_user_stored_username}")

    can_respond = False
    if clicker_actual_username: # Only if the clicker HAS a Telegram username
        if clicker_actual_username.lower() == challenged_user_stored_username.lower():
            can_respond = True
            logger.info(f"Challenge_response_callback: Username match successful for @{clicker_actual_username} against stored @{challenged_user_stored_username}.")
        else:
            logger.warning(f"Challenge_response_callback: Username mismatch. Clicker: @{clicker_actual_username} (lower: {clicker_actual_username.lower()}), Expected stored: @{challenged_user_stored_username} (lower: {challenged_user_stored_username.lower()})")
    else:
        logger.warning(f"Challenge_response_callback: User @{clicker_display_name} (ID: {clicker_id}) who clicked the button has NO Telegram username set. Cannot verify against stored challenged username @{challenged_user_stored_username}.")
    
    if not can_respond:
        # This log was already quite good.
        logger.warning(
            f"Challenge_response_callback: Unauthorized attempt to respond to challenge. Challenge ID: {challenge_id}. Expected stored: @{challenged_user_stored_username}. Clicked by: @{clicker_actual_username if clicker_actual_username else '[No Username]'} (ID: {clicker_id})."
        )

        try:
            # Send a new message instead of editing, as editing might fail silently or be less noticeable.
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"😕 Sorry @{clicker_display_name}, only @{challenged_user_stored_username} (the one who was challenged) can accept or decline this battle."
            )
        except Exception as e:
            logger.error(f"Challenge_response_callback: Error sending 'unauthorized' message: {e}")

        # We might not want to return to CHALLENGE_CONFIRMATION if the issue is systemic and not a one-off misclick.
        # Forcing the conversation to end might be cleaner if the user truly can't be verified.
        # However, keeping CHALLENGE_CONFIRMATION allows the buttons to remain if it was just a misclick by someone else.
        return CHALLENGE_CONFIRMATION
    
    # User is authorized to respond
    responding_user_name = user_clicking_callback.username or user_clicking_callback.first_name
    user_id = user_clicking_callback.id
    logger.info(
        f"User @{responding_user_name} (ID: {user_id}) is responding to challenge ID {challenge_id} for @{challenged_user_stored_username}."
    )
    
    if action == 'accept':
        challenger = challenge_data['challenger_user']
        challenged = challenge_data['challenged_user']
        wager_amount = challenge_data['wager_amount']
        
        # Remove from active challenges
        remove_challenge(challenge_id)
        
        # Clear user_data
        if context.user_data:
            context.user_data.clear()
        
        # Generate battle story
        story = generate_battle_story(challenger, challenged)
        
        # Start the battle sequence
        await query.edit_message_text(story["setup"])
        
        # Add dramatic pauses between phases
        for phase in story["phases"]:
            await asyncio.sleep(random.uniform(2, 4))
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=phase,
                reply_to_message_id=query.message.message_id
            )
        
        # Final pause before revealing winner
        await asyncio.sleep(random.uniform(3, 5))
        
        # Determine winner
        winner, loser = determine_winner(challenger, challenged)
        
        # Update leaderboards
        update_leaderboard(winner, loser, wager_amount)
        
        # Victory message
        victory_text = f"🏆 **VICTORY!** @{winner} emerges triumphant!"
        if wager_amount > 0:
            victory_text += f"\n💰 @{winner} wins {wager_amount} marbles from @{loser}!"
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=victory_text,
            reply_to_message_id=query.message.message_id,
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    else:  # action == 'decline'
        challenger = challenge_data['challenger_user']
        challenged = challenge_data['challenged_user']
        
        # Remove from active challenges
        remove_challenge(challenge_id)
        
        # Clear user_data
        if context.user_data:
            context.user_data.clear()
        
        await query.edit_message_text(
            f"😔 @{challenged} has declined the challenge from @{challenger}.\n"
            f"Maybe next time! 🏛️"
        )
        
        return ConversationHandler.END

async def cancel_challenge_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel_challenge command."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if not username:
        await update.message.reply_text("You need a username to participate in battles!")
        return
    
    # Find user's active challenge
    user_challenge_id = find_user_challenge(username)
    
    if user_challenge_id:
        challenge_data = get_challenge(user_challenge_id)
        if not challenge_data:
            await update.message.reply_text("Error retrieving challenge data. Please try again.")
            return
            
        challenged_user = challenge_data['challenged_user']
        remove_challenge(user_challenge_id)
        
        # Clear user_data if it belongs to this user
        if context.user_data.get('challenger_id') == user_id:
            context.user_data.clear()
        
        await update.message.reply_text(
            f"❌ @{username} has cancelled their challenge against @{challenged_user}."
        )
    else:
        await update.message.reply_text("You don't have any active challenges to cancel.")

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /leaderboard command."""
    overall = load_leaderboard(OVERALL_LEADERBOARD_FILE)
    text = format_leaderboard(overall, "🏆 Overall Leaderboard")
    await update.message.reply_text(text, parse_mode='Markdown')

async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /weekly command."""
    weekly = load_leaderboard(WEEKLY_LEADERBOARD_FILE)
    text = format_leaderboard(weekly, "📅 Weekly Leaderboard")
    await update.message.reply_text(text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command."""
    if context.args and context.args[0].startswith('@'):
        target_user = context.args[0][1:]  # Remove @
    elif context.args:
        target_user = context.args[0]
    else:
        target_user = update.effective_user.username
    
    if not target_user:
        await update.message.reply_text("Please specify a username or make sure you have a username set!")
        return
    
    overall_stats, weekly_stats = get_user_stats(target_user)
    
    overall_total = overall_stats['wins'] + overall_stats['losses']
    weekly_total = weekly_stats['wins'] + weekly_stats['losses']
    
    overall_winrate = (overall_stats['wins'] / overall_total * 100) if overall_total > 0 else 0
    weekly_winrate = (weekly_stats['wins'] / weekly_total * 100) if weekly_total > 0 else 0
    
    stats_text = f"📊 **Stats for @{target_user}**\n\n"
    stats_text += f"**Overall:**\n"
    stats_text += f"• Battles: {overall_total} ({overall_stats['wins']}W-{overall_stats['losses']}L)\n"
    stats_text += f"• Win Rate: {overall_winrate:.1f}%\n"
    stats_text += f"• Marbles: {overall_stats['marbles']:+d}\n\n"
    stats_text += f"**This Week:**\n"
    stats_text += f"• Battles: {weekly_total} ({weekly_stats['wins']}W-{weekly_stats['losses']}L)\n"
    stats_text += f"• Win Rate: {weekly_winrate:.1f}%\n"
    stats_text += f"• Marbles: {weekly_stats['marbles']:+d}"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def my_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /my_stats command."""
    username = update.effective_user.username
    if not username:
        await update.message.reply_text("You need a username to view your stats!")
        return
    
    # Use the stats command logic with the user's username
    context.args = [username]
    await stats_command(update, context)

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation."""
    # If there's an active challenge in user_data, remove it
    if 'challenge_id' in context.user_data:
        remove_challenge(context.user_data['challenge_id'])
    
    context.user_data.clear()
    await update.message.reply_text("Operation cancelled!")
    return ConversationHandler.END