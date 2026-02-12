import re
import streamlit as st

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="FortisVoice • Voice Chatbot",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- Styling (Fix spacing + better chat area) ----------------
st.markdown(
    """
<style>
/* Wider app + better padding */
.block-container { padding-top: 1.1rem; padding-bottom: 2rem; }

/* Make the main column wider and give chat a clean card */
.chat-wrap{
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.03);
  border-radius: 18px;
  padding: 14px 14px;
}

/* Header */
.header-card{
  border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(16,185,129,0.10));
  padding: 16px 16px;
  border-radius: 18px;
  margin-bottom: 12px;
}
.header-title{ font-size: 1.45rem; font-weight: 800; margin: 0; }
.header-sub{ margin: 6px 0 0 0; opacity: 0.85; }

/* Chat messages */
.stChatMessage { border-radius: 16px; }
.small-muted { opacity: 0.75; font-size: 0.92rem; }

/* Buttons */
div.stButton > button, div.stDownloadButton > button {
  border-radius: 12px !important;
  padding: 0.55rem 0.9rem !important;
}

/* Speak section spacing */
.speak-card{
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.02);
  border-radius: 18px;
  padding: 12px 14px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- Language detection (simple + practical) ----------------
URDU_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")  # Arabic/Urdu script

def detect_lang(text: str) -> str:
    """
    Returns: 'ur' if Urdu/Arabic script found OR roman-urdu keywords dominate; else 'en'
    """
    t = (text or "").strip()
    if not t:
        return "en"
    if URDU_ARABIC_RE.search(t):
        return "ur"
    tl = t.lower()
    roman_urdu_markers = ["bhai", "mujhe", "kya", "hain", "hai", "nahi", "kar", "kr", "chahiye", "banao", "ban", "please", "aoa", "salam"]
    score = sum(1 for w in roman_urdu_markers if w in tl)
    return "ur" if score >= 2 else "en"

# ---------------- Rule-based Bot (Bilingual, no model/no API key) ----------------
def bot_reply(text: str) -> str:
    lang = detect_lang(text)
    t = (text or "").strip()
    tl = t.lower()

    if not t:
        return "Mujhe aapki awaz clear nahi mili. Dobara bol dein." if lang == "ur" else "I didn’t catch that clearly. Please say it again."

    # Greetings
    if any(x in tl for x in ["assalam", "asalam", "salam", "aoa", "hello", "hi", "hey"]):
        return "Wa alaikum assalam! Batao bhai, kis cheez mein help chahiye?" if lang == "ur" else "Hi! How can I help you today?"

    # Streamlit / deploy
    if "streamlit" in tl and any(x in tl for x in ["deploy", "deployment", "host", "publish"]):
        return (
            "Streamlit deploy ke liye: app.py aur requirements.txt GitHub repo mein push karo, phir Streamlit Community Cloud se deploy kar do."
            if lang == "ur"
            else
            "To deploy on Streamlit: push app.py and requirements.txt to a GitHub repo, then deploy it on Streamlit Community Cloud."
        )

    # Colab networking
    if any(x in tl for x in ["colab", "google colab"]):
        return (
            "Colab mein Streamlit direct IP se open nahi hota. Tunnel (Cloudflare/localtunnel) use karo, ya best: GitHub + Streamlit Cloud."
            if lang == "ur"
            else
            "In Colab, you can’t open Streamlit via direct IP. Use a tunnel (Cloudflare/localtunnel) or the best option: GitHub + Streamlit Cloud."
        )

    # Voice without API key
    if any(x in tl for x in ["without api", "no api", "without key", "no key", "without model", "no model", "api key"]):
        return (
            "Voice input/output bina API key ke possible hai (browser Web Speech API). Lekin real AI chat ke liye model/API chahiye hota hai. Rule-based bot chal sakta hai."
            if lang == "ur"
            else
            "You can do voice input/output without an API key using the browser’s Web Speech API. But real AI chat needs a model/API. A rule-based bot can work without it."
        )

    # Default fallback
    return (
        f"Main ne suna: “{t}”. Ab batao—tumhein short answer chahiye ya detailed steps?"
        if lang == "ur"
        else
        f"I heard: “{t}”. Do you want a quick answer or detailed steps?"
    )

# ---------------- Session State ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_incoming" not in st.session_state:
    st.session_state.last_incoming = ""
if "auto_speak" not in st.session_state:
    st.session_state.auto_speak = True

# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.session_state.auto_speak = st.toggle("Auto-speak assistant reply", value=st.session_state.auto_speak)

    recog_lang = st.selectbox(
        "Speech Recognition Language",
        ["en-US", "en-GB", "ur-PK (if supported)"],
        index=0,
        help="Browser support varies. If ur-PK doesn't work, use en-US/en-GB.",
    )
    recog_lang = "ur-PK" if recog_lang.startswith("ur-PK") else recog_lang

    st.markdown("---")
    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_incoming = ""
        st.rerun()

    st.markdown("---")
    st.caption("✅ No API Key • ✅ No AI Model • ✅ Browser STT/TTS")

# ---------------- Header ----------------
st.markdown(
    """
<div class="header-card">
  <p class="header-title">🎙️ FortisVoice</p>
  <p class="header-sub">Professional chat layout + bilingual replies (English ↔ Urdu). Voice via Web Speech API.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------- Layout: Chat (left) + Speak (right) ----------------
left, right = st.columns([2.2, 1.0], gap="large")

# ---------- Mic component (top of chat) ----------
mic_component = f"""
<div style="display:flex; gap:10px; align-items:center; margin: 2px 0 10px 0;">
  <button id="startBtn" style="padding:10px 14px; border-radius:12px; border:1px solid rgba(0,0,0,0.15); cursor:pointer;">
    🎤 Start
  </button>
  <button id="stopBtn" style="padding:10px 14px; border-radius:12px; border:1px solid rgba(0,0,0,0.15); cursor:pointer;" disabled>
    ⏹ Stop
  </button>
  <span id="status" style="font-family: system-ui; opacity:0.75;"></span>
</div>

<script>
(function(){{
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const statusEl = document.getElementById("status");
  const startBtn = document.getElementById("startBtn");
  const stopBtn  = document.getElementById("stopBtn");

  if (!SpeechRecognition) {{
    statusEl.textContent = "❌ SpeechRecognition not supported. Use Chrome.";
    startBtn.disabled = true;
    return;
  }}

  let recog = new SpeechRecognition();
  recog.lang = "{recog_lang}";
  recog.interimResults = true;
  recog.continuous = false;

  let finalText = "";
  let lastInterim = "";

  function setUI(listening) {{
    startBtn.disabled = listening;
    stopBtn.disabled = !listening;
  }}

  recog.onstart = () => {{
    finalText = "";
    lastInterim = "";
    statusEl.textContent = "Listening...";
    setUI(true);
  }};

  recog.onresult = (event) => {{
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {{
      const chunk = event.results[i][0].transcript;
      if (event.results[i].isFinal) finalText += chunk;
      else interim += chunk;
    }}
    if (interim && interim !== lastInterim) {{
      lastInterim = interim;
      statusEl.textContent = "…" + interim;
    }}
  }};

  recog.onerror = (e) => {{
    statusEl.textContent = "❌ Error: " + e.error;
    setUI(false);
  }};

  recog.onend = () => {{
    setUI(false);
    const text = (finalText || "").trim();
    if (text.length > 0) {{
      const base = window.location.origin + window.location.pathname;
      const t = encodeURIComponent(text);
      window.location.href = base + "?t=" + t + "&_ts=" + Date.now();
    }} else {{
      statusEl.textContent = "Stopped.";
    }}
  }};

  startBtn.onclick = () => {{
    try {{ recog.start(); }} catch (e) {{ statusEl.textContent = "❌ Could not start mic."; }}
  }};
  stopBtn.onclick = () => {{
    try {{ recog.stop(); }} catch (e) {{}}
  }};
}})();
</script>
"""

def add_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})

# Read transcript from query params
qp = st.query_params
incoming = qp.get("t", "")

if incoming and incoming != st.session_state.last_incoming:
    st.session_state.last_incoming = incoming
    add_message("user", incoming)
    add_message("assistant", bot_reply(incoming))

with left:
    st.markdown("### 💬 Chat")
    st.components.v1.html(mic_component, height=85)

    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    if not st.session_state.messages:
        st.markdown(
            '<div class="small-muted">Tip: 🎤 Start dabao aur bol kar message bhejo. Ya neeche type karo.</div>',
            unsafe_allow_html=True,
        )

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])
    st.markdown("</div>", unsafe_allow_html=True)

    # Text input (fallback)
    user_text = st.chat_input("Type a message (fallback)...")
    if user_text:
        add_message("user", user_text)
        add_message("assistant", bot_reply(user_text))
        st.rerun()

# Speak card
with right:
    st.markdown("### 🔊 Speak")
    st.markdown('<div class="speak-card">', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Browser TTS (SpeechSynthesis). Works best on Chrome.</div>', unsafe_allow_html=True)

    last_assistant = ""
    for m in reversed(st.session_state.messages):
        if m["role"] == "assistant":
            last_assistant = m["content"]
            break

    speak_btn = f"""
<button style="margin-top:10px; padding:10px 14px; border-radius:12px; border:1px solid rgba(0,0,0,0.15); cursor:pointer; width:100%;"
onclick="
  const txt = {last_assistant!r};
  if (!txt) return;
  const msg = new SpeechSynthesisUtterance(txt);
  msg.rate = 1.0; msg.pitch = 1.0;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(msg);
">
🔊 Speak last reply
</button>
"""
    st.components.v1.html(speak_btn, height=80)

    st.markdown("---")
    st.markdown(
        '<div class="small-muted">Language auto-detect: English question → English reply. Urdu/Roman-Urdu → Urdu reply.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Auto-speak on new assistant reply (best effort)
if st.session_state.auto_speak and incoming:
    last_assistant = ""
    for m in reversed(st.session_state.messages):
        if m["role"] == "assistant":
            last_assistant = m["content"]
            break
    if last_assistant:
        st.components.v1.html(
            f"""
<script>
setTimeout(() => {{
  const txt = {last_assistant!r};
  if (!txt) return;
  const msg = new SpeechSynthesisUtterance(txt);
  msg.rate = 1.0; msg.pitch = 1.0;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(msg);
}}, 450);
</script>
""",
            height=0,
        )
