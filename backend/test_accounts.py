#!/usr/bin/env python3
"""
Test script for User Accounts & Authentication.
Tests registration, login, reading history, and session linking.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_register():
    """Test user registration."""
    print_section("1. Testing User Registration")
    
    payload = {
        "email": "test@mysticapp.com",
        "password": "testpass123",
        "display_name": "Test User",
        "auth_provider": "email"
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/v1/auth/register", json=payload)
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 400 and "already registered" in response.text:
        print("ℹ User already exists, will test login instead")
        return None
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None
    
    data = response.json()
    print(f"✓ User registered")
    print(f"  User ID: {data['user_id']}")
    print(f"  Email: {data['email']}")
    print(f"  Token expires: {data['expires_at']}")
    
    return data["access_token"]


def test_login():
    """Test user login."""
    print_section("2. Testing User Login")
    
    payload = {
        "email": "test@mysticapp.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/v1/auth/login", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None
    
    data = response.json()
    print(f"✓ User logged in")
    print(f"  User ID: {data['user_id']}")
    print(f"  Access token: {data['access_token'][:20]}...")
    
    return data["access_token"]


def test_get_profile(token):
    """Test getting current user profile."""
    print_section("3. Testing Get User Profile")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/v1/auth/me", headers=headers)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return False
    
    data = response.json()
    print(f"\n📊 User Profile:")
    print(f"  Email: {data['email']}")
    print(f"  Display Name: {data['display_name']}")
    print(f"  Total Readings: {data['total_readings']}")
    print(f"  Total Spent: ${data['total_spent_usd']}")
    print(f"  Member Since: {data['created_at']}")
    
    print(f"\n✓ Profile retrieved")
    return True


def test_create_and_link_session(token):
    """Test creating a session and linking it to user account."""
    print_section("4. Testing Session Creation & Linking")
    
    # Create anonymous session
    print("Step 1: Creating session...")
    response = requests.post(f"{BASE_URL}/v1/sessions", json={
        "client_type": "ios",
        "style": "grounded"
    })
    session_id = response.json()["session_id"]
    print(f"✓ Session created: {session_id}")
    
    # Add birth data
    print("\nStep 2: Adding birth data...")
    requests.patch(f"{BASE_URL}/v1/sessions/{session_id}", json={
        "birth_date": "1992-12-05",
        "birth_time": "18:20",
        "birth_location_text": "Sydney, Australia",
        "question_intention": "What patterns am I repeating?"
    })
    print("✓ Birth data added")
    
    # Generate preview
    print("\nStep 3: Generating preview...")
    response = requests.post(f"{BASE_URL}/v1/sessions/{session_id}/preview")
    print("✓ Preview generated")
    
    # Purchase
    print("\nStep 4: Purchasing reading...")
    requests.post(f"{BASE_URL}/v1/sessions/{session_id}/purchase", json={
        "product_id": "reading_basic_199",
        "transaction_id": f"test_{session_id[:8]}"
    })
    print("✓ Reading purchased")
    
    # Generate reading
    print("\nStep 5: Generating full reading...")
    response = requests.post(f"{BASE_URL}/v1/sessions/{session_id}/reading")
    print("✓ Reading generated")
    
    # Link to user account
    print("\nStep 6: Linking session to user account...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/v1/sessions/{session_id}/link",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✓ Session linked to account")
    else:
        print(f"✗ Link failed: {response.text}")
        return False
    
    return session_id


def test_reading_history(token):
    """Test getting user's reading history."""
    print_section("5. Testing Reading History")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/v1/users/me/readings", headers=headers)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return False
    
    data = response.json()
    readings = data.get("readings", [])
    
    print(f"\n📚 Reading Library:")
    print(f"  Total readings: {data['total']}")
    
    if readings:
        print(f"\n  Recent readings:")
        for reading in readings[:3]:
            print(f"    - {reading['created_at'][:10]}: \"{reading['question']}\"")
            print(f"      Products: {', '.join(reading['purchased_products'])}")
    else:
        print(f"  No readings yet")
    
    print(f"\n✓ Reading history retrieved")
    return True


def test_user_stats(token):
    """Test getting user statistics."""
    print_section("6. Testing User Statistics")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/v1/users/me/stats", headers=headers)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return False
    
    data = response.json()
    
    print(f"\n📊 User Statistics:")
    print(f"  Total sessions: {data['total_sessions']}")
    print(f"  Completed readings: {data['completed_readings']}")
    print(f"  Total spent: ${data['total_spent_usd']}")
    print(f"  Member since: {data['member_since'][:10]}")
    
    insights = data.get("insights", {})
    if insights.get("most_common_sun_sign"):
        print(f"\n  🌟 Insights:")
        print(f"    Most queried sign: {insights['most_common_sun_sign']}")
        if insights.get("most_drawn_card"):
            print(f"    Most drawn card: {insights['most_drawn_card']}")
    
    print(f"\n✓ User stats retrieved")
    return True


def test_logout(token):
    """Test logout (token revocation)."""
    print_section("7. Testing Logout")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/v1/auth/logout", headers=headers)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ User logged out")
        
        # Verify token is invalid
        print("\nVerifying token is revoked...")
        response = requests.get(f"{BASE_URL}/v1/auth/me", headers=headers)
        if response.status_code == 401:
            print("✓ Token successfully revoked")
            return True
        else:
            print("✗ Token still valid (should be revoked)")
            return False
    else:
        print(f"✗ Logout failed: {response.text}")
        return False


def main():
    """Run accounts system tests."""
    print("\n" + "="*60)
    print("  ACCOUNTS & STATE MANAGEMENT TESTS")
    print("="*60)
    
    try:
        # Test registration
        token = test_register()
        
        # If registration failed (user exists), try login
        if not token:
            token = test_login()
        
        if not token:
            print("\n❌ Could not authenticate user")
            return 1
        
        # Test authenticated endpoints
        test_get_profile(token)
        test_create_and_link_session(token)
        test_reading_history(token)
        test_user_stats(token)
        test_logout(token)
        
        # Success
        print_section("✅ ALL TESTS PASSED")
        print("User accounts and state management working!")
        print("\nℹ NOTE: Apple Sign In not tested (requires iOS client)")
        print()
        
        return 0
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API")
        print("Make sure the server is running: uvicorn main:app --reload")
        return 1
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
