import { useState, useRef, useEffect, useCallback } from "react";
import Vapi from "@vapi-ai/web";
import * as api from "../services/api";

// Set to true to enable debug logging
const DEBUG = import.meta.env.DEV;
const log = (...args) => DEBUG && console.log(...args);
const logError = (...args) => console.error(...args);
const logWarn = (...args) => console.warn(...args);

/* ── Waveform Canvas ─────────────────────────────────────────────── */
function Waveform({ analyser, isActive, color, mirror }) {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width,
      H = canvas.height;
    const BAR_COUNT = 48;

    const drawIdle = () => {
      ctx.clearRect(0, 0, W, H);
      const barW = W / BAR_COUNT;
      for (let i = 0; i < BAR_COUNT; i++) {
        const x = i * barW + barW * 0.15;
        const h = 3;
        const y = H / 2 - h / 2;
        ctx.fillStyle = color + "55";
        ctx.beginPath();
        ctx.roundRect(x, y, barW * 0.7, h, 2);
        ctx.fill();
      }
    };

    const drawLive = () => {
      if (!analyser) {
        drawIdle();
        return;
      }
      const bufLen = analyser.frequencyBinCount;
      const data = new Uint8Array(bufLen);
      analyser.getByteFrequencyData(data);

      ctx.clearRect(0, 0, W, H);
      const barW = W / BAR_COUNT;
      const step = Math.floor(bufLen / BAR_COUNT);

      for (let i = 0; i < BAR_COUNT; i++) {
        const val = data[i * step] / 255;
        const minH = 3,
          maxH = H * 0.85;
        const h = minH + val * (maxH - minH);
        const x = i * barW + barW * 0.15;
        const y = H / 2 - h / 2;

        const grad = ctx.createLinearGradient(0, y, 0, y + h);
        grad.addColorStop(0, color + "cc");
        grad.addColorStop(0.5, color);
        grad.addColorStop(1, color + "cc");
        ctx.fillStyle = grad;
        ctx.shadowColor = color;
        ctx.shadowBlur = val * 8;
        ctx.beginPath();
        ctx.roundRect(x, y, barW * 0.7, h, 3);
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    };

    const animate = () => {
      if (isActive && analyser) drawLive();
      else if (isActive) {
        const t = Date.now() / 300;
        ctx.clearRect(0, 0, W, H);
        const barW = W / BAR_COUNT;
        for (let i = 0; i < BAR_COUNT; i++) {
          const val =
            (Math.sin(t + i * 0.4) * 0.5 + 0.5) *
            (Math.sin(t * 0.7 + i * 0.2) * 0.3 + 0.7);
          const minH = 3,
            maxH = H * 0.8;
          const h = minH + val * (maxH - minH);
          const x = i * barW + barW * 0.15;
          const y = H / 2 - h / 2;
          const grad = ctx.createLinearGradient(0, y, 0, y + h);
          grad.addColorStop(0, color + "88");
          grad.addColorStop(0.5, color);
          grad.addColorStop(1, color + "88");
          ctx.fillStyle = grad;
          ctx.shadowColor = color;
          ctx.shadowBlur = val * 6;
          ctx.beginPath();
          ctx.roundRect(x, y, barW * 0.7, h, 3);
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      } else {
        drawIdle();
      }
      rafRef.current = requestAnimationFrame(animate);
    };

    animate();
    return () => cancelAnimationFrame(rafRef.current);
  }, [isActive, analyser, color, mirror]);

  return (
    <canvas
      ref={canvasRef}
      width={280}
      height={60}
      style={{
        width: "100%",
        height: 60,
        display: "block",
        transform: mirror ? "scaleX(-1)" : "none",
      }}
    />
  );
}

/* ── Avatar Ring ─────────────────────────────────────────────── */
function AvatarRing({ label, emoji, color, isSpeaking }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, minWidth: 64 }}>
      <div
        style={{
          width: 52,
          height: 52,
          borderRadius: "50%",
          background: isSpeaking ? `radial-gradient(circle, ${color}33, ${color}11)` : "#1e293b",
          border: `2px solid ${isSpeaking ? color : "#334155"}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          position: "relative",
          boxShadow: isSpeaking ? `0 0 20px ${color}55, 0 0 40px ${color}22` : "none",
          transition: "all 0.35s ease",
        }}
      >
        {emoji}
        {isSpeaking && (
          <div
            style={{
              position: "absolute",
              inset: -5,
              borderRadius: "50%",
              border: `1.5px solid ${color}66`,
              animation: "ripple 1.5s ease-out infinite",
            }}
          />
        )}
        {isSpeaking && (
          <div
            style={{
              position: "absolute",
              inset: -11,
              borderRadius: "50%",
              border: `1px solid ${color}33`,
              animation: "ripple 1.5s 0.4s ease-out infinite",
            }}
          />
        )}
      </div>
      <span
        style={{
          fontSize: 11,
          fontWeight: 700,
          color: isSpeaking ? color : "#475569",
          letterSpacing: "0.06em",
          textTransform: "uppercase",
          transition: "color 0.3s",
        }}
      >
        {label}
      </span>
    </div>
  );
}

/* ── Transcript Bubble ───────────────────────────────────────────── */
function Bubble({ role, text, isLive }) {
  const isUser = role === "user";
  return (
    <div style={{ display: "flex", gap: 8, justifyContent: isUser ? "flex-end" : "flex-start", marginBottom: 10, animation: "slideUp 0.25s ease" }}>
      {!isUser && <span style={{ fontSize: 18, alignSelf: "flex-end", marginBottom: 2 }}>🤖</span>}
      <div
        style={{
          maxWidth: "75%",
          padding: "9px 13px",
          borderRadius: isUser ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
          background: isUser ? "linear-gradient(135deg,#7c3aed,#4f46e5)" : "#1e293b",
          color: "white",
          fontSize: 13.5,
          lineHeight: 1.55,
          boxShadow: isUser ? "0 4px 12px rgba(124,58,237,0.35)" : "0 2px 8px rgba(0,0,0,0.3)",
          border: isUser ? "none" : "1px solid #334155",
          position: "relative",
          whiteSpace: "pre-wrap",
        }}
      >
        {text}
        {isLive && (
          <span style={{ display: "inline-flex", gap: 3, marginLeft: 6, verticalAlign: "middle" }}>
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                style={{
                  width: 4,
                  height: 4,
                  background: "#94a3b8",
                  borderRadius: "50%",
                  display: "inline-block",
                  animation: `bounce 0.9s ${i * 0.15}s infinite`,
                }}
              />
            ))}
          </span>
        )}
      </div>
      {isUser && <span style={{ fontSize: 18, alignSelf: "flex-end", marginBottom: 2 }}>👤</span>}
    </div>
  );
}

/* ── Detail Pill ─────────────────────────────────────────────── */
function DetailPills({ details }) {
  const icons = { name: "👤", date: "📅", time: "🕐", duration: "⏱️", title: "📝" };
  const filled = Object.values(details).filter(Boolean).length;
  const total = Object.keys(details).length;

  return (
    <div style={{ padding: "10px 16px", borderTop: "1px solid #1e293b", background: "#0f172a" }}>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "center", marginBottom: 8 }}>
        {Object.entries(details).map(([k, v]) => (
          <div
            key={k}
            style={{
              padding: "4px 10px",
              borderRadius: 999,
              fontSize: 12,
              fontWeight: 600,
              background: v ? "#1e3a5f" : "#1e293b",
              border: `1px solid ${v ? "#3b82f6" : "#334155"}`,
              color: v ? "#7dd3fc" : "#475569",
              display: "flex",
              alignItems: "center",
              gap: 5,
              transition: "all 0.3s ease",
            }}
          >
            <span>{icons[k]}</span>
            <span>{v || k}</span>
            {v && <span style={{ color: "#10b981" }}>✓</span>}
          </div>
        ))}
      </div>
      <div style={{ height: 3, background: "#1e293b", borderRadius: 999, overflow: "hidden" }}>
        <div
          style={{
            height: "100%",
            width: `${(filled / total) * 100}%`,
            background: "linear-gradient(90deg,#3b82f6,#7c3aed)",
            borderRadius: 999,
            transition: "width 0.6s ease",
          }}
        />
      </div>
    </div>
  );
}

/* ── Main ───────────────────────────────────────────────────────── */
export default function VoiceScheduler() {
  const [phase, setPhase] = useState("idle");
  const [whoSpeaking, setWhoSpeaking] = useState(null);
  const [messages, setMessages] = useState([]);
  const [details, setDetails] = useState({ name: "", date: "", time: "", duration: "", title: "" });
  const [sessionId, setSessionId] = useState(null);

  const [analyser, setAnalyser] = useState(null);
  const [micError, setMicError] = useState("");
  const [isVapiConnected, setIsVapiConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(true);

  const micStreamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const chatEndRef = useRef(null);

  const vapiRef = useRef(null);
  const listenersAttachedRef = useRef(false);
  const startingRef = useRef(false);
  const activeCallRef = useRef(false);

  const creatingEventRef = useRef(false);

  // Draft bubbles
  const draftUserIdRef = useRef(null);
  const draftAiIdRef = useRef(null);
  // Session ref to access current sessionId inside listeners
  const sessionIdRef = useRef(sessionId);
  // Details ref for accessing in tool handlers
  const detailsRef = useRef(details);
  
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  useEffect(() => {
    detailsRef.current = details;
  }, [details]);

  // Ignore echoed assistant transcripts from injected messages
  const ignoreAiTranscriptRef = useRef({ text: "", until: 0 });

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const setupAnalyser = async () => {
    console.log("🔊 setupAnalyser: Initializing audio context...");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;

      const ctx = new AudioContext();
      audioCtxRef.current = ctx;

      const source = ctx.createMediaStreamSource(stream);
      const node = ctx.createAnalyser();
      node.fftSize = 256;
      source.connect(node);

      setAnalyser(node);
      console.log("✅ setupAnalyser: Audio context initialized.");
      return node;
    } catch (e) {
      console.error("❌ setupAnalyser error:", e);
      setMicError("Mic access denied — using simulated waveform.");
      return null;
    }
  };

  const upsertDraftMessage = useCallback((role, text, isFinal) => {
    // console.log(`📝 upsertDraftMessage: role=${role}, isFinal=${isFinal}, text="${text.substring(0, 30)}..."`);
    const idRef = role === "user" ? draftUserIdRef : draftAiIdRef;
    if (!idRef.current) idRef.current = crypto.randomUUID();
    const draftId = idRef.current;

    setMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === draftId);
      const next = [...prev];
      if (idx === -1) next.push({ id: draftId, role, text, isLive: !isFinal });
      else next[idx] = { ...next[idx], text, isLive: !isFinal };
      return next;
    });

    if (isFinal) {
        console.log(`📌 Draft message finalized for ${role}: "${text}"`);
        idRef.current = null;
    }
  }, []);

  const speakViaVapi = useCallback((text) => {
    console.log(`🗣️ speakViaVapi: "${text}"`);
    const vapi = vapiRef.current;
    if (!vapi || !text) {
        console.warn("⚠️ speakViaVapi: Vapi instance or text missing.");
        return;
    }

    ignoreAiTranscriptRef.current = { text, until: Date.now() + 2500 };

    try {
      vapi.send?.({
        type: "add-message",
        message: { role: "assistant", content: text },
      });
      console.log("✅ speakViaVapi: Message sent to Vapi.");
    } catch (e) {
      console.error("❌ speakViaVapi error:", e);
    }
  }, []);

  const isConfirmation = useCallback((text) => {
    const t = (text || "").toLowerCase();
    const result = [
      "correct",
      "confirm",
      "that's right",
      "that is right",
      "yes",
      "yeah",
      "yep",
      "ok",
      "okay",
      "sure",
      "go ahead",
      "create it",
    ].some((p) => t.includes(p));
    // console.log(`🔍 isConfirmation: "${t}" -> ${result}`);
    return result;
  }, []);

  /**
   * ✅ KEY FIX: processTranscript returns data; we use THAT immediately
   * to decide readiness, instead of waiting for React state updates.
   */
  const processUserText = useCallback(
    async (sid, userText) => {
      console.log(`🧠 processUserText: Processing "${userText}" for session ${sid}`);
      try {
        const data = await api.processTranscript(sid, userText);
        console.log("✅ processUserText output:", data);
        setDetails(data.userDetails || { name: "", date: "", time: "", duration: "", title: "" });
        return {
            userDetails: data.userDetails || { name: "", date: "", time: "", duration: "", title: "" },
            isReadyForEvent: Boolean(data.isReadyForEvent),
        };
      } catch (e) {
        console.error("❌ processUserText error:", e);
        throw e;
      }
    },
    []
  );

  /**
   * ✅ KEY FIX: no `isReadyForEvent` state gating (avoids race).
   * This function runs only when we *already have* readiness from backend.
   * Uses service account authentication (no OAuth needed).
   */
  const handleCreateEvent = useCallback(
    async (sid, readyDetails) => {
      console.log(`📅 handleCreateEvent: Creating event for session ${sid}`, readyDetails);
      if (!sid) return;
      if (creatingEventRef.current) {
        console.warn("⚠️ handleCreateEvent: Creation already in progress.");
        return;
      }

      creatingEventRef.current = true;

      try {
        setMicError("");

        // Don't add duplicate message - Vapi AI will naturally respond
        // Just create the event silently and show the result
        
        // Create event on backend (uses service account, no OAuth needed)
        const data = await api.createEvent(sid, readyDetails);
        console.log("✅ handleCreateEvent result:", data);

        if (data.success && data.eventId) {
          setPhase("done");

          const finalMsg = data.eventLink
            ? `✅ Event created in Google Calendar:\n${data.eventLink}`
            : "✅ Event created in Google Calendar.";

          setMessages((m) => [
            ...m,
            { role: "ai", text: finalMsg, id: crypto.randomUUID(), isLive: false },
          ]);

          // Let Vapi's natural response handle the speech - don't inject another message
          // speakViaVapi("Done — your Google Calendar event is created.");
        } else {
          console.error("❌ handleCreateEvent failed:", data);
          setMicError(data.detail || data.error || "Failed to create event");
          setMessages((m) => [
            ...m,
            { role: "ai", text: "I couldn't create the event. Please try again.", id: crypto.randomUUID(), isLive: false },
          ]);
        }
      } catch (e) {
        console.error("❌ handleCreateEvent exception:", e);
        setMicError(`Error creating event: ${e?.message || String(e)}`);
        setMessages((m) => [
          ...m,
          { role: "ai", text: `Error: ${e?.message || String(e)}`, id: crypto.randomUUID(), isLive: false },
        ]);
      } finally {
        creatingEventRef.current = false;
        console.log("🏁 handleCreateEvent: Finished.");
      }
    },
    [speakViaVapi]
  );
  
  const ensureVapi = useCallback(() => {
    console.log("🔌 ensureVapi: Checking Vapi initialization...");
    const publicKey = import.meta.env.VITE_VAPI_PUBLIC_KEY;
    if (!publicKey || publicKey === "YOUR_VAPI_PUBLIC_KEY") {
      console.error("❌ ensureVapi: Missing public key.");
      setMicError("Vapi public key not configured. Add VITE_VAPI_PUBLIC_KEY to .env.local");
      return null;
    }

    if (!vapiRef.current) {
        console.log("🆕 ensureVapi: Creating new Vapi instance.");
        vapiRef.current = new Vapi(publicKey);
    }
    const vapi = vapiRef.current;

    if (!listenersAttachedRef.current) {
      console.log("👂 ensureVapi: Attaching event listeners...");
      listenersAttachedRef.current = true;

      vapi.on("call-start", () => {
        console.log("📞 Vapi Event: call-start");
        activeCallRef.current = true;
        setIsVapiConnected(true);
        setWhoSpeaking(null);

        const currentDate = new Date().toISOString().split("T")[0];
        const currentSessionId = sessionIdRef.current;
        
        // Send both date and sessionId to Vapi so tool calls use the correct session
        vapi.send?.({
          type: "add-message",
          message: { 
            role: "system", 
            content: `Today's date is ${currentDate}. The sessionId for this conversation is: ${currentSessionId}. Always use this exact sessionId when calling tools.` 
          },
        });
        
        console.log(`📋 Vapi call started with sessionId: ${currentSessionId}`);

        try {
          vapi.setMuted(true);
          setIsMuted(true);
        } catch {}
      });

      vapi.on("call-end", () => {
        console.log("📞 Vapi Event: call-end");
        activeCallRef.current = false;
        setIsVapiConnected(false);
        setWhoSpeaking(null);
        setIsMuted(true);

        draftUserIdRef.current = null;
        draftAiIdRef.current = null;

        // If event creation is happening, don't spam call ended
        if (creatingEventRef.current) return;

        setPhase((p) => {
          if (p === "done") return p;
          setMessages((m) => [
            ...m,
            { id: crypto.randomUUID(), role: "ai", text: "Call ended. Tap Start Voice Session to try again.", isLive: false },
          ]);
          return p === "session" ? "idle" : p;
        });
      });

      vapi.on("speech-start", () => {
        console.log("🗣️ Vapi Event: speech-start (AI)");
        setWhoSpeaking("ai");
      });
      vapi.on("speech-end", () => {
        console.log("🤐 Vapi Event: speech-end (AI)");
        setWhoSpeaking(null);
      });

      vapi.on("message", async (message) => {
        // console.log("📩 Vapi Event: message", message.type);
        
        // Tool calls update details server-side
        if (message?.type === "tool-calls") {
          console.log("🔧 Vapi Tool Call received:", message);
          const calls = message.toolCalls || message.tool_calls || [];
          for (const call of calls) {
            const name = call?.name || call?.function?.name;
            const rawArgs = call?.arguments ?? call?.function?.arguments;

            let args = rawArgs;
            if (typeof rawArgs === "string") {
              try { args = JSON.parse(rawArgs); } catch { args = {}; }
            }
            
            console.log(`🛠️ Processing tool: ${name}`, args);

            if (name === "meeting_scheduler" && sessionIdRef.current) {
              try {
                // First, immediately update local state from args (in case backend fails)
                const argsDetails = args.userDetails || args;
                if (argsDetails && (argsDetails.name || argsDetails.date || argsDetails.time)) {
                  console.log("📝 Updating local details from tool args:", argsDetails);
                  setDetails(prev => ({
                    ...prev,
                    ...argsDetails,
                    name: argsDetails.name || prev.name || "",
                    date: argsDetails.date || prev.date || "",
                    time: argsDetails.time || prev.time || "",
                    duration: argsDetails.duration || prev.duration || "",
                    title: argsDetails.title || prev.title || "",
                  }));
                }
                
                // Also call backend to persist
                const data = await api.updateDetails(sessionIdRef.current, args);
                console.log("✅ Tool update success:", data);
                if (data.userDetails) {
                  setDetails(data.userDetails);
                }
              } catch (e) {
                console.error("❌ Tool update failed:", e);
                // Don't show error - we already updated local state from args
              }
            }
            
            // Handle explicit event creation tool call
            if (name === "create_event" && sessionIdRef.current) {
              console.log("📅 create_event tool called - creating event now!");
              const currentDetails = args.userDetails || detailsRef.current;
              if (currentDetails) {
                handleCreateEvent(sessionIdRef.current, currentDetails);
              }
            }
          }
          return;
        }

        if (message?.type !== "transcript") return;

        const role = message.role === "assistant" ? "ai" : "user";
        const text = message.transcript || "";
        if (!text.trim()) return;

        const isPartial =
          message.transcriptType === "partial" ||
          message.isPartial === true ||
          message.isFinal === false;
        const isFinal = !isPartial;

        // Ignore echoed transcript from injected speakViaVapi messages
        if (role === "ai" && isFinal) {
          const ig = ignoreAiTranscriptRef.current;
          const stillValid = Date.now() < ig.until;
          const matches = ig.text && (text.trim() === ig.text.trim() || text.trim().includes(ig.text.trim()));
          if (stillValid && matches) {
            console.log(`🙈 Ignoring echoed AI transcript: "${text}"`);
            return;
          }
        }

        upsertDraftMessage(role, text, isFinal);

        // Process user transcript and check for event creation trigger
        const currentSessionId = sessionIdRef.current;
        
        // Also trigger event creation when AI says "creating" and we have details
        if (role === "ai" && isFinal && currentSessionId) {
          const lowerText = text.toLowerCase();
          const aiCreating = lowerText.includes("creating") || lowerText.includes("i'll create") || lowerText.includes("i will create");
          const localDetails = detailsRef.current;
          const localReady = localDetails && localDetails.name && localDetails.date && localDetails.time;
          
          if (aiCreating && localReady && !creatingEventRef.current) {
            console.log("🚀 AI said creating and details ready - triggering event creation!");
            handleCreateEvent(currentSessionId, localDetails);
          }
        }
        
        if (role === "user" && isFinal && currentSessionId) {
          console.log(`👤 User final transcript: "${text}"`);
          
          // Check if user confirmed - use LOCAL details (from tool calls) not backend session
          // This avoids Cloud Run instance mismatch issues where tool calls hit different instances
          const userConfirmed = isConfirmation(text);
          const localDetails = detailsRef.current;
          const localReady = localDetails && localDetails.name && localDetails.date && localDetails.time;
          
          console.log(`📋 Local details check: ready=${localReady}, confirmed=${userConfirmed}`, localDetails);
          
          if (userConfirmed && localReady && !creatingEventRef.current) {
            console.log("🚀 User confirmed and local details ready - creating event!");
            handleCreateEvent(currentSessionId, localDetails);
          } else {
            // Still process transcript for non-confirmation messages (to update AI response)
            try {
              await processUserText(currentSessionId, text);
            } catch (e) {
              console.error("❌ Error processing transcript:", e);
            }
          }
        }
      });

      vapi.on("error", (err) => {
        console.error("❌ Vapi error raw:", err);
        const msg =
          err?.errorMsg ||
          err?.message ||
          err?.error?.msg ||
          err?.error?.message ||
          (err ? JSON.stringify(err, null, 2) : "Unknown error");
        setMicError(`Vapi error: ${msg}`);
        setWhoSpeaking(null);
      });
    }

    return vapi;
  }, [handleCreateEvent, isConfirmation, processUserText, sessionId, upsertDraftMessage]);

  useEffect(() => {
    return () => {
      if (!import.meta.env.DEV) {
        try { vapiRef.current?.stop?.(); } catch {}
      }
      vapiRef.current = null;
      listenersAttachedRef.current = false;
      activeCallRef.current = false;

      try { micStreamRef.current?.getTracks()?.forEach((t) => t.stop()); } catch {}
      micStreamRef.current = null;

      try { audioCtxRef.current?.close?.(); } catch {}
      audioCtxRef.current = null;
    };
  }, []);

  const handleStart = async () => {
    console.log("▶️ handleStart: Starting session...");
    if (startingRef.current) return;
    startingRef.current = true;

    try {
      setMicError("");
      await setupAnalyser();

      console.log("🌐 handleStart: Initializing backend session...");
      const init = await api.initSession();
      console.log("✅ handleStart: Session initialized:", init);
      
      // Set both state AND ref immediately so Vapi listeners can access it
      setSessionId(init.sessionId);
      sessionIdRef.current = init.sessionId;

      setPhase("session");

      const vapi = ensureVapi();
      if (!vapi) {
        console.warn("⚠️ handleStart: Vapi ensure failed.");
        setPhase("idle");
        return;
      }

      const assistantId = import.meta.env.VITE_VAPI_ASSISTANT_ID;
      if (!assistantId || assistantId === "YOUR_ASSISTANT_ID") {
        console.error("❌ handleStart: Missing Assistant ID.");
        setMicError("Vapi assistant ID not configured. Add VITE_VAPI_ASSISTANT_ID to .env.local");
        setPhase("idle");
        return;
      }

      console.log(`🚀 handleStart: Starting Vapi call with ID: ${assistantId}`);
      await vapi.start(assistantId);
    } catch (e) {
      console.error("❌ handleStart error:", e);
      setMicError(`Failed to start session: ${e?.message || String(e)}`);
      setPhase("idle");
    } finally {
      startingRef.current = false;
    }
  };

  const toggleVapiListening = useCallback(() => {
    console.log("🎤 toggleVapiListening invoked.");
    const vapi = vapiRef.current;
    if (!vapi) {
      setMicError("Vapi not initialized. Please restart the session.");
      return;
    }
    if (!isVapiConnected) return;

    try {
      const currentlyMuted = vapi.isMuted?.() ?? isMuted;
      const nextMuted = !currentlyMuted;
      console.log(`🔇 Toggling mute: ${currentlyMuted} -> ${nextMuted}`);
      vapi.setMuted?.(nextMuted);
      setIsMuted(nextMuted);
      setWhoSpeaking(nextMuted ? null : "user");
    } catch (e) {
      console.error("❌ toggleVapiListening error:", e);
      setMicError("Mute/unmute not supported.");
    }
  }, [isVapiConnected, isMuted]);

  const handleReset = () => {
    console.log("🔄 handleReset invoked.");
    try { vapiRef.current?.stop?.(); } catch {}
    activeCallRef.current = false;
    creatingEventRef.current = false;

    try { micStreamRef.current?.getTracks()?.forEach((t) => t.stop()); } catch {}
    micStreamRef.current = null;

    try { audioCtxRef.current?.close?.(); } catch {}
    audioCtxRef.current = null;

    draftUserIdRef.current = null;
    draftAiIdRef.current = null;

    setAnalyser(null);
    setPhase("idle");
    setWhoSpeaking(null);
    setMessages([]);
    setMicError("");
    setDetails({ name: "", date: "", time: "", duration: "", title: "" });
    setSessionId(null);
    setIsVapiConnected(false);
    setIsMuted(true);
  };

  const canListen = phase === "session" && isVapiConnected;

  return (
    <>
      <style>{`
        @keyframes ripple { 0%{opacity:1;transform:scale(1)} 100%{opacity:0;transform:scale(1.6)} }
        @keyframes bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-4px)} }
        @keyframes slideUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
        @keyframes glow { 0%,100%{box-shadow:0 0 20px #7c3aed44} 50%{box-shadow:0 0 40px #7c3aed99} }
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
      `}</style>

      <div
        style={{
          minHeight: "100vh",
          background: "radial-gradient(ellipse at 20% 50%, #1a0533 0%, #0a0a1a 40%, #000d1a 100%)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 20,
          fontFamily: "-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
        }}
      >
        <div style={{ width: "100%", maxWidth: 420 }}>
          <div style={{ textAlign: "center", marginBottom: 20 }}>
            <h1 style={{ color: "white", fontSize: 22, fontWeight: 800, margin: "0 0 4px", letterSpacing: -0.5 }}>
              🗓️ Voice AI Scheduler
            </h1>
          </div>

          <div
            style={{
              background: "#0d1117",
              borderRadius: 22,
              border: "1px solid #1e293b",
              boxShadow: "0 32px 80px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.05)",
              overflow: "hidden",
            }}
          >
            <div style={{ background: "linear-gradient(180deg,#0d0f1a 0%,#0a0c16 100%)", padding: "20px 16px 14px", borderBottom: "1px solid #1a2035" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <AvatarRing label="You" emoji="🎤" color="#7c3aed" isSpeaking={whoSpeaking === "user"} />

                <div style={{ flex: 1, position: "relative" }}>
                  <div style={{ opacity: whoSpeaking === "user" ? 1 : 0.3, transition: "opacity 0.4s" }}>
                    <Waveform analyser={whoSpeaking === "user" ? analyser : null} isActive={whoSpeaking === "user"} color="#7c3aed" />
                  </div>

                  {whoSpeaking === null && phase !== "idle" && (
                    <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <div style={{ width: "80%", height: 1.5, background: "linear-gradient(90deg,#7c3aed44,#1e40af44,#7c3aed44)" }} />
                    </div>
                  )}

                  <div style={{ opacity: whoSpeaking === "ai" ? 1 : 0.3, transition: "opacity 0.4s" }}>
                    <Waveform analyser={null} isActive={whoSpeaking === "ai"} color="#0ea5e9" mirror />
                  </div>
                </div>

                <AvatarRing label="Voice AI" emoji="🤖" color="#0ea5e9" isSpeaking={whoSpeaking === "ai"} />
              </div>

              <div style={{ textAlign: "center", marginTop: 10, height: 18 }}>
                {whoSpeaking === "user" && <span style={{ fontSize: 11, color: "#7c3aed", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>● Listening…</span>}
                {whoSpeaking === "ai" && <span style={{ fontSize: 11, color: "#0ea5e9", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>● AI Speaking…</span>}
                {whoSpeaking === null && phase === "session" && <span style={{ fontSize: 11, color: "#334155", letterSpacing: "0.06em" }}>Tap the mic to {isMuted ? "speak" : "stop"}</span>}
              </div>
            </div>

            <div style={{ height: 220, overflowY: "auto", padding: "14px 14px 6px", background: "#0d1117" }}>
              {messages.length === 0 && (
                <div style={{ height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", color: "#334155", gap: 10 }}>
                  <span style={{ fontSize: 36 }}>🎙️</span>
                  <p style={{ fontSize: 13, textAlign: "center", lineHeight: 1.5, margin: 0, maxWidth: 220 }}>
                    Start a session and speak naturally to schedule your meeting
                  </p>
                </div>
              )}

              {messages.map((m) => (
                <Bubble key={m.id} role={m.role} text={m.text} isLive={m.isLive} />
              ))}
              <div ref={chatEndRef} />
            </div>

            {Object.values(details).some(Boolean) && <DetailPills details={details} />}

            {micError && (
              <div style={{ padding: "8px 16px", background: "#1a0a0a", borderTop: "1px solid #3b1111", color: "#f87171", fontSize: 12, display: "flex", justifyContent: "space-between" }}>
                <span>⚠️ {micError}</span>
                <button onClick={() => setMicError("")} style={{ background: "none", border: "none", color: "#f87171", cursor: "pointer", fontSize: 14, padding: 0 }}>
                  ✕
                </button>
              </div>
            )}

            <div style={{ padding: "16px", background: "#090d13", borderTop: "1px solid #1e293b", display: "flex", flexDirection: "column", gap: 10 }}>
              {phase === "idle" && (
                <button
                  onClick={handleStart}
                  style={{
                    width: "100%",
                    padding: "14px",
                    borderRadius: 14,
                    border: "none",
                    background: "linear-gradient(135deg,#7c3aed,#4f46e5)",
                    color: "white",
                    fontWeight: 700,
                    fontSize: 15,
                    cursor: "pointer",
                    boxShadow: "0 6px 20px rgba(124,58,237,0.4)",
                    animation: "glow 2.5s ease-in-out infinite",
                  }}
                >
                  ✨ Schedule Meeting
                </button>
              )}

              {phase === "session" && (
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <button
                    onClick={toggleVapiListening}
                    disabled={!canListen}
                    style={{
                      width: 58,
                      height: 58,
                      borderRadius: "50%",
                      border: "2px solid",
                      borderColor: canListen ? "#7c3aed" : "#1e293b",
                      background:
                        !isMuted && whoSpeaking === "user"
                          ? "radial-gradient(circle,#7c3aed55,#7c3aed22)"
                          : canListen
                          ? "#1a1040"
                          : "#0d1117",
                      color: canListen ? "#a78bfa" : "#334155",
                      fontSize: 22,
                      cursor: canListen ? "pointer" : "not-allowed",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                      transition: "all 0.3s ease",
                      boxShadow:
                        !isMuted && whoSpeaking === "user"
                          ? "0 0 24px #7c3aed88"
                          : canListen
                          ? "0 0 12px #7c3aed33"
                          : "none",
                    }}
                    title={isMuted ? "Tap to talk" : "Tap to stop"}
                  >
                    {!isMuted ? "🔴" : "🎤"}
                  </button>

                  <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 8 }}>
                    <button
                      onClick={handleReset}
                      style={{
                        width: "100%",
                        padding: "9px",
                        borderRadius: 10,
                        border: "1px solid #1e293b",
                        background: "#0d1117",
                        color: "#475569",
                        fontWeight: 600,
                        fontSize: 13,
                        cursor: "pointer",
                        transition: "all 0.2s",
                      }}
                    >
                      ↺ Reset
                    </button>
                  </div>
                </div>
              )}

              {phase === "done" && (
                <div style={{ display: "flex", gap: 10 }}>
                  <div style={{ flex: 1, padding: "12px", borderRadius: 12, background: "#0a1f12", border: "1px solid #166534", color: "#4ade80", fontSize: 13, fontWeight: 600, textAlign: "center" }}>
                    🎉 Event Created!
                  </div>
                  <button
                    onClick={handleReset}
                    style={{
                      padding: "12px 20px",
                      borderRadius: 12,
                      border: "1px solid #1e293b",
                      background: "#0d1117",
                      color: "#475569",
                      fontWeight: 600,
                      fontSize: 13,
                      cursor: "pointer",
                    }}
                  >
                    ↺ New
                  </button>
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </>
  );
}
