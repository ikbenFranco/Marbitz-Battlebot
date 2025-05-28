// Instructions: Simplify f-string formatting in logger calls within challenge_response_callback to prevent potential SyntaxError.

\
// ... existing code ... <challenge_data = active_challenges[challenge_id]>
    # challenged_user_username is the one stored from the initial /challenge @<username> command
    challenged_user_stored_username = challenge_data['challenged_user']
    # challenger_user = challenge_data['challenger_user'] # This was not in the previous code structure here

    user_clicking_callback = query.from_user

    can_respond = False
    # Primary check: Compare the username of the clicker (if they have one)
    # with the stored challenged username (case-insensitive).
    if user_clicking_callback.username:
        if user_clicking_callback.username.lower() == challenged_user_stored_username.lower():
            can_respond = True

    if not can_respond:
        clicker_display_name = user_clicking_callback.username or user_clicking_callback.first_name
        clicked_by_log_username = user_clicking_callback.username if user_clicking_callback.username else "[No Username]"

        warning_log_message = (
            f"Unauthorized attempt to respond to challenge. "
            f"Challenge ID: {challenge_id}. "
            f"Expected: @{challenged_user_stored_username}. "
            f"Clicked by: @{clicked_by_log_username} (ID: {user_clicking_callback.id})."
        )
        logger.warning(warning_log_message)

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"😕 Sorry @{clicker_display_name}, only @{challenged_user_stored_username} (the one who was challenged) can accept or decline this battle.",
            reply_to_message_id=query.message.message_id
        )
        return CHALLENGE_CONFIRMATION # Stay in the same state

    # User is authorized to respond
    responding_user_log_name = user_clicking_callback.username if user_clicking_callback.username else user_clicking_callback.first_name
    info_log_message = (
        f"User @{responding_user_log_name} (ID: {user_clicking_callback.id}) "
        f"is responding to challenge ID {challenge_id} "
        f"for @{challenged_user_stored_username}."
    )
    logger.info(info_log_message)

    if action == 'accept':
        # Ensure the person clicking is the one who was challenged
        if query.from_user.username and query.from_user.username.lower() != challenged_user_stored_username.lower():
            # Check if the clicker is the challenger, trying to cancel maybe? No, separate /cancel command
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"@{query.from_user.username}, only @{challenged_user_stored_username} can respond to this challenge.",
                reply_to_message_id=query.message.message_id,
            )
            return CHALLENGE_CONFIRMATION # Stay in the same state

        if action == 'accept':
