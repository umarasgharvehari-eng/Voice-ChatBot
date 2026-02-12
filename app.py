# app.py — FortisVoice (WhatsApp-style) Text + Voice (Browser STT/TTS)
# ✅ Fixes:
# 1) “Received component message for unregistered ComponentInstance” by using ONE stable component iframe (stable key)
# 2) Mic click now triggers recognition inside the SAME component via a start counter (no new iframes on click)
# 3) TTS autoplay is unreliable in browsers (gesture policy), so added a “🔊 Speak” button that works reliably

import json
import re
from datetime import datetime

import numpy as np
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="FortisVoice • Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------
# Helpers
# ---------------------------
URDU_RANGE_RE = re.compile(r"[\u0600-\u06FF]")  # Arabic/Urdu unicode range


def detect_language(text: str) -> str:
    """Return 'ur' if Urdu/Arabic script detected else 'en'."""
    if not text:
        return "en"
    return "ur" if URDU_RANGE_RE.search(text) else "en"


def bot_reply(user_text: str) -> str:
    """Demo reply engine (NO AI model). Language matches user input."""
    lang = detect_language(user_text)
    if lang == "ur":
        return "جی! میں آپ کی مدد کے لیے حاضر ہوں۔\n\nآپ کیا جاننا چاہتے ہیں؟"
    return "Sure — I’m here to help.\n\nWhat would you like to know?"


def now_time():
    return datetime.now().strftime("%H:%M")


# ---------------------------
# Session state
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of dicts: {role, content, time}

if "draft" not in st.session_state:
    st.session_state.draft = ""

if "last_reply" not in st.session_state:
    st.session_state.last_reply = ""

if "tts_queue" not in st.session_state:
    st.session_state.tts_queue = ""  # text to speak

if "mic_start_count" not in st.session_state:
    st.session_state.mic_start_count = 0  # increment to trigger STT in component

if "last_transcript" not in st.session_state:
    st.session_state.last_transcript = ""


# ---------------------------
# Sidebar controls
# ---------------------------
st.sidebar.title("Settings")

auto_speak = st.sidebar.toggle("Auto-speak assistant reply (may be blocked by browser)", value=False)

voice_lang = st.sidebar.selectbox(
    "Voice input language",
    options=["en-US", "en-GB", "ur-PK", "hi-IN"],
    index=0,
    help="This controls browser speech recognition language.",
)

if st.sidebar.button("Clear chat", use_container_width=True):
    st.session_state.messages = []
    st.session_state.draft = ""
    st.session_state.last_reply = ""
    st.session_state.tts_queue = ""
    st.session_state.last_transcript = ""
    st.session_state.mic_start_count = 0
    st.rerun()

st.sidebar.caption("Voice uses your browser STT/TTS. No API key required.")


# ---------------------------
# Global CSS (WhatsApp-like)
# ---------------------------
st.markdown(
    """
<style>
html, body, [data-testid="stAppViewContainer"] { height: 100%; }
[data-testid="stAppViewContainer"] { background: #efeae2; }
[data-testid="stHeader"] { background: rgba(0,0,0,0); }

.block-container {
  padding-top: 0.75rem !important;
  padding-bottom: 6.0rem !important;
  max-width: 1200px;
}

.chat-shell {
  width: 100%;
  height: calc(100vh - 10.5rem);
  background: #efeae2;
  border-radius: 18px;
  padding: 12px 12px 16px 12px;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  border: 1px solid rgba(0,0,0,0.05);
}

.msg-row { display: flex; margin: 10px 0; }
.msg-row.user { justify-content: flex-end; }
.msg-row.bot  { justify-content: flex-start; }

.bubble {
  max-width: 72%;
  padding: 10px 12px;
  border-radius: 14px;
  line-height: 1.35;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.98rem;
  position: relative;
}
.bubble.user { background: #d9fdd3; border-top-right-radius: 6px; }
.bubble.bot  { background: #ffffff; border-top-left-radius: 6px; }

.time {
  display: block;
  margin-top: 6px;
  font-size: 0.72rem;
  opacity: 0.55;
  text-align: right;
}

.composer {
  position: fixed;
  left: 0; right: 0; bottom: 0;
  z-index: 999;
  background: rgba(239,234,226,0.92);
  backdrop-filter: blur(8px);
  border-top: 1px solid rgba(0,0,0,0.08);
  padding: 10px 0;
}
.composer-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

div[data-testid="stTextInput"] input {
  border-radius: 999px !important;
  padding: 0.70rem 1rem !important;
  border: 1px solid rgba(0,0,0,0.12) !important;
  background: #fff !important;
}
div[data-testid="stTextInput"] { margin-bottom: 0 !important; }

button[kind="primary"], button[kind="secondary"] {
  border-radius: 999px !important;
  height: 44px !important;
}

@media (max-width: 768px) {
  .block-container { max-width: 100% !important; }
  .bubble { max-width: 86%; }
  .chat-shell { height: calc(100vh - 12rem); border-radius: 14px; }
}
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
      <div style="font-size:0.85rem;opacity:0.65;">WhatsApp-style text + voice</div>
    </div>
  </div>
  <div style="font-size:0.85rem;opacity:0.6;">Browser STT/TTS • Streamlit</div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Chat rendering
# ---------------------------
chat_html = ['<div class="chat-shell" id="chatShell">']
for m in st.session_state.messages:
    role = "user" if m["role"] == "user" else "bot"
    bubble_class = "user" if role == "user" else "bot"
    content = m["content"]
    chat_html.append(
        f"""
<div class="msg-row {role}">
  <div class="bubble {bubble_class}">
    {content}
    <span class="time">{m["time"]}</span>
  </div>
</div>
"""
    )
chat_html.append("</div>")
chat_html.append(
    """
<script>
  const el = document.getElementById("chatShell");
  if (el) { el.scrollTop = el.scrollHeight; }
</script>
"""
)
st.markdown("\n".join(chat_html), unsafe_allow_html=True)

# ---------------------------
# Voice STT component (SINGLE stable iframe)
# Triggered by mic_start_count changes
# ---------------------------
stt_payload = {
    "lang": voice_lang,
    "startCount": st.session_state.mic_start_count,
}
stt_payload_json = json.dumps(stt_payload)

voice_component_html = f"""
<div>
<script>
(function() {{
  const payload = {stt_payload_json};
  const STREAMLIT_EVENT = "streamlit:setComponentValue";

  function sendToStreamlit(value) {{
    window.parent.postMessage({{
      isStreamlitMessage: true,
      type: STREAMLIT_EVENT,
      value: value
    }}, "*");
  }}

  function startRecognition() {{
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {{
      sendToStreamlit("__STT_ERROR__:Speech recognition not supported (use Chrome).");
      return;
    }}

    const recog = new SpeechRecognition();
    recog.lang = payload.lang || "en-US";
    recog.interimResults = false;
    recog.maxAlternatives = 1;

    recog.onresult = (event) => {{
      try {{
        const transcript = event.results[0][0].transcript || "";
        sendToStreamlit(transcript);
      }} catch (e) {{
        sendToStreamlit("__STT_ERROR__:Could not read transcript");
      }}
    }};

    recog.onerror = (e) => {{
      sendToStreamlit("__STT_ERROR__:" + (e && e.error ? e.error : "unknown"));
    }};

    try {{
      recog.start();
    }} catch (e) {{
      // Sometimes start() throws if called too quickly
      sendToStreamlit("__STT_ERROR__:start_failed");
    }}
  }}

  // Use localStorage to remember last startCount for this browser tab.
  const key = "fv_lastStartCount";
  const last = Number(localStorage.getItem(key) || "0");
  if (payload.startCount > last) {{
    localStorage.setItem(key, String(payload.startCount));
    startRecognition();
  }}
}})();
</script>
</div>
"""

# IMPORTANT: stable key => prevents “unregistered ComponentInstance”
voice_value = components.html(voice_component_html, height=0, key="fv_stt_component")

# If voice returned text, process it
if isinstance(voice_value, str) and voice_value.strip():
    txt = voice_value.strip()
    if txt.startswith("__STT_ERROR__"):
        # show error to user (non-fatal)
        st.toast(f"Voice error: {txt.replace('__STT_ERROR__:', '')}", icon="⚠️")
    else:
        st.session_state.last_transcript = txt
        st.session_state.draft = txt  # put in input box
    # clear component value loop by rerun
    st.rerun()


# ---------------------------
# Send logic
# ---------------------------
def send_message(text: str):
    text = (text or "").strip()
    if not text:
        return

    st.session_state.messages.append({"role": "user", "content": text, "time": now_time()})

    reply = bot_reply(text)
    st.session_state.messages.append({"role": "assistant", "content": reply, "time": now_time()})

    st.session_state.last_reply = reply

    # optional auto-speak (may be blocked). We'll queue it.
    if auto_speak:
        st.session_state.tts_queue = reply

    st.session_state.draft = ""


# ---------------------------
# Composer fixed bottom
# ---------------------------
st.markdown('<div class="composer"><div class="composer-inner">', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns([7, 1, 1, 1])

with c1:
    st.session_state.draft = st.text_input(
        "Message",
        value=st.session_state.draft,
        label_visibility="collapsed",
        placeholder="Type a message…",
        key="fv_text_input",
    )

with c2:
    if st.button("🎤", help="Voice input (STT)", use_container_width=True):
        # Increment counter => component will start recognition
        st.session_state.mic_start_count += 1
        st.rerun()

with c3:
    if st.button("➤", type="primary", help="Send", use_container_width=True):
        send_message(st.session_state.draft)
        st.rerun()

with c4:
    # Reliable TTS: user gesture button (browser allows speechSynthesis)
    if st.button("🔊", help="Speak last assistant reply", use_container_width=True):
        if st.session_state.last_reply:
            st.session_state.tts_queue = st.session_state.last_reply
        st.rerun()

st.markdown("</div></div>", unsafe_allow_html=True)


# ---------------------------
# TTS (Browser speechSynthesis)
# NOTE: Autoplay may be blocked; the 🔊 button works best.
# ---------------------------
if st.session_state.tts_queue:
    tts_text = st.session_state.tts_queue
    # Safe JS string via JSON
    tts_text_js = json.dumps(tts_text)

    components.html(
        f"""
<script>
(function() {{
  try {{
    const text = {tts_text_js};
    const msg = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(msg);
  }} catch (e) {{
    console.log("TTS error", e);
  }}
}})();
</script>
""",
        height=0,
        key=f"fv_tts_{hash(tts_text)}",
    )
    # prevent repeat on rerun
    st.session_state.tts_queue = ""


# ---------------------------
# Audio Debug
# ---------------------------
st.subheader("Audio Debug")

def make_beep(sr=22050, freq=440, duration=1.0):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = (0.2 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    return wave, sr

if st.button("🔊 Play test beep", key="fv_beep_btn"):
    wave, sr = make_beep()
    st.audio(wave, sample_rate=sr)

if st.session_state.last_transcript:
    st.caption(f"Last transcript: {st.session_state.last_transcript}")
