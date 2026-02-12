# app.py — FortisVoice (WhatsApp-style) Text + Voice (Browser STT/TTS)
# ✅ Fixes:
# - components.html() me key/return-value wali mistake removed
# - No postMessage to Streamlit component API (unregistered error removed)
# - Mic button (STT) runs in iframe and writes transcript into Streamlit text input
# - Speak button (TTS) runs in iframe on real click so browser usually allows audio

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
    if not text:
        return "en"
    return "ur" if URDU_RANGE_RE.search(text) else "en"


def bot_reply(user_text: str) -> str:
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
    st.session_state.messages = []

if "draft" not in st.session_state:
    st.session_state.draft = ""

if "last_reply" not in st.session_state:
    st.session_state.last_reply = ""


# ---------------------------
# Sidebar
# ---------------------------
st.sidebar.title("Settings")

voice_lang = st.sidebar.selectbox(
    "Voice input language",
    options=["en-US", "en-GB", "ur-PK", "hi-IN"],
    index=0,
    help="Browser speech recognition language.",
)

if st.sidebar.button("Clear chat", use_container_width=True):
    st.session_state.messages = []
    st.session_state.draft = ""
    st.session_state.last_reply = ""
    st.rerun()

st.sidebar.caption("Voice uses your browser STT/TTS. No API key required.")


# ---------------------------
# CSS
# ---------------------------
st.markdown(
    """
<style>
html, body, [data-testid="stAppViewContainer"] { height: 100%; }
[data-testid="stAppViewContainer"] { background: #efeae2; }
[data-testid="stHeader"] { background: rgba(0,0,0,0); }

.block-container {
  padding-top: 0.75rem !important;
  padding-bottom: 6.5rem !important;
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

button[kind="primary"] { border-radius: 999px !important; height: 44px !important; }

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
    chat_html.append(
        f"""
<div class="msg-row {role}">
  <div class="bubble {bubble_class}">
    {m["content"]}
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
    st.session_state.draft = ""


# ---------------------------
# Composer fixed bottom
# ---------------------------
st.markdown('<div class="composer"><div class="composer-inner">', unsafe_allow_html=True)

c1, c2, c3 = st.columns([8, 1, 1])

with c1:
    # IMPORTANT: label stays "Message" so JS can find it via aria-label
    st.session_state.draft = st.text_input(
        "Message",
        value=st.session_state.draft,
        label_visibility="collapsed",
        placeholder="Type a message…",
        key="fv_message_input",
    )

with c2:
    # This area will be replaced by HTML buttons (Mic + Speak) inside a component
    # We keep it empty so layout stays clean.
    st.write("")

with c3:
    if st.button("➤", type="primary", help="Send", use_container_width=True):
        send_message(st.session_state.draft)
        st.rerun()

st.markdown("</div></div>", unsafe_allow_html=True)

# ---------------------------
# Voice Controls (HTML buttons with real user clicks)
# - STT writes transcript into Streamlit input (parent DOM)
# - TTS speaks last reply
# ---------------------------
last_reply_safe = (st.session_state.last_reply or "").replace("\\", "\\\\").replace("`", "\\`")

voice_ui = f"""
<div style="position:fixed; left:0; right:0; bottom:58px; z-index:1000; display:flex; justify-content:center; pointer-events:none;">
  <div style="max-width:1200px; width:100%; padding:0 1rem; display:flex; gap:10px; justify-content:flex-end; pointer-events:auto;">
    <button id="fvMic"
      style="border:none; border-radius:999px; height:44px; width:44px; cursor:pointer; background:#ffffff; box-shadow:0 6px 18px rgba(0,0,0,0.10);">
      🎤
    </button>
    <button id="fvSpeak"
      style="border:none; border-radius:999px; height:44px; width:44px; cursor:pointer; background:#ffffff; box-shadow:0 6px 18px rgba(0,0,0,0.10);">
      🔊
    </button>
  </div>
</div>

<script>
(function() {{
  const VOICE_LANG = "{voice_lang}";
  const LAST_REPLY = `{last_reply_safe}`;

  function findStreamlitInput() {{
    // Streamlit text_input ends up as an <input> with aria-label equal to label
    // Even if label is collapsed, aria-label is usually kept.
    const doc = window.parent.document;
    let el = doc.querySelector('input[aria-label="Message"]');
    if (!el) {{
      // fallback: any visible text input
      el = doc.querySelector('div[data-testid="stTextInput"] input');
    }}
    return el;
  }}

  function setInputValue(val) {{
    const input = findStreamlitInput();
    if (!input) {{
      alert("Input box not found. Please refresh the page.");
      return;
    }}
    input.focus();
    input.value = val;

    // React/Streamlit needs events
    const ev1 = new Event('input', {{ bubbles: true }});
    const ev2 = new Event('change', {{ bubbles: true }});
    input.dispatchEvent(ev1);
    input.dispatchEvent(ev2);
  }}

  function startSTT() {{
    const SpeechRecognition = window.parent.SpeechRecognition || window.parent.webkitSpeechRecognition
      || window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {{
      alert("Speech Recognition not supported. Use Chrome on Desktop.");
      return;
    }}

    const recog = new SpeechRecognition();
    recog.lang = VOICE_LANG;
    recog.interimResults = false;
    recog.maxAlternatives = 1;

    recog.onresult = (event) => {{
      try {{
        const transcript = event.results[0][0].transcript || "";
        setInputValue(transcript);
      }} catch (e) {{
        console.log(e);
      }}
    }};
    recog.onerror = (e) => {{
      console.log("STT error:", e);
      alert("Voice error: " + (e && e.error ? e.error : "unknown"));
    }};

    try {{
      recog.start();
    }} catch (e) {{
      console.log(e);
      alert("Could not start mic. Try again.");
    }}
  }}

  function speakTTS() {{
    const synth = window.parent.speechSynthesis || window.speechSynthesis;
    if (!synth) {{
      alert("TTS not supported in this browser.");
      return;
    }}
    if (!LAST_REPLY || LAST_REPLY.trim().length === 0) {{
      alert("No assistant reply yet.");
      return;
    }}
    try {{
      const msg = new SpeechSynthesisUtterance(LAST_REPLY);
      synth.cancel();
      synth.speak(msg);
    }} catch (e) {{
      console.log("TTS error", e);
    }}
  }}

  const micBtn = document.getElementById("fvMic");
  const spkBtn = document.getElementById("fvSpeak");
  if (micBtn) micBtn.onclick = startSTT;
  if (spkBtn) spkBtn.onclick = speakTTS;
}})();
</script>
"""

# Render once; no key argument (Streamlit doesn't allow key here)
components.html(voice_ui, height=0)

# ---------------------------
# Audio Debug
# ---------------------------
st.subheader("Audio Debug")

def make_beep(sr=22050, freq=440, duration=1.0):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = (0.2 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    return wave, sr

if st.button("🔊 Play test beep"):
    wave, sr = make_beep()
    st.audio(wave, sample_rate=sr)
