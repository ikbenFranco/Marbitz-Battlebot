#!/usr/bin/env python3
"""
Test script to verify the wager functionality is working correctly.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from marbitz_battlebot.battle import create_challenge, get_challenge, update_challenge, remove_challenge
from marbitz_battlebot.battle import initialize_battle_system

def test_wager_functionality():
    """Test the wager functionality."""
    print("🧪 Testing Wager Functionality")
    print("=" * 40)
    
    # Initialize the battle system
    initialize_battle_system()
    print("✅ Battle system initialized")
    
    # Test 1: Create a challenge with wager
    print("\n📝 Test 1: Creating challenge with wager")
    try:
        challenge_id = create_challenge("testuser1", "testuser2", 50)
        print(f"✅ Challenge created with ID: {challenge_id}")
        
        # Get challenge data
        challenge_data = get_challenge(challenge_id)
        if challenge_data:
            print(f"✅ Challenge data retrieved:")
            print(f"   - Challenger: {challenge_data.get('challenger_user')}")
            print(f"   - Challenged: {challenge_data.get('challenged_user')}")
            print(f"   - Wager: {challenge_data.get('wager_amount')} marbles")
            print(f"   - Status: {challenge_data.get('status')}")
        else:
            print("❌ Failed to retrieve challenge data")
            return False
            
    except Exception as e:
        print(f"❌ Error creating challenge: {e}")
        return False
    
    # Test 2: Update wager amount
    print("\n📝 Test 2: Updating wager amount")
    try:
        success = update_challenge(challenge_id, {'wager_amount': 100})
        if success:
            print("✅ Wager amount updated successfully")
            
            # Verify update
            updated_data = get_challenge(challenge_id)
            if updated_data and updated_data.get('wager_amount') == 100:
                print(f"✅ Wager amount verified: {updated_data.get('wager_amount')} marbles")
            else:
                print("❌ Wager amount update verification failed")
                return False
        else:
            print("❌ Failed to update wager amount")
            return False
            
    except Exception as e:
        print(f"❌ Error updating wager: {e}")
        return False
    
    # Test 3: Create challenge with zero wager
    print("\n📝 Test 3: Creating challenge with zero wager")
    try:
        challenge_id_2 = create_challenge("testuser3", "testuser4", 0)
        print(f"✅ Zero-wager challenge created with ID: {challenge_id_2}")
        
        challenge_data_2 = get_challenge(challenge_id_2)
        if challenge_data_2 and challenge_data_2.get('wager_amount') == 0:
            print(f"✅ Zero wager verified: {challenge_data_2.get('wager_amount')} marbles")
        else:
            print("❌ Zero wager verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Error creating zero-wager challenge: {e}")
        return False
    
    # Cleanup
    print("\n🧹 Cleaning up test data")
    try:
        remove_challenge(challenge_id)
        remove_challenge(challenge_id_2)
        print("✅ Test challenges removed")
    except Exception as e:
        print(f"⚠️ Warning: Error during cleanup: {e}")
    
    print("\n🎉 All wager functionality tests passed!")
    return True

if __name__ == "__main__":
    success = test_wager_functionality()
    sys.exit(0 if success else 1)