// Use Cloud Run backend URL, fall back to localhost for development
const BACKEND = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// Auto-detect user's timezone
function getUserTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch (e) {
    return 'America/New_York'; // Fallback
  }
}

export async function initSession(){
  const timezone = getUserTimezone();
  const res = await fetch(`${BACKEND}/api/voice/init`, { 
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ timezone })
  });
  if (!res.ok) throw new Error(`Failed to init session: ${res.status}`);
  return res.json();
}

export async function processTranscript(sessionId, transcript, audioBase64=null){
  const body = { sessionId, userTranscript: transcript };
  if (audioBase64) body.audio = audioBase64;
  const res = await fetch(`${BACKEND}/api/voice/process`, { 
    method: 'POST', 
    headers: {'Content-Type':'application/json'}, 
    body: JSON.stringify(body) 
  });
  if (!res.ok) throw new Error(`Failed to process transcript: ${res.status}`);
  return res.json();
}

export async function createEvent(sessionId, userDetails){
  const res = await fetch(`${BACKEND}/api/calendar/create`, { 
    method: 'POST', 
    headers: {'Content-Type':'application/json'}, 
    body: JSON.stringify({ sessionId, userDetails }) 
  });
  if (!res.ok) throw new Error(`Failed to create event: ${res.status}`);
  return res.json();
}

export async function getAuthUrl(){
  const res = await fetch(`${BACKEND}/auth/url`, { method: 'GET' });
  if (!res.ok) throw new Error(`Failed to get auth URL: ${res.status}`);
  return res.json();
}

export async function handleAuthCallback(sessionId, code){
  const res = await fetch(`${BACKEND}/auth/callback`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ sessionId, code })
  });
  if (!res.ok) throw new Error(`Failed to handle auth callback: ${res.status}`);
  return res.json();
}

export async function updateDetails(sessionId, patch){
  // Construct a Vapi-style tool call wrapper so the backend understands it
  // We strip 'sessionId' from 'patch' so it doesn't override the real session ID
  const { sessionId: ignored, ...safePatch } = patch;
  
  const payload = {
    message: {
      type: "tool-calls",
      toolCalls: [
        {
          id: "frontend-manual-call",
          type: "function",
          function: {
            name: "meeting_scheduler",
            arguments: {
              sessionId, 
              // If patch has userDetails, use it. Otherwise assume patch IS userDetails?
              // The tool definition says arguments has 'userDetails'.
              // Let's assume 'patch' is the arguments object from the tool call.
              ...safePatch
            }
          }
        }
      ]
    }
  };

  const res = await fetch(`${BACKEND}/api/voice/update`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(payload)
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
  
  // Parse the result string from Vapi tool response
  if (data?.results?.[0]?.result) {
    try {
      const resultStr = data.results[0].result;
      if (typeof resultStr === 'string') {
        return JSON.parse(resultStr);
      }
      return resultStr;
    } catch (e) {
      console.error('Failed to parse result:', e);
      return data;
    }
  }
  
  return data;
}