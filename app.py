import streamlit as st
import time

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="FortisVoice • Voice Chatbot",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------- Styling (Professional UI) ----------------
st.markdown(
    """
<style>
/* App background + typography */
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 900px; }
h1, h2, h3 { letter-spacing: -0.02em; }
.small-muted { opacity: 0.75; font-size: 0.92rem; }

/* Header card */
.header-card{
  border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(16,185,129,0.10));
  padding: 16px 16px;
  border-radius: 16px;
  margin-bottom: 14px;
}
.header-title{ font-size: 1.35rem; font-weight: 700; margin: 0; }
.header-sub{ margin: 6px 0 0 0; opacity: 0.85; }

/* Chat bubbles spacing */
.stChatMessage { border-radius: 16px; }

/* Buttons */
div.stButton > button, div.stDownloadButton > button {
  border-radius: 12px !important;
  padding: 0.55rem 0.9rem !important;
}

/* Sidebar section titles */
.sidebar-title { font-weight: 700; margin: 0.25rem 0 0.4rem 0; }

/* Pills */
.pill {
  display:inline-block; padding:6px 10px; border-radius:999px;
  border:1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.04);
  font-size: 0.85rem; opacity: 0.9;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- Rule-based Bot (No Model, No API Key) ----------------
def rule_bot(text: str) -> str:
    t = (text or "").strip()
    tl = t.lower()

    if not t:
        return "Mujhe aapki awaz clear nahi mili. Dobara bol dein."

    # Greetings
    if any(x in tl for x in ["assalam", "asalam", "salam", "aoa", "hello", "hi", "hey"]):
        return "Wa alaikum assalam! Batao bhai, kis cheez mein help chahiye?"

    # Basic intents
    if any(x in tl for x in ["your name", "name kya", "name"]):
        return "Mera naam FortisVoice hai."

    if "streamlit" in tl and any(x in tl for x in ["deploy", "deployment", "host", "publish"]):
        return (
            "Streamlit deploy ke liye: app.py aur requirements.txt GitHub repo mein push karo, "
            "phir Streamlit Community Cloud se deploy kar do."
        )

    if any(x in tl for x in ["colab", "google colab"]):
        return (
            "Colab mein Streamlit direct IP se open nahi hota. Tunnel chahiye hota hai, "
            "ya phir best option: GitHub + Streamlit Cloud deployment."
        )

    if any(x in tl for x in ["help", "madad", "guide", "steps"]):
        return "Theek hai—bolo tum voice bot mein STT/TTS chahte ho ya AI (Groq) bhi add karna hai?"

    # Default fallback
    return f"Main ne suna: “{t}”. Ab batao—tumhein is ka short answer chahiye ya detailed steps?"

# ---------------- Session State ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_incoming" not in st.session_state:
    st.session_state.last_incoming = ""
if "auto_speak" not in st.session_state:
    st.session_state.auto_speak = True

# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚙️ Settings</div>', unsafe_allow_html=True)

    mode = st.selectbox("Mode", ["voice (default)", "dev (code-focused)"], index=0)
    st.session_state.auto_speak = st.toggle("Auto-speak assistant reply", value=st.session_state.auto_speak)
    lang = st.selectbox(
        "Speech Recognition Language",
        ["en-US", "ur-PK (if supported)", "hi-IN", "en-GB"],
        index=0,
        help="Browser support varies. If ur-PK doesn't work, use en-US.",
    )
    recog_lang = "ur-PK" if lang.startswith("ur-PK") else lang.split()[0]

    st.markdown("---")
    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_incoming = ""
        st.rerun()

    st.markdown("---")
    st.markdown(
        '<span class="pill">No API Key</span> &nbsp; <span class="pill">No AI model</span> &nbsp; <span class="pill">Browser STT/TTS</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="small-muted">Note: This is a rule-based demo. Real “AI chat” needs a model (local) or an API (e.g., Groq).</p>',
        unsafe_allow_html=True,
    )

# ---------------- Header ----------------
st.markdown(
    """
<div class="header-card">
  <p class="header-title">🎙️ FortisVoice</p>
  <p class="header-sub">Professional voice chatbot UI (Web Speech API) — demo without API key / without AI model.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------- Web Speech UI Component ----------------
# On final transcript it redirects to same page with ?t=<transcript>
mic_component = f"""
<div style="display:flex; gap:10px; align-items:center; margin: 6px 0 4px 0;">
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
st.components.v1.html(mic_component, height=85)

# ---------------- Read transcript from query params ----------------
qp = st.query_params
incoming = qp.get("t", "")

def add_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})

# Deduplicate transcript
if incoming and incoming != st.session_state.last_incoming:
    st.session_state.last_incoming = incoming
    add_message("user", incoming)

    reply = rule_bot(incoming)
    add_message("assistant", reply)

# ---------------- Render Chat ----------------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# ---------------- Text Input fallback ----------------
user_text = st.chat_input("Type a message (fallback)...")
if user_text:
    add_message("user", user_text)
    reply = rule_bot(user_text)
    add_message("assistant", reply)
    st.rerun()

# ---------------- Speak Assistant Reply ----------------
st.markdown("---")
col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("🔊 Speak")
with col2:
    st.markdown('<div class="small-muted">Browser TTS (SpeechSynthesis). Works best on Chrome.</div>', unsafe_allow_html=True)

last_assistant = ""
for m in reversed(st.session_state.messages):
    if m["role"] == "assistant":
        last_assistant = m["content"]
        break

speak_btn = f"""
<button style="padding:10px 14px; border-radius:12px; border:1px solid rgba(0,0,0,0.15); cursor:pointer;"
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
st.components.v1.html(speak_btn, height=70)

# Auto-speak when a new assistant reply arrives (best effort)
if st.session_state.auto_speak and incoming and last_assistant:
    # small delay to ensure UI loads
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

# ---------------- Footer ----------------
st.markdown(
    "<div class='small-muted'>Tip: Agar aapko real AI chahiye (Groq), main is app mein Groq integration bhi add kar dunga.</div>",
    unsafe_allow_html=True,
)
