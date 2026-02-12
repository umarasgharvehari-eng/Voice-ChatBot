import re
import streamlit as st

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="FortisVoice • Voice Chatbot",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- Styling (English UI, clean spacing) ----------------
st.markdown(
    """
<style>
.block-container { padding-top: 1.1rem; padding-bottom: 2.5rem; max-width: 1200px; }

.header-card{
  border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(16,185,129,0.10));
  padding: 16px 16px;
  border-radius: 18px;
  margin-bottom: 12px;
}
.header-title{ font-size: 1.45rem; font-weight: 800; margin: 0; color: #fff; }
.header-sub{ margin: 6px 0 0 0; opacity: 0.85; color: #fff; }

.small-muted { opacity: 0.75; font-size: 0.92rem; }

.chat-wrap{
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.03);
  border-radius: 18px;
  padding: 14px 14px;
  min-height: 66vh;
}

.stChatMessage { border-radius: 16px; }

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- Language detection (for replies only; UI stays English) ----------------
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

# ---------------- Rule-based bot (bilingual replies) ----------------
def bot_reply(user_text: str) -> str:
    lang = detect_lang(user_text)
    t = (user_text or "").strip()
    tl = t.lower()

    if not t:
        return "I didn’t catch that clearly. Please say it again." if lang == "en" else "Mujhe aapki awaz clear nahi mili. Dobara bol dein."

    if any(x in tl for x in ["assalam", "asalam", "salam", "aoa", "hello", "hi", "hey"]):
        return "Hi! How can I help you today?" if lang == "en" else "Wa alaikum assalam! Batao bhai, kis cheez mein help chahiye?"

    if any(x in tl for x in ["no api", "without api", "no key", "without key", "no model", "without model", "api key"]):
        return (
            "Voice input/output can work without an API key using the browser’s Web Speech API. "
            "But real AI chat needs a model/API. A rule-based bot works without it."
            if lang == "en"
            else
            "Voice input/output bina API key ke possible hai (browser Web Speech API). Lekin real AI chat ke liye model/API chahiye hota hai. Rule-based bot chal sakta hai."
        )

    if "streamlit" in tl and any(x in tl for x in ["deploy", "deployment", "host", "publish"]):
        return (
            "To deploy on Streamlit: push app.py and requirements.txt to GitHub, then deploy on Streamlit Community Cloud."
            if lang == "en"
            else
            "Streamlit deploy ke liye: app.py aur requirements.txt GitHub repo mein push karo, phir Streamlit Community Cloud se deploy kar do."
        )

    return (
        f"I heard: “{t}”. Do you want a quick answer or detailed steps?"
        if lang == "en"
        else
        f"Main ne suna: “{t}”. Ab batao—short answer chahiye ya detailed steps?"
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

# ---------------- Sidebar (English only) ----------------
with st.sidebar:
    st.markdown("## Settings")
    st.session_state.auto_speak = st.toggle("Auto-speak assistant reply", value=st.session_state.auto_speak)

    recog_lang = st.selectbox(
        "Voice input language",
        ["en-US", "en-GB", "ur-PK (if supported)"],
        index=0,
        help="Browser support varies. If ur-PK doesn’t work, use en-US/en-GB.",
    )
    recog_lang = "ur-PK" if recog_lang.startswith("ur-PK") else recog_lang

    st.markdown("---")
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_incoming = ""
        st.rerun()

    st.markdown("---")
    st.caption("Voice uses browser STT/TTS. No API key in this demo.")

# ---------------- Header (English only) ----------------
st.markdown(
    """
<div class="header-card">
  <p class="header-title">🎙️ FortisVoice</p>
  <p class="header-sub">Type + Send + Voice (WhatsApp-style). Replies match your language (English or Urdu).</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------- Handle incoming message from query params ----------------
qp = st.query_params
incoming = qp.get("t", "")

if incoming and incoming != st.session_state.last_incoming:
    st.session_state.last_incoming = incoming
    add_message("user", incoming)
    add_message("assistant", bot_reply(incoming))

# ---------------- Main Layout ----------------
left, right = st.columns([2.2, 1.0], gap="large")

with left:
    st.markdown("### Chat")
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown('<div class="small-muted">Use the message bar below to type or send a voice message.</div>', unsafe_allow_html=True)

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("### Speak")
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="small-muted">Text-to-speech uses your browser (SpeechSynthesis).</div>', unsafe_allow_html=True)

    last_assistant = ""
    for m in reversed(st.session_state.messages):
        if m["role"] == "assistant":
            last_assistant = m["content"]
            break

    speak_btn = f"""
<button style="width:100%; padding:12px 14px; border-radius:14px; border:1px solid rgba(255,255,255,0.14); background:rgba(255,255,255,0.08); color:white; cursor:pointer;"
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
    st.components.v1.html(speak_btn, height=65)

    st.markdown('<div class="small-muted" style="margin-top:10px;">Tip: Turn auto-speak on/off in Settings.</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- UPDATED COMPOSER (Guaranteed visible on Streamlit Cloud) ----------------
st.markdown("---")
st.markdown("### Message")

composer_html = f"""
<div style="display:flex; gap:10px; align-items:center; margin-top:10px;">
  
  <input id="msgInput" type="text" placeholder="Type a message..."
    style="
      flex:1;
      padding:12px 16px;
      border-radius:999px;
      border:1px solid rgba(255,255,255,0.2);
      background:rgba(255,255,255,0.05);
      color:white;
      font-size:15px;
      outline:none;
    "
  />

  <button id="sendBtn"
    style="
      width:48px;
      height:48px;
      border-radius:999px;
      border:none;
      background:#22c55e;
      color:white;
      font-size:18px;
      cursor:pointer;
    ">➤</button>

  <button id="micBtn"
    style="
      width:48px;
      height:48px;
      border-radius:999px;
      border:none;
      background:#3b82f6;
      color:white;
      font-size:18px;
      cursor:pointer;
    ">🎤</button>

</div>

<div id="status" style="margin-top:8px; font-size:14px; opacity:0.7;"></div>

<script>
(function(){{
  const base = window.location.origin + window.location.pathname;
  const msgInput = document.getElementById("msgInput");
  const sendBtn = document.getElementById("sendBtn");
  const micBtn  = document.getElementById("micBtn");
  const status  = document.getElementById("status");

  function redirectWithText(text) {{
    const t = (text || "").trim();
    if (!t) return;
    window.location.href = base + "?t=" + encodeURIComponent(t) + "&_ts=" + Date.now();
  }}

  sendBtn.onclick = () => redirectWithText(msgInput.value);

  msgInput.addEventListener("keydown", (e) => {{
    if (e.key === "Enter") {{
      e.preventDefault();
      redirectWithText(msgInput.value);
    }}
  }});

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {{
    status.textContent = "Voice input not supported. Use Chrome.";
    micBtn.disabled = true;
    return;
  }}

  const recog = new SpeechRecognition();
  recog.lang = "{recog_lang}";
  recog.interimResults = true;
  recog.continuous = false;

  let finalText = "";

  recog.onstart = () => {{
    finalText = "";
    status.textContent = "Listening...";
    micBtn.disabled = true;
  }};

  recog.onresult = (event) => {{
    for (let i = event.resultIndex; i < event.results.length; i++) {{
      if (event.results[i].isFinal)
        finalText += event.results[i][0].transcript;
    }}
  }};

  recog.onerror = (e) => {{
    status.textContent = "Error: " + e.error;
    micBtn.disabled = false;
  }};

  recog.onend = () => {{
    micBtn.disabled = false;
    if (finalText.trim().length > 0) {{
      status.textContent = "Sending voice message...";
      redirectWithText(finalText);
    }} else {{
      status.textContent = "";
    }}
  }};

  micBtn.onclick = () => {{
    status.textContent = "";
    try {{ recog.start(); }} catch(e) {{
      status.textContent = "Microphone error.";
    }}
  }};
}})();
</script>
"""

st.components.v1.html(composer_html, height=140)

# ---------------- Auto-speak last assistant reply ----------------
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
}}, 350);
</script>
""",
            height=0,
        )
