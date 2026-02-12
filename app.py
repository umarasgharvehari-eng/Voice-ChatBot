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
    """Demo reply engine (NO AI model)."""
    lang = detect_language(user_text)
    if lang == "ur":
        return "جی! میں آپ کی مدد کے لیے حاضر ہوں۔\n\nآپ کیا جاننا چاہتے ہیں؟"
    return "Sure — I’m here to help.\n\nWhat would you like to know?"


def now_time() -> str:
    return datetime.now().strftime("%H:%M")


def js_speak(text: str, lang: str = "en-US", rate: float = 1.0):
    """
    Speak via browser TTS. Works best when triggered by a user click.
    """
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
  const t = `{safe}`;
  const u = new SpeechSynthesisUtterance(t);
  u.lang = "{lang}";
  u.rate = {rate};
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}} catch (e) {{
  console.log("TTS error:", e);
}}
</script>
""",
        height=0,
    )


# ---------------------------
# Session state
# ---------------------------
if "messages" not in st.session_state:
    # each message: {role: "user"/"assistant", text: str, time: str, audio: bytes|None}
    st.session_state.messages = []

if "draft" not in st.session_state:
    st.session_state.draft = ""

if "last_assistant_text" not in st.session_state:
    st.session_state.last_assistant_text = ""

# ---------------------------
# Sidebar
# ---------------------------
st.sidebar.title("Settings")

tts_lang = st.sidebar.selectbox(
    "TTS voice language",
    options=["en-US", "en-GB", "ur-PK", "hi-IN"],
    index=0,
    help="This controls browser text-to-speech voice language.",
)

if st.sidebar.button("🔊 Speak last reply", use_container_width=True):
    js_speak(st.session_state.last_assistant_text, lang=tts_lang)

if st.sidebar.button("Clear chat", use_container_width=True):
    st.session_state.messages = []
    st.session_state.draft = ""
    st.session_state.last_assistant_text = ""
    st.rerun()

st.sidebar.caption("Voice notes use Streamlit audio recorder (reliable on Cloud).")
st.sidebar.caption("TTS may require user click due to browser autoplay policies.")

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
  padding-bottom: 7rem !important; /* room for composer */
  max-width: 1200px;
}
.chat-wrap {
  background: #efeae2;
  border-radius: 18px;
  padding: 10px 10px 14px 10px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  border: 1px solid rgba(0,0,0,0.05);
}
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
      <div style="font-size:0.85rem;opacity:0.65;">WhatsApp-style text + voice notes</div>
    </div>
  </div>
  <div style="font-size:0.85rem;opacity:0.6;">Streamlit Cloud • No Bokeh</div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Chat rendering
# ---------------------------
st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)

for i, m in enumerate(st.session_state.messages):
    role = m["role"]
    # Streamlit roles: "user" / "assistant"
    with st.chat_message(role):
        if m.get("text"):
            st.markdown(m["text"])
        if m.get("audio"):
            # voice note playback
            st.audio(m["audio"])
        st.markdown(f'<span class="time">{m["time"]}</span>', unsafe_allow_html=True)

        # Speak button only for assistant messages
        if role == "assistant" and m.get("text"):
            col_a, col_b = st.columns([1, 5])
            with col_a:
                if st.button("🔊 Speak", key=f"speak_{i}"):
                    js_speak(m["text"], lang=tts_lang)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Send logic
# ---------------------------
def send_text_message(text: str):
    text = (text or "").strip()
    if not text:
        return

    st.session_state.messages.append(
        {"role": "user", "text": text, "time": now_time(), "audio": None}
    )

    reply = bot_reply(text)
    st.session_state.messages.append(
        {"role": "assistant", "text": reply, "time": now_time(), "audio": None}
    )
    st.session_state.last_assistant_text = reply
    st.session_state.draft = ""


def send_voice_note(audio_bytes: bytes):
    if not audio_bytes:
        return

    st.session_state.messages.append(
        {"role": "user", "text": "🎙️ Voice note", "time": now_time(), "audio": audio_bytes}
    )

    # Simple demo assistant reply when voice note received
    reply = "I received your voice note ✅\n\n(If you want, I can transcribe it using an API later.)"
    st.session_state.messages.append(
        {"role": "assistant", "text": reply, "time": now_time(), "audio": None}
    )
    st.session_state.last_assistant_text = reply


# ---------------------------
# Composer (fixed bottom)
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
    if st.button("➤", type="primary", help="Send", use_container_width=True):
        send_text_message(st.session_state.draft)
        st.rerun()

# Voice recorder row (reliable)
st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
audio = st.audio_input("🎤 Record a voice note", label_visibility="visible")
if audio is not None:
    # audio is an UploadedFile-like object
    audio_bytes = audio.getvalue()
    send_voice_note(audio_bytes)
    st.rerun()

st.markdown("</div></div>", unsafe_allow_html=True)
