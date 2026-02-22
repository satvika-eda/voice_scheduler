#!/usr/bin/env python3
"""
Test calendar event creation via backend API endpoints directly
"""
import os
import requests
import json
from datetime import datetime, timedelta

# Backend URL - override with BACKEND_URL env var
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def test_calendar_creation():
    print("=" * 60)
    print("TESTING CALENDAR EVENT CREATION")
    print("=" * 60)
    
    # Step 1: Initialize session
    print("\n[1] Initializing session...")
    try:
        response = requests.post(f"{BACKEND_URL}/api/voice/init", timeout=10)
        response.raise_for_status()
        session_data = response.json()
        session_id = session_data.get("sessionId")
        print(f"✅ Session created: {session_id}")
    except Exception as e:
        print(f"❌ Failed to init session: {e}")
        return
    
    # Step 2: Set user details
    print(f"\n[2] Setting user details for session {session_id}...")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    user_details = {
        "name": "Test User",
        "date": tomorrow,
        "time": "10:00 AM",
        "duration": "30",
        "title": "API Test Meeting"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/voice/set-details",
            json={
                "sessionId": session_id,
                "userDetails": user_details
            },
            timeout=10
        )
        response.raise_for_status()
        set_details_response = response.json()
        print(f"✅ Details set: {set_details_response}")
        
        is_ready = set_details_response.get("isReadyForEvent")
        print(f"   Is Ready For Event: {is_ready}")
    except Exception as e:
        print(f"❌ Failed to set details: {e}")
        return
    
    # Step 3: Create calendar event
    print(f"\n[3] Creating calendar event...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/calendar/create",
            json={
                "sessionId": session_id,
                "userDetails": user_details
            },
            timeout=30
        )
        response.raise_for_status()
        create_response = response.json()
        print(f"✅ Response: {json.dumps(create_response, indent=2)}")
        
        if create_response.get("success"):
            print(f"\n🎉 EVENT CREATED SUCCESSFULLY!")
            print(f"   Event ID: {create_response.get('eventId')}")
            print(f"   Event Link: {create_response.get('eventLink')}")
        else:
            print(f"\n❌ Event creation failed: {create_response.get('error')}")
    
    except Exception as e:
        print(f"❌ Failed to create event: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")

if __name__ == "__main__":
    test_calendar_creation()
