import streamlit as st
import streamlit.components.v1 as components
import re
from datetime import datetime


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
    """
    Demo reply engine (NO AI model). Language matches user input.
    You can replace this with Groq/OpenAI later.
    """
    lang = detect_language(user_text)
    if lang == "ur":
        return (
            "جی! میں آپ کی مدد کے لیے حاضر ہوں۔\n\n"
            "آپ کیا جاننا چاہتے ہیں؟"
        )
    return (
        "Sure — I’m here to help.\n\n"
        "What would you like to know?"
    )


def now_time():
    return datetime.now().strftime("%H:%M")


# ---------------------------
# Session state
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of dicts: {role, content, time}

if "draft" not in st.session_state:
    st.session_state.draft = ""

if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""

if "voice_input" not in st.session_state:
    st.session_state.voice_input = ""


# ---------------------------
# Sidebar controls
# ---------------------------
st.sidebar.title("Settings")

auto_speak = st.sidebar.toggle("Auto-speak assistant reply", value=True)
voice_lang = st.sidebar.selectbox(
    "Voice input language",
    options=[
        "en-US",
        "en-GB",
        "ur-PK",
        "hi-IN",
    ],
    index=0,
    help="This controls browser speech recognition language.",
)

if st.sidebar.button("Clear chat", use_container_width=True):
    st.session_state.messages = []
    st.session_state.draft = ""
    st.session_state.voice_input = ""
    st.rerun()

st.sidebar.caption("Voice uses your browser STT/TTS. No API key required.")


# ---------------------------
# Global CSS (WhatsApp-like)
# ---------------------------
st.markdown(
    """
<style>
/* Make the main app full height */
html, body, [data-testid="stAppViewContainer"] {
  height: 100%;
}
[data-testid="stAppViewContainer"] {
  background: #efeae2;
}
[data-testid="stHeader"] {
  background: rgba(0,0,0,0);
}

/* Reduce default padding so chat can use full space */
.block-container {
  padding-top: 0.75rem !important;
  padding-bottom: 6.0rem !important; /* space for composer */
  max-width: 1200px;
}

/* Chat shell */
.chat-shell {
  width: 100%;
  height: calc(100vh - 10.5rem); /* adjust for header + sidebar */
  background: #efeae2;
  border-radius: 18px;
  padding: 12px 12px 16px 12px;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  border: 1px solid rgba(0,0,0,0.05);
}

/* Message rows */
.msg-row {
  display: flex;
  margin: 10px 0;
}
.msg-row.user {
  justify-content: flex-end;
}
.msg-row.bot {
  justify-content: flex-start;
}

/* Bubbles */
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
.bubble.user {
  background: #d9fdd3;
  border-top-right-radius: 6px;
}
.bubble.bot {
  background: #ffffff;
  border-top-left-radius: 6px;
}

/* Tiny time */
.time {
  display: block;
  margin-top: 6px;
  font-size: 0.72rem;
  opacity: 0.55;
  text-align: right;
}

/* Composer fixed at bottom */
.composer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
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

/* Make Streamlit input look like WhatsApp */
div[data-testid="stTextInput"] input {
  border-radius: 999px !important;
  padding: 0.70rem 1rem !important;
  border: 1px solid rgba(0,0,0,0.12) !important;
  background: #fff !important;
}
div[data-testid="stTextInput"] {
  margin-bottom: 0 !important;
}

/* Button style */
button[kind="primary"] {
  border-radius: 999px !important;
  height: 44px !important;
}
button[kind="secondary"] {
  border-radius: 999px !important;
  height: 44px !important;
}

/* Remove extra whitespace above components */
[data-testid="stVerticalBlock"] > div:has(.chat-shell) {
  margin-top: 0.25rem !important;
}

/* Mobile friendly */
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
  // auto-scroll to bottom
  const el = document.getElementById("chatShell");
  if (el) { el.scrollTop = el.scrollHeight; }
</script>
"""
)

st.markdown("\n".join(chat_html), unsafe_allow_html=True)


# ---------------------------
# Voice component (browser STT)
# Sends transcript to Streamlit using postMessage API
# ---------------------------
voice_component = f"""
<div style="display:flex;align-items:center;justify-content:center;">
  <script>
    const STREAMLIT_EVENT = "streamlit:setComponentValue";
    function sendToStreamlit(value) {{
      const msg = {{
        isStreamlitMessage: true,
        type: STREAMLIT_EVENT,
        value: value
      }};
      window.parent.postMessage(msg, "*");
    }}

    function startRecognition() {{
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {{
        alert("Speech recognition is not supported in this browser. Please use Chrome.");
        return;
      }}
      const recog = new SpeechRecognition();
      recog.lang = "{voice_lang}";
      recog.interimResults = false;
      recog.maxAlternatives = 1;

      recog.onresult = (event) => {{
        const transcript = event.results[0][0].transcript;
        sendToStreamlit(transcript);
      }};
      recog.onerror = (e) => {{
        console.log("SpeechRecognition error:", e);
      }};
      recog.start();
    }}
  </script>
</div>
"""

# We don't render this visibly here; we trigger it from the mic button below
voice_value = components.html(voice_component, height=0)


# If voice returned text, process it
if isinstance(voice_value, str) and voice_value.strip():
    st.session_state.voice_input = voice_value.strip()
    # Put transcript into draft and auto-send
    st.session_state.draft = st.session_state.voice_input
    st.session_state.voice_input = ""
    st.rerun()


# ---------------------------
# Send logic
# ---------------------------
def send_message(text: str):
    text = (text or "").strip()
    if not text:
        return

    st.session_state.messages.append(
        {"role": "user", "content": text, "time": now_time()}
    )

    reply = bot_reply(text)
    st.session_state.messages.append(
        {"role": "assistant", "content": reply, "time": now_time()}
    )
    st.session_state.last_spoken = reply

    st.session_state.draft = ""


# ---------------------------
# Composer fixed bottom (WhatsApp style)
# ---------------------------
st.markdown('<div class="composer"><div class="composer-inner">', unsafe_allow_html=True)

c1, c2, c3 = st.columns([8, 1, 1])

with c1:
    st.session_state.draft = st.text_input(
        "Message",
        value=st.session_state.draft,
        label_visibility="collapsed",
        placeholder="Type a message…",
    )

with c2:
    if st.button("🎤", help="Voice message", use_container_width=True):
        # Trigger speech recognition by re-rendering component and calling JS
        # We do it by injecting a tiny script that calls startRecognition().
        components.html(
            f"""
<script>
  // Find the function defined in the component and call it
  try {{
    // The function is in the same iframe scope where component is mounted.
    // We simply recreate it here and run.
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {{
      alert("Speech recognition is not supported in this browser. Please use Chrome.");
    }} else {{
      const recog = new SpeechRecognition();
      recog.lang = "{voice_lang}";
      recog.interimResults = false;
      recog.maxAlternatives = 1;
      recog.onresult = (event) => {{
        const transcript = event.results[0][0].transcript;
        const msg = {{
          isStreamlitMessage: true,
          type: "streamlit:setComponentValue",
          value: transcript
        }};
        window.parent.postMessage(msg, "*");
      }};
      recog.start();
    }}
  }} catch (e) {{
    console.log(e);
  }}
</script>
""",
            height=0,
        )

with c3:
    if st.button("➤", type="primary", help="Send", use_container_width=True):
        send_message(st.session_state.draft)
        st.rerun()

st.markdown("</div></div>", unsafe_allow_html=True)


# ---------------------------
# Auto-speak (browser TTS)
# ---------------------------
if auto_speak and st.session_state.last_spoken:
    safe_text = st.session_state.last_spoken.replace("\\", "\\\\").replace("`", "\\`")
    components.html(
        f"""
<script>
  try {{
    const msg = new SpeechSynthesisUtterance(`{safe_text}`);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(msg);
  }} catch (e) {{
    console.log(e);
  }}
</script>
""",
        height=0,
    )
    # prevent repeat on rerun
    st.session_state.last_spoken = ""
import streamlit as st
import numpy as np

st.subheader("Audio Debug")

# 1) Simple beep generator (1 sec 440Hz)
def make_beep(sr=22050, freq=440, duration=1.0):
    t = np.linspace(0, duration, int(sr*duration), endpoint=False)
    wave = (0.2*np.sin(2*np.pi*freq*t)).astype(np.float32)
    return wave, sr

if st.button("🔊 Play test beep"):
    wave, sr = make_beep()
    st.audio(wave, sample_rate=sr)
