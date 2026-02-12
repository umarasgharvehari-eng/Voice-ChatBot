import re
import streamlit as st

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="FortisVoice • Voice Chatbot",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- Styling (WhatsApp-ish input bar + proper space) ----------------
st.markdown(
    """
<style>
/* Give room at bottom for fixed input bar */
.block-container { padding-top: 1.1rem; padding-bottom: 6.5rem; }

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

.small-muted { opacity: 0.75; font-size: 0.92rem; }

/* Chat wrapper */
.chat-wrap{
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.03);
  border-radius: 18px;
  padding: 14px 14px;
  min-height: 60vh;
}

/* Fixed WhatsApp-like composer bar */
.composer{
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 10px 12px 14px 12px;
  background: rgba(18,18,18,0.85);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255,255,255,0.10);
  z-index: 9999;
}
.composer-inner{
  max-width: 1250px;
  margin: 0 auto;
  display: flex;
  gap: 10px;
  align-items: center;
}
.composer-input{
  flex: 1;
  display: flex;
  align-items: center;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 999px;
  padding: 10px 12px;
}
.composer-input input{
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  color: white;
  font-size: 15px;
}
.icon-btn{
  width: 44px;
  height: 44px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.08);
  cursor: pointer;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size: 18px;
}
.icon-btn:disabled{
  opacity: 0.55;
  cursor: not-allowed;
}

/* Make Streamlit chat messages look nice */
.stChatMessage { border-radius: 16px; }

/* Hide Streamlit default footer/menu (optional) */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- Language detection (English vs Urdu/Roman-Urdu) ----------------
URDU_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")

def detect_lang(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "en"
    if URDU_ARABIC_RE.search(t):
        return "ur"
    tl = t.lower()
    roman_urdu_markers = ["bhai", "mujhe", "kya", "hain", "hai", "nahi", "kar", "kr", "chahiye", "banao", "ban", "aoa", "salam"]
    score = sum(1 for w in roman_urdu_markers if w in tl)
    return "ur" if score >= 2 else "en"

# ---------------- Rule-based Bot (Bilingual, no model/no API key) ----------------
def bot_reply(text: str) -> str:
    lang = detect_lang(text)
    t = (text or "").strip()
    tl = t.lower()

    if not t:
        return "Mujhe aapki awaz clear nahi mili. Dobara bol dein." if lang == "ur" else "I didn’t catch that clearly. Please say it again."

    if any(x in tl for x in ["assalam", "asalam", "salam", "aoa", "hello", "hi", "hey"]):
        return "Wa alaikum assalam! Batao bhai, kis cheez mein help chahiye?" if lang == "ur" else "Hi! How can I help you today?"

    if "streamlit" in tl and any(x in tl for x in ["deploy", "deployment", "host", "publish"]):
        return (
            "Streamlit deploy ke liye: app.py aur requirements.txt GitHub repo mein push karo, phir Streamlit Community Cloud se deploy kar do."
            if lang == "ur"
            else
            "To deploy on Streamlit: push app.py and requirements.txt to GitHub, then deploy on Streamlit Community Cloud."
        )

    if any(x in tl for x in ["without api", "no api", "without key", "no key", "without model", "no model", "api key"]):
        return (
            "Voice input/output bina API key ke possible hai (browser Web Speech API). Lekin real AI chat ke liye model/API chahiye hota hai. Rule-based bot chal sakta hai."
            if lang == "ur"
            else
            "Voice input/output can work without an API key using the browser Web Speech API. But real AI chat needs a model/API. A rule-based bot works without it."
        )

    return (
        f"Main ne suna: “{t}”. Ab batao—short answer chahiye ya detailed steps?"
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

def add_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})

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
    st.caption("✅ No API Key • ✅ No AI Model • ✅ WhatsApp-style Composer")

# ---------------- Header ----------------
st.markdown(
    """
<div class="header-card">
  <p class="header-title">🎙️ FortisVoice</p>
  <p class="header-sub">WhatsApp-style input: text send + voice send together. English → English, Urdu/Roman-Urdu → Urdu.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------- Read incoming message from query params ----------------
qp = st.query_params
incoming = qp.get("t", "")

if incoming and incoming != st.session_state.last_incoming:
    st.session_state.last_incoming = incoming
    add_message("user", incoming)
    add_message("assistant", bot_reply(incoming))

# ---------------- Main Layout ----------------
left, right = st.columns([2.2, 1.0], gap="large")

with left:
    st.markdown("### 💬 Chat")
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown('<div class="small-muted">Neeche input bar mein type karo ya 🎤 dabao (WhatsApp style).</div>', unsafe_allow_html=True)

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("### 🔊 Speak")
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Browser TTS (SpeechSynthesis). Chrome best.</div>', unsafe_allow_html=True)

    last_assistant = ""
    for m in reversed(st.session_state.messages):
        if m["role"] == "assistant":
            last_assistant = m["content"]
            break

    speak_btn = f"""
<button class="icon-btn" style="width:100%; border-radius:14px; height:44px;"
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
    st.components.v1.html(speak_btn, height=60)
    st.markdown('<div class="small-muted" style="margin-top:10px;">Tip: Voice reply auto-speak sidebar se on/off kar lo.</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- WhatsApp-style Composer (Text + Send + Mic) ----------------
# JS behavior:
# - Text send: redirect to ?t=<text>
# - Voice: SpeechRecognition -> on final redirect to ?t=<transcript>
# - Shows small status text
# - Press Enter to send
composer = f"""
<div class="composer">
  <div class="composer-inner">
    <div class="composer-input">
      <input id="msgInput" type="text" placeholder="Type a message..." autocomplete="off" />
    </div>

    <button id="sendBtn" class="icon-btn" title="Send">➤</button>
    <button id="micBtn" class="icon-btn" title="Voice">🎤</button>
    <button id="stopBtn" class="icon-btn" title="Stop" disabled>⏹</button>

    <span id="status" class="small-muted" style="min-width:180px; margin-left:6px;"></span>
  </div>
</div>

<script>
(function(){{
  const base = window.location.origin + window.location.pathname;
  const msgInput = document.getElementById("msgInput");
  const sendBtn = document.getElementById("sendBtn");
  const micBtn  = document.getElementById("micBtn");
  const stopBtn = document.getElementById("stopBtn");
  const status  = document.getElementById("status");

  // Keep typed text across reruns (optional)
  try {{
    const saved = sessionStorage.getItem("fv_draft") || "";
    if (saved && !msgInput.value) msgInput.value = saved;
  }} catch(e){{}}

  function redirectWithText(text) {{
    const t = (text || "").trim();
    if (!t) return;
    try {{ sessionStorage.setItem("fv_draft", ""); }} catch(e){{}}
    const qp = "?t=" + encodeURIComponent(t) + "&_ts=" + Date.now();
    window.location.href = base + qp;
  }}

  function setDraft() {{
    try {{ sessionStorage.setItem("fv_draft", msgInput.value || ""); }} catch(e){{}}
  }}

  msgInput.addEventListener("input", setDraft);

  // Send on click
  sendBtn.onclick = () => {{
    redirectWithText(msgInput.value);
  }};

  // Send on Enter
  msgInput.addEventListener("keydown", (e) => {{
    if (e.key === "Enter") {{
      e.preventDefault();
      redirectWithText(msgInput.value);
    }}
  }});

  // Voice recognition
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {{
    status.textContent = "Voice not supported (use Chrome).";
    micBtn.disabled = true;
    return;
  }}

  const recog = new SpeechRecognition();
  recog.lang = "{recog_lang}";
  recog.interimResults = true;
  recog.continuous = false;

  let finalText = "";

  function setListening(on) {{
    micBtn.disabled = on;
    stopBtn.disabled = !on;
    sendBtn.disabled = on;
    msgInput.disabled = on;
  }}

  recog.onstart = () => {{
    finalText = "";
    status.textContent = "Listening...";
    setListening(true);
  }};

  recog.onresult = (event) => {{
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {{
      const chunk = event.results[i][0].transcript;
      if (event.results[i].isFinal) finalText += chunk;
      else interim += chunk;
    }}
    status.textContent = interim ? ("…" + interim) : "Listening...";
  }};

  recog.onerror = (e) => {{
    status.textContent = "Error: " + e.error;
    setListening(false);
  }};

  recog.onend = () => {{
    setListening(false);
    const t = (finalText || "").trim();
    status.textContent = t ? "Sending voice..." : "Stopped.";
    if (t) redirectWithText(t);
  }};

  micBtn.onclick = () => {{
    status.textContent = "";
    try {{ recog.start(); }} catch(e) {{ status.textContent = "Could not start mic."; }}
  }};

  stopBtn.onclick = () => {{
    try {{ recog.stop(); }} catch(e) {{}}
  }};

}})();
</script>
"""

st.components.v1.html(composer, height=0)

# ---------------- Auto-speak new assistant reply (best effort) ----------------
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
}}, 400);
</script>
""",
            height=0,
        )
