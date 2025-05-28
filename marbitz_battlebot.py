// Instructions: More robustly check if the user clicking the accept/decline button is the intended challenged user by focusing on case-insensitive username matching. Add logging for this check.

\
// ... existing code ... <action, challenge_id = query.data.split("_", 1)>

    if challenge_id not in active_challenges:
        await query.edit_message_text("This challenge is no longer active or has expired.")
        # Attempt to clear user_data just in case, though this path might not have it.
        if context.user_data and context.user_data.get('challenger_id') == query.from_user.id:
            context.user_data.clear()
        return ConversationHandler.END

    challenge_data = active_challenges[challenge_id]
    # challenged_user_username is the one stored from the initial /challenge @<username> command
    challenged_user_stored_username = challenge_data['challenged_user']
    challenger_user = challenge_data['challenger_user']

    user_clicking_callback = query.from_user

    can_respond = False
    # Primary check: Compare the username of the clicker (if they have one)
    # with the stored challenged username (case-insensitive).
    if user_clicking_callback.username:
        if user_clicking_callback.username.lower() == challenged_user_stored_username.lower():
            can_respond = True

    # If primary check fails, let's consider the user ID.
    # This is a bit of a stretch because we don't explicitly store the challenged user's ID.
    # However, if the challenged user *is* the one clicking, their ID should match SOME part of the system.
    # This specific section might need more robust ID handling in the future if usernames prove too unreliable.
    # For now, the username check is the main guard.

    if not can_respond:
        clicker_display_name = user_clicking_callback.username or user_clicking_callback.first_name
        logger.warning(
            f"Unauthorized attempt to respond to challenge. "
            f"Challenge ID: {challenge_id}, "
            f"Expected: @{challenged_user_stored_username}, "
            f"Clicked by: @{user_clicking_callback.username} (ID: {user_clicking_callback.id})"
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"😕 Sorry @{clicker_display_name}, only @{challenged_user_stored_username} (the one who was challenged) can accept or decline this battle.",
            reply_to_message_id=query.message.message_id
        )
        return CHALLENGE_CONFIRMATION # Stay in the same state

    # User is authorized to respond
    logger.info(f"User @{user_clicking_callback.username or user_clicking_callback.first_name} (ID: {user_clicking_callback.id}) is responding to challenge ID {challenge_id} for @{challenged_user_stored_username}.")

    if action == 'accept':
        if query.from_user.username and query.from_user.username.lower() != challenged_user_stored_username.lower():
            # Check if the clicker is the challenger, trying to cancel maybe? No, separate /cancel command
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"@{query.from_user.username}, only @{challenged_user_username} can respond to this challenge.",
                reply_to_message_id=query.message.message_id,
            )
            return CHALLENGE_CONFIRMATION # Stay in the same state

    if action == 'accept':
