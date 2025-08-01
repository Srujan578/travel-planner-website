#!/usr/bin/env python3
"""
Test script for the enhanced travel planner authentication system
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_registration():
    """Test user registration"""
    print("🧪 Testing user registration...")
    
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=data)
        result = response.json()
        
        if result.get('success'):
            print("✅ Registration successful!")
            return True
        else:
            print(f"❌ Registration failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False

def test_login():
    """Test user login"""
    print("🧪 Testing user login...")
    
    data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=data)
        result = response.json()
        
        if result.get('success'):
            print("✅ Login successful!")
            return True
        else:
            print(f"❌ Login failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

def test_profile():
    """Test getting user profile"""
    print("🧪 Testing profile retrieval...")
    
    try:
        response = requests.get(f"{BASE_URL}/auth/profile")
        result = response.json()
        
        if result.get('success'):
            print("✅ Profile retrieval successful!")
            print(f"   Username: {result['user']['username']}")
            print(f"   Email: {result['user']['email']}")
            return True
        else:
            print(f"❌ Profile retrieval failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Profile retrieval error: {e}")
        return False

def test_chat():
    """Test chat functionality"""
    print("🧪 Testing chat functionality...")
    
    data = {
        "message": "Plan a trip to Tokyo for 5 days",
        "session_id": "test_session"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat", json=data)
        result = response.json()
        
        if result.get('success'):
            print("✅ Chat successful!")
            print(f"   Response type: {'JSON' if result.get('is_json') else 'Text'}")
            return True
        else:
            print(f"❌ Chat failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting authentication system tests...")
    print("=" * 50)
    
    # Test registration
    if not test_registration():
        print("❌ Registration test failed. Stopping tests.")
        return
    
    # Test login
    if not test_login():
        print("❌ Login test failed. Stopping tests.")
        return
    
    # Test profile
    if not test_profile():
        print("❌ Profile test failed. Stopping tests.")
        return
    
    # Test chat
    if not test_chat():
        print("❌ Chat test failed. Stopping tests.")
        return
    
    print("=" * 50)
    print("🎉 All tests passed! Authentication system is working correctly.")
    print("\n📝 Next steps:")
    print("1. Visit http://localhost:8080 in your browser")
    print("2. Register with a new account")
    print("3. Login and start planning your trips!")
    print("4. Try follow-up requests like 'Make day 2 more adventurous'")

if __name__ == "__main__":
    main() 