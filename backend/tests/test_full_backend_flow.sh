#!/bin/bash

BACKEND="${BACKEND_URL:-http://localhost:8000}"

echo "====== FULL BACKEND FLOW TEST ======"
echo ""

# Step 1: Initialize session
echo "[1/5] Initializing session..."
TIMEZONE="America/New_York"
SESSION_RESPONSE=$(curl -s -X POST "$BACKEND/api/voice/init" \
  -H "Content-Type: application/json" \
  -d "{\"timezone\": \"$TIMEZONE\"}")
SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.sessionId')
echo "✅ Session ID: $SESSION_ID (timezone: $TIMEZONE)"
echo ""

# Step 2: Set user details
echo "[2/5] Setting user details..."
TOMORROW=$(date -v+1d +"%Y-%m-%d")
DETAILS_RESPONSE=$(curl -s -X POST "$BACKEND/api/voice/set-details" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"$SESSION_ID\",
    \"userDetails\": {
      \"name\": \"Test User\",
      \"date\": \"$TOMORROW\",
      \"time\": \"10:00\",
      \"duration\": \"30\",
      \"title\": \"Backend Test Meeting\"
    }
  }")
IS_READY=$(echo $DETAILS_RESPONSE | jq -r '.isReadyForEvent')
echo "✅ Details set. isReadyForEvent: $IS_READY"
echo "   Details: $(echo $DETAILS_RESPONSE | jq '.userDetails')"
echo ""

# Step 3: Get auth URL
echo "[3/5] Getting Google auth URL..."
AUTH_URL_RESPONSE=$(curl -s -X GET "$BACKEND/auth/url")
AUTH_URL=$(echo $AUTH_URL_RESPONSE | jq -r '.authUrl')
echo "✅ Auth URL obtained"
echo ""
echo "🔐 PLEASE COMPLETE GOOGLE OAUTH:"
echo "   1. Open this URL in your browser:"
echo "   $AUTH_URL"
echo ""
echo "   2. Sign in with your Google account"
echo "   3. Grant calendar permissions"
echo "   4. You'll be redirected to http://localhost:8000/oauth/callback?code=..."
echo "   5. Copy the 'code' parameter from the URL"
echo ""
read -p "Paste the auth code here: " AUTH_CODE
echo ""

if [ -z "$AUTH_CODE" ]; then
  echo "❌ No auth code provided. Exiting."
  exit 1
fi

# Step 4: Exchange auth code for tokens
echo "[4/5] Exchanging auth code for tokens..."
CALLBACK_RESPONSE=$(curl -s -X POST "$BACKEND/auth/callback" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"$SESSION_ID\",
    \"code\": \"$AUTH_CODE\"
  }")
CALLBACK_SUCCESS=$(echo $CALLBACK_RESPONSE | jq -r '.success // empty')
echo "✅ OAuth callback response: $CALLBACK_RESPONSE"
echo ""

# Step 5: Create calendar event
echo "[5/5] Creating calendar event..."
CREATE_RESPONSE=$(curl -s -X POST "$BACKEND/api/calendar/create" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"$SESSION_ID\",
    \"userDetails\": {
      \"name\": \"Test User\",
      \"date\": \"$TOMORROW\",
      \"time\": \"10:00\",
      \"duration\": \"30\",
      \"title\": \"Backend Test Meeting\"
    }
  }")

echo "✅ Response:"
echo $CREATE_RESPONSE | jq . 2>/dev/null || echo $CREATE_RESPONSE
echo ""

# Check if successful
SUCCESS=$(echo $CREATE_RESPONSE | jq -r '.success // empty')
if [ "$SUCCESS" = "true" ]; then
  EVENT_ID=$(echo $CREATE_RESPONSE | jq -r '.eventId')
  EVENT_LINK=$(echo $CREATE_RESPONSE | jq -r '.eventLink')
  echo "========================================"
  echo "🎉 EVENT CREATED SUCCESSFULLY!"
  echo "========================================"
  echo "Event ID: $EVENT_ID"
  echo "Event Link: $EVENT_LINK"
  echo ""
  echo "Check your Google Calendar to verify!"
else
  ERROR=$(echo $CREATE_RESPONSE | jq -r '.error // .detail // "Unknown error"')
  echo "========================================"
  echo "❌ EVENT CREATION FAILED"
  echo "========================================"
  echo "Error: $ERROR"
fi
