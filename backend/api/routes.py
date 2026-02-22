# backend/api/routes.py

import os
import uuid
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI

from calendar_providers.google_calendar import create_event
from calendar_providers.auth import get_flow
from utils.datetime_parser import parse_datetime
from utils.text_parser import extract_user_details
from utils.logger import log_info, log_error

load_dotenv()

router = APIRouter()

# Default timezone from env or fallback to New York
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "America/New_York")

# -----------------------------
# OpenAI client (lazy init)
# -----------------------------
_openai_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")
        try:
            _openai_client = OpenAI(api_key=api_key)
        except TypeError as e:
            # Fallback for some library versions or if proxies arg is being auto-injected
            log_error(f"OpenAI Init Error: {e}")
            # Try initializing without args if possible or just api_key
            _openai_client = OpenAI(api_key=api_key, http_client=None)
    return _openai_client


# -----------------------------
# In-memory session store
# (use Redis in production)
# -----------------------------
sessions: Dict[str, Dict[str, Any]] = {}


# -----------------------------
# Pydantic Models
# -----------------------------
class VoiceInitResponse(BaseModel):
    sessionId: str


class VoiceInitRequest(BaseModel):
    timezone: str = "America/New_York"


class VoiceProcessRequest(BaseModel):
    sessionId: str
    userTranscript: str


class VoiceProcessResponse(BaseModel):
    assistantMessage: str
    isReadyForEvent: bool
    userDetails: dict


class CalendarCreateRequest(BaseModel):
    sessionId: str
    userDetails: dict = None


class AuthCallbackRequest(BaseModel):
    code: str
    sessionId: str


# -----------------------------
# HEALTH CHECK
# -----------------------------
@router.get("/health")
async def health():
    log_info("Health check passed")
    return {"status": "ok"}


# -----------------------------
# VOICE SESSION ENDPOINTS
# -----------------------------
@router.post("/api/voice/init", response_model=VoiceInitResponse)
async def voice_init(req: VoiceInitRequest = None):
    """Initialize a new voice session."""
    session_id = str(uuid.uuid4())
    user_timezone = (req.timezone if req else None) or DEFAULT_TIMEZONE
    sessions[session_id] = {
        "authed": False,
        "conversationState": "awaiting_info",
        "userDetails": {},
        "tokens": None,
        "timezone": user_timezone,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    log_info(f"✨ [VOICE_INIT] New session created: {session_id} (timezone: {user_timezone})")
    return VoiceInitResponse(sessionId=session_id)


@router.post("/api/voice/process", response_model=VoiceProcessResponse)
async def voice_process(req: VoiceProcessRequest):
    """
    Your frontend calls this on each final user transcript to:
    - parse details (local regex parsing)
    - generate assistant message via OpenAI
    """
    log_info(f"🎤 [VOICE_PROCESS] Received request for session: {req.sessionId}")
    
    if req.sessionId not in sessions:
        log_error(f"❌ [VOICE_PROCESS] Invalid session: {req.sessionId}")
        raise HTTPException(status_code=400, detail="Invalid session")

    session = sessions[req.sessionId]
    user_transcript = (req.userTranscript or "").strip()
    log_info(f"📝 [VOICE_PROCESS] Transcript: '{user_transcript}'")

    if not user_transcript:
        raise HTTPException(status_code=400, detail="Empty transcript")

    # Extract details from transcript (your regex-based extractor)
    old_details = session.get("userDetails", {}).copy()
    extract_user_details(session, user_transcript)
    new_details = session.get("userDetails", {})
    
    log_info(f"🔍 [VOICE_PROCESS] Details stats | Old: {old_details} -> New: {new_details}")

    # Generate assistant response using OpenAI
    system_prompt = f"""You are a helpful voice assistant for scheduling meetings.
Your job is to collect the user's name, preferred date, time, duration (in minutes), and optional meeting title.
Current collected details: {json.dumps(session['userDetails'])}

Rules:
- Ask for missing info conversationally (1 question at a time).
- Confirm details BEFORE any "ready" message.
- When you have name, date, and time (duration optional), say: "Perfect! I'm ready to create your event now."
- Never say the event is created/confirmed unless the system explicitly tells you "Calendar event created successfully".
Keep responses brief (1-2 sentences)."""

    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_transcript},
            ],
            temperature=0.7,
            max_tokens=120,
        )
        assistant_message = response.choices[0].message.content or ""
        log_info(f"🤖 [VOICE_PROCESS] AI Response: '{assistant_message}'")
    except Exception as e:
        log_error(f"❌ [VOICE_PROCESS] OpenAI error: {str(e)}")
        assistant_message = "I had trouble processing that. Could you please repeat?"

    # Ready when core fields exist (duration optional; you default to 60 later)
    d = session.get("userDetails", {}) or {}
    is_ready = all(d.get(k) for k in ["name", "date", "time"])

    print(f"🎯 VOICE_PROCESS: transcript='{user_transcript}'")
    print(f"📍 Extracted details: {d}")
    print(f"✅ is_ready={is_ready} (name={d.get('name')}, date={d.get('date')}, time={d.get('time')})")
    log_info(f"✅ [VOICE_PROCESS] Completed. Ready: {is_ready}. Details: {d}")

    return VoiceProcessResponse(
        assistantMessage=assistant_message,
        isReadyForEvent=is_ready,
        userDetails=d,
    )

@router.post("/api/voice/set-details", response_model=VoiceProcessResponse)
async def set_details(req: CalendarCreateRequest):
    """
    Manually set user details for testing.
    """
    if req.sessionId not in sessions:
        log_error(f"Invalid session: {req.sessionId}")
        raise HTTPException(status_code=400, detail="Invalid session")
    
    session = sessions[req.sessionId]
    session["userDetails"] = req.userDetails
    
    d = session.get("userDetails", {}) or {}
    is_ready = all(d.get(k) for k in ["name", "date", "time"])
    
    print(f"🎯 SET_DETAILS: {d}")
    print(f"✅ is_ready={is_ready}")
    
    return VoiceProcessResponse(
        assistantMessage="Details updated",
        isReadyForEvent=is_ready,
        userDetails=d,
    )

@router.post("/api/voice/update")
async def vapi_update(request: Request):
    """
    Vapi custom tool calls hit this endpoint.
    MUST return:
      { "results": [ { "toolCallId": "...", "result": "<single-line-string>" } ] }
    """
    body = await request.json()
    log_info(f"🔄 [VAPI_UPDATE] Received update: {body.get('type')}")
    # log_info(f"Full Body: {body}")

    # Vapi sends tool calls in different shapes; handle common variants.
    tool_calls = (
        body.get("toolCalls")
        or body.get("message", {}).get("toolCalls")
        or body.get("toolCallList")
        or []
    )
    
    log_info(f"🛠️ [VAPI_UPDATE] Tool calls found: {len(tool_calls)}")

    if not tool_calls:
        log_info("⚠️ [VAPI_UPDATE] No tool calls, skipping.")
        return JSONResponse(
            status_code=200,
            content={
                "results": [
                    {
                        "toolCallId": body.get("toolCallId", "unknown"),
                        "result": "{\"ok\":false,\"error\":\"No toolCalls found\"}",
                    }
                ]
            },
        )

    results = []

    for tc in tool_calls:
        tool_call_id = tc.get("id") or tc.get("toolCallId") or "unknown"

        args = tc.get("args") or tc.get("parameters") or tc.get("function", {}).get("arguments") or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception as e:
                log_error(f"❌ [VAPI_UPDATE] Failed to parse args: {args}. Error: {e}")
                args = {}
        
        log_info(f"🔧 [VAPI_UPDATE] Tool: {tc.get('function', {}).get('name')}, CallId: {tool_call_id}, Args: {args}")

        session_id = args.get("sessionId")
        user_details = args.get("userDetails", {}) or {}

        if not session_id or session_id not in sessions:
            log_error(f"❌ [VAPI_UPDATE] Invalid sessionId: {session_id}")
            result_str = json.dumps(
                {"ok": False, "error": "Invalid sessionId", "sessionId": session_id},
                separators=(",", ":"),
            )
            results.append({"toolCallId": tool_call_id, "result": result_str})
            continue

        # normalize duration to string if present
        if "duration" in user_details and user_details["duration"] is not None:
            try:
                user_details["duration"] = str(int(user_details["duration"]))
            except Exception:
                pass
        
        log_info(f"📝 [VAPI_UPDATE] Updating details for session {session_id} with: {user_details}")
        
        # merge updates into the session
        sessions[session_id]["userDetails"] = {
            **(sessions[session_id].get("userDetails") or {}),
            **user_details,
        }

        d = sessions[session_id]["userDetails"]
        is_ready = all(d.get(k) for k in ["name", "date", "time"])
        
        log_info(f"✅ [VAPI_UPDATE] Updated state. IsReady: {is_ready}. Details: {d}")

        # Vapi requires SINGLE LINE STRING
        result_str = json.dumps(
            {"ok": True, "sessionId": session_id, "userDetails": d, "isReadyForEvent": is_ready},
            separators=(",", ":"),
        )
        results.append({"toolCallId": tool_call_id, "result": result_str})
    
    log_info("📤 [VAPI_UPDATE] Returning results to Vapi.")
    return JSONResponse(status_code=200, content={"results": results})


# -----------------------------
# GOOGLE OAUTH
# -----------------------------
@router.get("/auth/url")
async def get_auth_url():
    """Get Google OAuth authorization URL."""
    try:
        log_info("📍 Step 1: Generating Google OAuth URL")
        flow = get_flow()
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
        )
        log_info(f"✅ Auth URL generated with state: {state}")
        log_info(f"OAuth URL: {auth_url[:80]}...")
        return {"authUrl": auth_url}
    except Exception as e:
        log_error(f"Auth URL error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate auth URL")


@router.get("/auth/callback")
async def auth_callback_get(code: str = None, state: str = None, error: str = None):
    """Handle OAuth callback from Google (GET request with query params)."""
    if error:
        return JSONResponse(
            status_code=400,
            content={"error": error, "message": "Authentication failed"}
        )
    
    if not code:
        return JSONResponse(
            status_code=400,
            content={"error": "missing_code", "message": "No authorization code received"}
        )
    
    log_info(f"📍 Step 2: Received OAuth callback with code: {code[:20]}...")
    return JSONResponse(
        status_code=200,
        content={"code": code, "state": state, "message": "Auth code received. Use POST /auth/callback to exchange for tokens."}
    )


@router.post("/auth/callback")
async def auth_callback(req: AuthCallbackRequest):
    """Handle OAuth callback and exchange code for tokens (POST from frontend/CLI)."""
    if req.sessionId not in sessions:
        log_error(f"❌ Invalid session for auth callback: {req.sessionId}")
        raise HTTPException(status_code=400, detail="Invalid session")

    try:
        log_info(f"📍 Step 2: Processing OAuth callback for session {req.sessionId}")
        log_info(f"Auth code received: {req.code[:20]}...")

        flow = get_flow()
        log_info("Exchanging auth code for tokens...")
        flow.fetch_token(code=req.code)
        creds = flow.credentials

        session = sessions[req.sessionId]
        session["tokens"] = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }
        session["authed"] = True

        log_info(f"✅ Session {req.sessionId} authenticated successfully")
        return {"success": True, "message": "Authentication successful"}
    except Exception as e:
        log_error(f"Auth callback error: {str(e)}")
        raise HTTPException(status_code=400, detail="Authentication failed")


# -----------------------------
# CALENDAR CREATION
# -----------------------------
@router.post("/api/calendar/create")
async def create_calendar_event(req: CalendarCreateRequest):
    """Create a Google Calendar event using service account."""
    log_info(f"📍 [CALENDAR_CREATE] Creating calendar event for session {req.sessionId}")

    session = sessions.get(req.sessionId)
    if not session and not req.userDetails:
        log_error(f"❌ [CALENDAR_CREATE] Invalid session: {req.sessionId}")
        raise HTTPException(status_code=400, detail="Invalid session")

    # Use provided userDetails or get from session
    user_details = req.userDetails or (session.get("userDetails") if session else {}) or {}
    log_info(f"📋 [CALENDAR_CREATE] Processing user details: {user_details}")

    # Require name/date/time; duration optional (defaults to 60)
    required = ["name", "date", "time"]
    missing = [k for k in required if not user_details.get(k)]
    if missing:
        msg = f"Missing required fields: {', '.join(missing)}"
        log_error(f"❌ [CALENDAR_CREATE] {msg}")
        raise HTTPException(status_code=400, detail=msg)

    try:
        date_str = str(user_details["date"]).strip()
        time_str = str(user_details["time"]).strip()
        duration_str = user_details.get("duration") or "60"
        duration_minutes = int(duration_str) if str(duration_str).strip() else 60

        normalized_start = parse_datetime(f"{date_str} {time_str}")
        datetime_str = normalized_start.replace(second=0, microsecond=0).isoformat()
        user_timezone = (session or {}).get("timezone", "America/New_York")
        title = user_details.get("title") or f"Meeting with {user_details['name']}"

        log_info(f"📅 [CALENDAR_CREATE] Event Params: Title='{title}', Start='{datetime_str}', Duration={duration_minutes}min, TZ='{user_timezone}'")
        log_info("🔄 [CALENDAR_CREATE] Calling Google Calendar API...")

        result = create_event(
            name=user_details["name"],
            datetime_str=datetime_str,
            title=title,
            token_data=None,  # Use service account, not user tokens
            duration_minutes=duration_minutes,
            timezone=user_timezone,
        )

        log_info(f"✅ [CALENDAR_CREATE] Event created successfully! ID: {result.get('id')}")
        log_info(f"🔗 [CALENDAR_CREATE] Link: {result.get('htmlLink')}")

        return {
            "success": True,
            "eventId": result.get("id"),
            "eventLink": result.get("htmlLink"),
            "message": result.get("message"),
        }

    except Exception as e:
        log_error(f"❌ [CALENDAR_CREATE] Calendar creation error: {str(e)}")
        import traceback
        log_error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")