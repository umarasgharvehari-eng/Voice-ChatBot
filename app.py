import os
import base64
import json
import re
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

# ---------------------------
# Config
# ---------------------------
st.set_page_config(
    page_title="FortisVoice • Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

URDU_RANGE_RE = re.compile(r"[\u0600-\u06FF]")

def now_time():
    return datetime.now().strftime("%H:%M")

def detect_language(text: str) -> str:
    if not text:
        return "en"
    return "ur" if URDU_RANGE_RE.search(text) else "en"

def get_groq_client():
    key = st.secrets.get("GROQ_API_KEY", None) if hasattr(st, "secrets") else None
    key = key or os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return Groq(api_key=key)

def groq_chat_reply(user_text: str, history):
    """
    history: list of {role: 'user'/'assistant', content: str}
    """
    client = get_groq_client()
    if client is None:
        return "⚠️ GROQ_API_KEY missing. Add it in Streamlit Secrets."

    # System prompt: bilingual + helpful
    system = (
        "You are FortisVoice, a helpful bilingual assistant (Urdu + English). "
        "Answer naturally, concise but helpful. If user uses Urdu, reply in Urdu. "
        "If user uses English, reply in English."
    )

    messages = [{"role": "system", "content": system}]

    # keep small memory window
    for m in history[-12:]:
        messages.append({"role": m["role"], "content": m["content"]})

    messages.append({"role": "user", "content": user_text})

    # Pick a Groq model
    # Good default: llama-3.1-8b-instant or llama-3.1-70b-versatile (slower)
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.6,
        max_tokens=500,
    )
    return resp.choices[0].message.content.strip()

def js_speak(text: str, lang: str):
    if not text:
        return
    safe = (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
        .replace("\n", "\\n")
    )
    components.html(
        f"""
<script>
try {{
  const u = new SpeechSynthesisUtterance(`{safe}`);
  u.lang = "{lang}";
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}} catch(e) {{
  console.log("TTS error:", e);
}}
</script>
""",
        height=0,
    )

# ---------------------------
# State
# ---------------------------
if "messages" not in st.session_state:
    # each: {role:'user'/'assistant', content:str, time:str, audio_b64:str|None, mime:str|None}
    st.session_state.messages = []

if "draft" not in st.session_state:
    st.session_state.draft = ""

if "last_assistant" not in st.session_state:
    st.session_state.last_assistant = ""

# ---------------------------
# Sidebar
# ---------------------------
st.sidebar.title("Settings")

tts_lang = st.sidebar.selectbox(
    "TTS language",
    ["en-US", "en-GB", "ur-PK", "hi-IN"],
    index=0,
)

if st.sidebar.button("🔊 Speak last reply", use_container_width=True):
    js_speak(st.session_state.last_assistant, tts_lang)

if st.sidebar.button("🧹 Clear chat", use_container_width=True):
    st.session_state.messages = []
    st.session_state.draft = ""
    st.session_state.last_assistant = ""
    st.rerun()

st.sidebar.caption("WhatsApp-style voice uses browser recorder.")
st.sidebar.caption("AI replies via Groq API (needs GROQ_API_KEY).")

# ---------------------------
# CSS (WhatsApp-ish)
# ---------------------------
st.markdown(
    """
<style>
html, body, [data-testid="stAppViewContainer"] { height: 100%; }
[data-testid="stAppViewContainer"] { background: #efeae2; }
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
.block-container {
  padding-top: 0.75rem !important;
  padding-bottom: 7rem !important;
  max-width: 1200px;
}
.composer {
  position: fixed; left: 0; right: 0; bottom: 0;
  z-index: 999;
  background: rgba(239,234,226,0.95);
  backdrop-filter: blur(8px);
  border-top: 1px solid rgba(0,0,0,0.08);
  padding: 10px 0;
}
.composer-inner { max-width: 1200px; margin: 0 auto; padding: 0 1rem; }
div[data-testid="stTextInput"] input {
  border-radius: 999px !important;
  padding: 0.70rem 1rem !important;
  border: 1px solid rgba(0,0,0,0.12) !important;
  background: #fff !important;
}
button[kind="primary"], button[kind="secondary"] {
  border-radius: 999px !important;
  height: 44px !important;
}
.voicebar {
  display:flex; gap:10px; align-items:center; justify-content:space-between;
  background:#fff; border:1px solid rgba(0,0,0,0.08);
  border-radius:999px; padding:10px 12px; margin-top:8px;
}
.vbtn {
  border:none; border-radius:999px; padding:10px 14px;
  cursor:pointer; font-weight:600;
}
.vbtn.rec { background:#ff3b30; color:white; }
.vbtn.stop { background:#111; color:white; }
.vbtn.send { background:#25D366; color:white; }
.vhint { font-size:0.85rem; opacity:0.7; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Header
# ---------------------------
st.markdown(
    """
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="width:38px;height:38px;border-radius:12px;background:#25D366;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">
      FV
    </div>
    <div>
      <div style="font-size:1.1rem;font-weight:700;">FortisVoice</div>
      <div style="font-size:0.85rem;opacity:0.65;">WhatsApp-style voice + Groq AI</div>
    </div>
  </div>
  <div style="font-size:0.85rem;opacity:0.6;">Streamlit • Browser recorder</div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Render chat
# ---------------------------
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        if m.get("content"):
            st.markdown(m["content"])

        # Voice bubble
        if m.get("audio_b64"):
            audio_bytes = base64.b64decode(m["audio_b64"])
            st.audio(audio_bytes, format=m.get("mime") or "audio/webm")

        st.caption(m.get("time", ""))

        if m["role"] == "assistant" and m.get("content"):
            if st.button("🔊 Speak", key=f"speak_{i}"):
                js_speak(m["content"], tts_lang)

# ---------------------------
# WhatsApp-style voice recorder component
# returns JSON:
#  {status:"idle"/"recording"/"ready", audio_b64:"...", mime:"audio/webm"}
# ---------------------------
voice_component_html = """
<div class="voicebar">
  <div class="vhint" id="hint">🎤 Press Record to start</div>
  <div style="display:flex;gap:8px;">
    <button class="vbtn rec" id="recBtn">Record</button>
    <button class="vbtn stop" id="stopBtn" disabled>Stop</button>
    <button class="vbtn send" id="sendBtn" disabled>Send</button>
  </div>
</div>

<script>
let mediaRecorder;
let chunks = [];
let lastBlob = null;
let lastMime = "audio/webm";

const hint = document.getElementById("hint");
const recBtn = document.getElementById("recBtn");
const stopBtn = document.getElementById("stopBtn");
const sendBtn = document.getElementById("sendBtn");

function toBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const dataUrl = reader.result;
      // data:audio/webm;base64,XXXX
      const b64 = dataUrl.split(",")[1];
      resolve(b64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

async function startRec() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const options = {};
    // try a preferred mime
    if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
      options.mimeType = "audio/webm;codecs=opus";
      lastMime = "audio/webm";
    } else if (MediaRecorder.isTypeSupported("audio/webm")) {
      options.mimeType = "audio/webm";
      lastMime = "audio/webm";
    } else {
      lastMime = "audio/webm";
    }

    mediaRecorder = new MediaRecorder(stream, options);
    chunks = [];

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      lastBlob = new Blob(chunks, { type: options.mimeType || "audio/webm" });
      hint.textContent = "✅ Recorded. Press Send.";
      sendBtn.disabled = false;
      // stop mic tracks
      stream.getTracks().forEach(t => t.stop());
    };

    mediaRecorder.start();
    hint.textContent = "🔴 Recording...";
    recBtn.disabled = true;
    stopBtn.disabled = false;
    sendBtn.disabled = true;
  } catch (e) {
    console.log(e);
    alert("Microphone permission denied or not available.");
  }
}

function stopRec() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
  }
  stopBtn.disabled = true;
  recBtn.disabled = false;
}

async function sendRec() {
  if (!lastBlob) return;
  const b64 = await toBase64(lastBlob);
  const payload = { status: "ready", audio_b64: b64, mime: lastMime };

  // Streamlit component value
  window.parent.postMessage(
    { isStreamlitMessage: true, type: "streamlit:setComponentValue", value: payload },
    "*"
  );

  // reset UI
  lastBlob = null;
  sendBtn.disabled = true;
  hint.textContent = "🎤 Press Record to start";
}

recBtn.addEventListener("click", startRec);
stopBtn.addEventListener("click", stopRec);
sendBtn.addEventListener("click", sendRec);
</script>
"""

voice_value = components.html(voice_component_html, height=70)

# If component returns a dict-like payload, Streamlit may deserialize as string; handle both.
payload = None
if isinstance(voice_value, dict):
    payload = voice_value
elif isinstance(voice_value, str) and voice_value.strip():
    # sometimes comes as JSON-like; try parse
    try:
        payload = json.loads(voice_value)
    except Exception:
        payload = None

# If voice payload received
if isinstance(payload, dict) and payload.get("status") == "ready" and payload.get("audio_b64"):
    st.session_state.messages.append({
        "role": "user",
        "content": "🎙️ Voice message",
        "time": now_time(),
        "audio_b64": payload["audio_b64"],
        "mime": payload.get("mime", "audio/webm"),
    })

    # Assistant response for voice message (no transcription yet)
    # If you want STT, we can add Whisper/Groq later.
    reply = "Voice message received ✅\n\nAap chahein to main isko transcribe bhi kar sakta hun (API se)."
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
        "time": now_time(),
        "audio_b64": None,
        "mime": None,
    })
    st.session_state.last_assistant = reply
    st.rerun()

# ---------------------------
# Composer (text)
# ---------------------------
st.markdown('<div class="composer"><div class="composer-inner">', unsafe_allow_html=True)

c1, c2 = st.columns([8, 1])

with c1:
    st.session_state.draft = st.text_input(
        "Message",
        value=st.session_state.draft,
        label_visibility="collapsed",
        placeholder="Type a message…",
    )

with c2:
    if st.button("➤", type="primary", use_container_width=True):
        text = (st.session_state.draft or "").strip()
        if text:
            st.session_state.messages.append({
                "role": "user",
                "content": text,
                "time": now_time(),
                "audio_b64": None,
                "mime": None,
            })

            # build chat history for Groq
            history = []
            for m in st.session_state.messages:
                if m["role"] in ("user", "assistant") and m.get("content"):
                    history.append({"role": m["role"], "content": m["content"]})

            reply = groq_chat_reply(text, history[:-1])
            st.session_state.messages.append({
                "role": "assistant",
                "content": reply,
                "time": now_time(),
                "audio_b64": None,
                "mime": None,
            })
            st.session_state.last_assistant = reply
            st.session_state.draft = ""
            st.rerun()

st.markdown("</div></div>", unsafe_allow_html=True)
