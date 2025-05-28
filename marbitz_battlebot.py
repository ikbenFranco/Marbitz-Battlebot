import logging
import os
import asyncio
import json
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation handler
WAGER_AMOUNT, CHALLENGE_CONFIRMATION = range(2)

# Global variables
active_challenges = {}
challenge_counter = 0

# File paths
OVERALL_LEADERBOARD_FILE = 'overall_leaderboard.json'
WEEKLY_LEADERBOARD_FILE = 'weekly_leaderboard.json'
WEEKLY_RESET_FILE = 'weekly_reset.json'

def load_leaderboard(filename):
    """Load leaderboard from JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_leaderboard(leaderboard, filename):
    """Save leaderboard to JSON file."""
    with open(filename, 'w') as f:
        json.dump(leaderboard, f, indent=2)

def get_weekly_reset_info():
    """Get information about the weekly reset."""
    try:
        with open(WEEKLY_RESET_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default to Monday reset if no info exists
        return {'reset_day': 'Monday', 'last_reset': None}

def save_weekly_reset_info(reset_info):
    """Save weekly reset information."""
    with open(WEEKLY_RESET_FILE, 'w') as f:
        json.dump(reset_info, f, indent=2)

def should_reset_weekly_leaderboard():
    """Check if weekly leaderboard should be reset."""
    reset_info = get_weekly_reset_info()
    reset_day = reset_info.get('reset_day', 'Monday')
    last_reset = reset_info.get('last_reset')
    
    now = datetime.now()
    current_weekday = now.strftime('%A')
    
    # If it's the reset day and we haven't reset this week
    if current_weekday == reset_day:
        if last_reset is None:
            return True
        
        last_reset_date = datetime.fromisoformat(last_reset)
        # Check if the last reset was more than 6 days ago
        if (now - last_reset_date).days >= 6:
            return True
    
    return False

def reset_weekly_leaderboard():
    """Reset the weekly leaderboard."""
    if should_reset_weekly_leaderboard():
        # Clear weekly leaderboard
        save_leaderboard({}, WEEKLY_LEADERBOARD_FILE)
        
        # Update reset info
        reset_info = get_weekly_reset_info()
        reset_info['last_reset'] = datetime.now().isoformat()
        save_weekly_reset_info(reset_info)
        
        logger.info("Weekly leaderboard has been reset.")

def update_leaderboard(winner, loser, marble_change=0):
    """Update both overall and weekly leaderboards."""
    # Reset weekly leaderboard if needed
    reset_weekly_leaderboard()
    
    # Load leaderboards
    overall = load_leaderboard(OVERALL_LEADERBOARD_FILE)
    weekly = load_leaderboard(WEEKLY_LEADERBOARD_FILE)
    
    # Initialize user stats if they don't exist
    for leaderboard in [overall, weekly]:
        for user in [winner, loser]:
            if user not in leaderboard:
                leaderboard[user] = {'wins': 0, 'losses': 0, 'marbles': 0}
    
    # Update stats
    overall[winner]['wins'] += 1
    overall[loser]['losses'] += 1
    weekly[winner]['wins'] += 1
    weekly[loser]['losses'] += 1
    
    # Update marble counts
    overall[winner]['marbles'] += marble_change
    overall[loser]['marbles'] -= marble_change
    weekly[winner]['marbles'] += marble_change
    weekly[loser]['marbles'] -= marble_change
    
    # Save updated leaderboards
    save_leaderboard(overall, OVERALL_LEADERBOARD_FILE)
    save_leaderboard(weekly, WEEKLY_LEADERBOARD_FILE)

def format_leaderboard(leaderboard, title):
    """Format leaderboard for display."""
    if not leaderboard:
        return f"**{title}**\n\nNo battles yet! 🏆"
    
    # Sort by wins (descending), then by win rate
    sorted_users = sorted(
        leaderboard.items(),
        key=lambda x: (x[1]['wins'], x[1]['wins'] / max(1, x[1]['wins'] + x[1]['losses'])),
        reverse=True
    )
    
    text = f"**{title}**\n\n"
    for i, (user, stats) in enumerate(sorted_users[:10], 1):
        wins = stats['wins']
        losses = stats['losses']
        marbles = stats['marbles']
        total_battles = wins + losses
        win_rate = (wins / total_battles * 100) if total_battles > 0 else 0
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} @{user}: {wins}W-{losses}L ({win_rate:.1f}%) | {marbles:+d} marbles\n"
    
    return text

async def generate_battle_story(challenger, challenged):
    """Generate a dramatic battle story."""
    battle_scenarios = [
        {
            "setup": f"🏛️ The arena falls silent as @{challenger} and @{challenged} face off...",
            "phases": [
                f"⚔️ @{challenger} charges forward with a fierce battle cry!",
                f"🛡️ @{challenged} deflects the attack and counters!",
                f"💥 The clash echoes through the marble halls!"
            ]
        },
        {
            "setup": f"🌩️ Lightning crackles as @{challenger} challenges @{challenged} to combat!",
            "phases": [
                f"🔥 @{challenger} unleashes a flurry of marble strikes!",
                f"❄️ @{challenged} responds with an icy defensive maneuver!",
                f"⚡ The elements collide in spectacular fashion!"
            ]
        },
        {
            "setup": f"🏴‍☠️ The battleground is set as @{challenger} draws their weapon against @{challenged}!",
            "phases": [
                f"🗡️ @{challenger} spins with deadly precision!",
                f"🛡️ @{challenged} parries and launches a counterattack!",
                f"💫 Sparks fly as marble meets marble!"
            ]
        }
    ]
    
    scenario = random.choice(battle_scenarios)
    return scenario

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def challenge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /challenge command."""
    global challenge_counter
    
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
    
    challenge_counter += 1
    challenge_id = f"challenge_{challenge_counter}"
    
    # Store challenge data
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

async def wager_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wager decision callback."""
    query = update.callback_query
    await query.answer()
    
    action, challenge_id = query.data.split("_", 2)[1], query.data.split("_", 2)[2]
    
    if action == "yes":
        await query.edit_message_text(
            "💰 How many marbles do you want to wager?\n"
            "Type a number (e.g., 10) or type 'cancel' to cancel the challenge."
        )
        return WAGER_AMOUNT
    else:
        # No wager, proceed directly to challenge confirmation
        challenger = context.user_data['challenger']
        challenged = context.user_data['challenged']
        
        # Store in active challenges without wager
        active_challenges[challenge_id] = {
            'challenger_user': challenger,
            'challenged_user': challenged,
            'wager_amount': 0,
            'timestamp': datetime.now().isoformat()
        }
        
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

async def wager_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wager amount input."""
    if update.message.text.lower() == 'cancel':
        context.user_data.clear()
        await update.message.reply_text("Challenge cancelled! 😔")
        return ConversationHandler.END
    
    try:
        wager_amount = int(update.message.text)
        if wager_amount <= 0:
            await update.message.reply_text("Please enter a positive number for the wager!")
            return WAGER_AMOUNT
    except ValueError:
        await update.message.reply_text("Please enter a valid number!")
        return WAGER_AMOUNT
    
    challenger = context.user_data['challenger']
    challenged = context.user_data['challenged']
    challenge_id = context.user_data['challenge_id']
    
    # Store in active challenges with wager
    active_challenges[challenge_id] = {
        'challenger_user': challenger,
        'challenged_user': challenged,
        'wager_amount': wager_amount,
        'timestamp': datetime.now().isoformat()
    }
    
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

async def challenge_response_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle challenge acceptance/decline."""
    query = update.callback_query
    await query.answer()
    
    action, challenge_id = query.data.split("_", 1)
    
    if challenge_id not in active_challenges:
        await query.edit_message_text("This challenge is no longer active or has expired.")
        if context.user_data and context.user_data.get('challenger_id') == query.from_user.id:
            context.user_data.clear()
        return ConversationHandler.END
    
    challenge_data = active_challenges[challenge_id]
    challenged_user_stored_username = challenge_data['challenged_user']
    
    user_clicking_callback = query.from_user
    
    can_respond = False
    # Primary check: Compare the username of the clicker (if they have one)
    # with the stored challenged username (case-insensitive).
    if user_clicking_callback.username:
        if user_clicking_callback.username.lower() == challenged_user_stored_username.lower():
            can_respond = True
    
    if not can_respond:
        clicker_display_name = user_clicking_callback.username or user_clicking_callback.first_name
        clicked_by_username = user_clicking_callback.username if user_clicking_callback.username else "[No Username]"
        user_id = user_clicking_callback.id
        
        logger.warning(
            f"Unauthorized attempt to respond to challenge. Challenge ID: {challenge_id}. Expected: @{challenged_user_stored_username}. Clicked by: @{clicked_by_username} (ID: {user_id})."
        )
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"😕 Sorry @{clicker_display_name}, only @{challenged_user_stored_username} (the one who was challenged) can accept or decline this battle.",
            reply_to_message_id=query.message.message_id
        )
        return CHALLENGE_CONFIRMATION # Stay in the same state
    
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
        del active_challenges[challenge_id]
        
        # Clear user_data
        if context.user_data:
            context.user_data.clear()
        
        # Generate battle story
        story = await generate_battle_story(challenger, challenged)
        
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
        winner = random.choice([challenger, challenged])
        loser = challenged if winner == challenger else challenger
        
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
        del active_challenges[challenge_id]
        
        # Clear user_data
        if context.user_data:
            context.user_data.clear()
        
        await query.edit_message_text(
            f"😔 @{challenged} has declined the challenge from @{challenger}.\n"
            f"Maybe next time! 🏛️"
        )
        
        return ConversationHandler.END

async def cancel_challenge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel_challenge command."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if not username:
        await update.message.reply_text("You need a username to participate in battles!")
        return
    
    # Find user's active challenge
    user_challenge_id = None
    for challenge_id, data in active_challenges.items():
        if data['challenger_user'].lower() == username.lower():
            user_challenge_id = challenge_id
            break
    
    if user_challenge_id:
        challenged_user = active_challenges[user_challenge_id]['challenged_user']
        del active_challenges[user_challenge_id]
        
        # Clear user_data if it belongs to this user
        if context.user_data.get('challenger_id') == user_id:
            context.user_data.clear()
        
        await update.message.reply_text(
            f"❌ @{username} has cancelled their challenge against @{challenged_user}."
        )
    else:
        await update.message.reply_text("You don't have any active challenges to cancel.")

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /leaderboard command."""
    overall = load_leaderboard(OVERALL_LEADERBOARD_FILE)
    text = format_leaderboard(overall, "🏆 Overall Leaderboard")
    await update.message.reply_text(text, parse_mode='Markdown')

async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /weekly command."""
    weekly = load_leaderboard(WEEKLY_LEADERBOARD_FILE)
    text = format_leaderboard(weekly, "📅 Weekly Leaderboard")
    await update.message.reply_text(text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    overall = load_leaderboard(OVERALL_LEADERBOARD_FILE)
    weekly = load_leaderboard(WEEKLY_LEADERBOARD_FILE)
    
    overall_stats = overall.get(target_user, {'wins': 0, 'losses': 0, 'marbles': 0})
    weekly_stats = weekly.get(target_user, {'wins': 0, 'losses': 0, 'marbles': 0})
    
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

async def my_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /my_stats command."""
    username = update.effective_user.username
    if not username:
        await update.message.reply_text("You need a username to view your stats!")
        return
    
    # Use the stats command logic with the user's username
    context.args = [username]
    await stats_command(update, context)

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current conversation."""
    context.user_data.clear()
    await update.message.reply_text("Operation cancelled!")
    return ConversationHandler.END

def main():
    """Start the bot."""
    # Get bot token from environment variable
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.critical("CRITICAL ERROR: BOT_TOKEN environment variable not found!")
        logger.critical("Please set the BOT_TOKEN environment variable with your Telegram bot token.")
        return
    
    logger.info("Starting Marbitz Battlebot...")
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Challenge conversation handler
    challenge_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('challenge', challenge_command)],
        states={
            WAGER_AMOUNT: [
                CallbackQueryHandler(wager_callback, pattern=r'^wager_(yes|no)_'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, wager_amount_handler)
            ],
            CHALLENGE_CONFIRMATION: [
                CallbackQueryHandler(challenge_response_callback, pattern=r'^(accept|decline)_')
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        per_user=True
    )
    
    # Add handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(challenge_conv_handler)
    application.add_handler(CommandHandler('cancel_challenge', cancel_challenge_command))
    application.add_handler(CommandHandler('leaderboard', leaderboard_command))
    application.add_handler(CommandHandler('weekly', weekly_command))
    application.add_handler(CommandHandler('stats', stats_command))
    application.add_handler(CommandHandler('my_stats', my_stats_command))
    
    # Start the bot
    logger.info("Bot is starting up and will begin polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()