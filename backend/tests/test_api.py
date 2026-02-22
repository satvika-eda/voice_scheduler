#!/usr/bin/env python3
"""
Simple test script to verify API routes are working.
Run the backend server first: cd backend && python -m uvicorn main:app --reload
"""

import requests
import json

BASE_URL = 'http://localhost:8000'

def test_health():
    """Test health check endpoint."""
    print('[TEST] Health Check')
    res = requests.get(f'{BASE_URL}/health')
    assert res.status_code == 200
    print(f'✓ Health check passed: {res.json()}')

def test_voice_init():
    """Test voice session initialization."""
    print('\n[TEST] Voice Init')
    res = requests.post(f'{BASE_URL}/api/voice/init')
    assert res.status_code == 200
    data = res.json()
    assert 'sessionId' in data
    print(f'✓ Session created: {data["sessionId"]}')
    return data['sessionId']

def test_voice_process(session_id):
    """Test voice processing."""
    print('\n[TEST] Voice Process')
    payload = {
        'sessionId': session_id,
        'userTranscript': "Hi, my name is John and I'd like to schedule a meeting for tomorrow at 2 PM."
    }
    res = requests.post(f'{BASE_URL}/api/voice/process', json=payload)
    assert res.status_code == 200
    data = res.json()
    print(f'✓ Assistant: {data["assistantMessage"]}')
    print(f'  Ready for event: {data["isReadyForEvent"]}')
    print(f'  User details: {data["userDetails"]}')
    return data

def test_auth_url():
    """Test OAuth URL generation."""
    print('\n[TEST] Auth URL')
    res = requests.get(f'{BASE_URL}/auth/url')
    # This may fail if GOOGLE_CLIENT_ID is not set
    if res.status_code == 200:
        data = res.json()
        assert 'authUrl' in data
        print(f'✓ Auth URL generated: {data["authUrl"][:80]}...')
    else:
        print(f'⚠ Auth URL test skipped (need Google credentials): {res.json()}')

if __name__ == '__main__':
    print('=== Voice Scheduling Agent - API Test ===\n')
    
    try:
        test_health()
        session_id = test_voice_init()
        test_voice_process(session_id)
        test_auth_url()
        print('\n✓ All tests passed!')
    except AssertionError as e:
        print(f'\n✗ Test failed: {e}')
    except Exception as e:
        print(f'\n✗ Error: {e}')
        print('Make sure the backend is running: cd backend && python -m uvicorn main:app --reload')
