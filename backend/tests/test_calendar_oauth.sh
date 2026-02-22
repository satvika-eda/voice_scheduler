#!/bin/bash

BACKEND="${BACKEND_URL:-http://localhost:8000}"

echo "====== COMPLETE CALENDAR EVENT CREATION TEST ======"
echo ""

# Step 1: Initialize session
echo "[1] Initializing session..."
SESSION_RESPONSE=$(curl -s -X POST "$BACKEND/api/voice/init" -H "Content-Type: application/json")
SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.sessionId')
echo "✅ Session ID: $SESSION_ID"
echo ""

# Step 2: Set user details
echo "[2] Setting user details..."
TOMORROW=$(date -v+1d +"%Y-%m-%d")
DETAILS_RESPONSE=$(curl -s -X POST "$BACKEND/api/voice/set-details" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"$SESSION_ID\",
    \"userDetails\": {
      \"name\": \"Test User\",
      \"date\": \"$TOMORROW\",
      \"time\": \"10:00 AM\",
      \"duration\": \"30\",
      \"title\": \"API Test Meeting\"
    }
  }")
IS_READY=$(echo $DETAILS_RESPONSE | jq -r '.isReadyForEvent')
echo "✅ Details set. isReadyForEvent: $IS_READY"
echo ""

# Step 3: Get Google auth URL
echo "[3] Getting Google auth URL..."
AUTH_URL_RESPONSE=$(curl -s -X GET "$BACKEND/auth/url")
AUTH_URL=$(echo $AUTH_URL_RESPONSE | jq -r '.authUrl')
echo "✅ Auth URL: $AUTH_URL"
echo ""
echo "⚠️  TO COMPLETE THE TEST:"
echo "   1. Open the URL above in your browser"
echo "   2. Complete Google OAuth"
echo "   3. You'll be redirected with an auth code"
echo "   4. Copy the 'code' parameter from the URL"
echo "   5. Paste it below"
echo ""
read -p "Enter the auth code from the redirect URL: " AUTH_CODE
echo ""

# Step 4: Handle auth callback
echo "[4] Exchanging auth code for tokens..."
CALLBACK_RESPONSE=$(curl -s -X POST "$BACKEND/auth/callback" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"$SESSION_ID\",
    \"code\": \"$AUTH_CODE\"
  }")
echo "✅ Response: $CALLBACK_RESPONSE" | jq . 2>/dev/null || echo $CALLBACK_RESPONSE
echo ""

# Step 5: Create calendar event
echo "[5] Creating calendar event..."
CREATE_RESPONSE=$(curl -s -X POST "$BACKEND/api/calendar/create" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"$SESSION_ID\",
    \"userDetails\": {
      \"name\": \"Test User\",
      \"date\": \"$TOMORROW\",
      \"time\": \"10:00 AM\",
      \"duration\": \"30\",
      \"title\": \"API Test Meeting\"
    }
  }")

if echo $CREATE_RESPONSE | jq . &>/dev/null; then
  SUCCESS=$(echo $CREATE_RESPONSE | jq -r '.success')
  if [ "$SUCCESS" = "true" ]; then
    echo "🎉 EVENT CREATED SUCCESSFULLY!"
    echo $CREATE_RESPONSE | jq .
  else
    echo "❌ Event creation failed:"
    echo $CREATE_RESPONSE | jq .
  fi
else
  echo "❌ Invalid response:"
  echo $CREATE_RESPONSE
fi
