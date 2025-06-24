# Challenge Expiration Feature

## Overview

The Challenge Expiration feature ensures that challenges don't remain active indefinitely if they're not accepted or declined. This improves the user experience by cleaning up stale challenges and encouraging timely responses.

## Key Components

### 1. Automatic Expiration

- Challenges automatically expire after 6 hours if not accepted or declined
- A periodic cleanup task runs every hour to remove expired challenges
- Users receive notifications when their challenges are about to expire

### 2. Status Command

A new `/status` command allows users to:
- Check the status of their active challenges
- See when a challenge will expire
- View a visual progress bar showing expiration progress
- Cancel their challenges directly from the status message

### 3. Expiry Notifications

- Users receive a notification when their challenge is about to expire (1 hour before expiration)
- The notification includes information about the challenge and how to check its status

## Implementation Details

### Cleanup Task

The cleanup task runs periodically to:
1. Check for expired challenges (older than 6 hours)
2. Remove expired challenges from the system
3. Check for challenges that will expire soon and send notifications

### Challenge Status

The status command provides detailed information about a challenge:
- Challenger and challenged usernames
- Wager amount (if any)
- Challenge status (pending, accepted, etc.)
- Creation time and expiration time
- Time remaining until expiration
- Visual progress bar showing expiration progress

### Cancel Button

The status command includes a cancel button that allows users to:
- Cancel their challenge directly from the status message
- Receive immediate confirmation of the cancellation

## Benefits

1. **Improved User Experience**: Users don't have to deal with stale challenges
2. **Reduced Database Clutter**: Expired challenges are automatically removed
3. **Timely Responses**: Users are encouraged to respond to challenges promptly
4. **Better Challenge Management**: Users have more visibility and control over their challenges

## Usage

### Checking Challenge Status

```
/status
```

This command shows:
- Your active challenge details
- When the challenge will expire
- A visual progress bar of expiration
- A button to cancel the challenge

### Cancelling a Challenge

Two methods:
1. Use the `/cancel_challenge` command
2. Use the "Cancel Challenge" button in the status message

### Expiry Notifications

Users automatically receive notifications when:
- Their challenge is about to expire (1 hour before expiration)
- The notification includes instructions on how to check status or create a new challenge