import re
import streamlit as st

# =======================
# FortisVoice (Polished WhatsApp-style UI)
# FIXES:
# 1) Your composer looked tiny because Streamlit components run inside an iframe.
#    CSS from the main page DOES NOT apply inside that iframe.
#    -> Solution: put ALL composer CSS inside the component itself (inline <style>).
# 2) Full page chat: big chat area + proper scroll + composer at bottom (not tiny).
# =======================

st.set_page_config(
    page_title="FortisVoice • Voice Chatbot",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Main-page CSS (chat area polish) ----------
st.markdown(
    """
<style>
/* Layout + spacing */
.block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 1100px; }

/* Header */
.header-card{
  border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(16,185,129,0.10));
  padding: 16px 16px;
  border-radius: 18px;
  margin-bottom: 12px;
}
.header-title{ font-size: 1.45rem; font-weight: 800; margin: 0; color:#fff; }
.header-sub{ margin: 6px 0 0 0; opacity: 0.85; color:#fff; }

.small-muted { opacity: 0.75; font-size: 0.92rem; }

/* Chat panel: BIG and scrollable */
.chat-shell{
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.03);
  border-radius: 18px;
  padding: 10px 10px;
  height: calc(100vh - 260px); /* fills screen nicely */
  min-height: 520px;
  overflow-y: auto;
}

/* Chat message bubble rounding */
.stChatMessage { border-radius: 16px; }

/* Hide menu/footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Language detection (UI stays English; replies match user language) ----------
URDU_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")

def detect_lang(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "en"
    if URDU_ARABIC_RE.search(t):
        return "ur"
    tl = t.lower()
    roman_urdu_markers = [
        "bhai","mujhe","kya","hain","hai","nahi","kar","kr","chahiye","banao","ban","aoa","salam"
    ]
    score = sum(1 for w in roman_urdu_markers if w in tl)
    return "ur" if score >= 2 else "en"

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

# ---------- Session state ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_incoming" not in st.session_state:
    st.session_state.last_incoming = ""
if "auto_speak" not in st.session_state:
    st.session_state.auto_speak = True

def add_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})

# ---------- Sidebar (English only) ----------
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
    st.caption("This demo uses browser STT/TTS. No API key.")

# ---------- Header ----------
st.markdown(
    """
<div class="header-card">
  <p class="header-title">🎙️ FortisVoice</p>
  <p class="header-sub">WhatsApp-style: full-page chat + text send + voice send at the bottom.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- Receive message via query params (from composer JS) ----------
incoming = st.query_params.get("t", "")

if incoming and incoming != st.session_state.last_incoming:
    st.session_state.last_incoming = incoming
    add_message("user", incoming)
    add_message("assistant", bot_reply(incoming))

# ---------- Full-page Chat Panel (scrollable) ----------
st.markdown('<div class="chat-shell" id="chatShell">', unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown('<div class="small-muted">Send a message using the bar below.</div>', unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

st.markdown("</div>", unsafe_allow_html=True)

# ---------- Auto-scroll to bottom of chat panel ----------
st.components.v1.html(
    """
<script>
(function(){
  const el = window.parent.document.getElementById("chatShell");
  if (el) el.scrollTop = el.scrollHeight;
})();
</script>
""",
    height=0,
)

# ---------- Auto-speak last assistant reply ----------
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
}}, 200);
</script>
""",
            height=0,
        )

# ============================================================
# Bottom Composer (WhatsApp style) — IMPORTANT:
# Put CSS INSIDE this component (iframe), otherwise it looks tiny/unstyled.
# ============================================================
composer_html = f"""
<style>
  html, body {{
    margin: 0; padding: 0;
    background: transparent;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
  }}
  .bar {{
    width: 100%;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 10px;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.14);
    background: rgba(20,20,24,0.92);
    box-sizing: border-box;
  }}
  .inp {{
    flex: 1;
    display: flex;
    align-items: center;
    padding: 10px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.14);
  }}
  .inp input {{
    width: 100%;
    border: none;
    outline: none;
    background: transparent;
    color: white;
    font-size: 15px;
  }}
  .btn {{
    width: 48px;
    height: 48px;
    border-radius: 999px;
    border: none;
    color: white;
    font-size: 18px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .send {{ background: #22c55e; }}
  .send:hover {{ background: #1fb255; }}
  .mic {{ background: #3b82f6; }}
  .mic:hover {{ background: #3273d9; }}
  .stop {{ background: #ef4444; }}
  .stop:hover {{ background: #d93b3b; }}
  .btn:disabled {{ opacity: 0.6; cursor: not-allowed; }}

  .status {{
    margin-top: 6px;
    font-size: 13px;
    opacity: 0.75;
    color: #111;
  }}
  /* If dark theme, status should still be visible */
  @media (prefers-color-scheme: dark) {{
    .status {{ color: rgba(255,255,255,0.8); }}
  }}
</style>

<div class="bar">
  <div class="inp">
    <input id="msg" type="text" placeholder="Message..." autocomplete="off"/>
  </div>
  <button id="send" class="btn send" title="Send">➤</button>
  <button id="mic" class="btn mic" title="Voice">🎤</button>
  <button id="stop" class="btn stop" title="Stop" disabled>⏹</button>
</div>
<div id="status" class="status"></div>

<script>
(function(){{
  const base = window.location.origin + window.location.pathname;

  const msg = document.getElementById("msg");
  const send = document.getElementById("send");
  const mic  = document.getElementById("mic");
  const stop = document.getElementById("stop");
  const status = document.getElementById("status");

  function redirectWithText(text){{
    const t = (text || "").trim();
    if(!t) return;
    window.location.href = base + "?t=" + encodeURIComponent(t) + "&_ts=" + Date.now();
  }}

  // Send text
  send.onclick = () => redirectWithText(msg.value);
  msg.addEventListener("keydown", (e) => {{
    if (e.key === "Enter") {{
      e.preventDefault();
      redirectWithText(msg.value);
    }}
  }});

  // Voice recognition
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {{
    status.textContent = "Voice input not supported in this browser. Use Chrome.";
    mic.disabled = true;
    return;
  }}

  const recog = new SpeechRecognition();
  recog.lang = "{recog_lang}";
  recog.interimResults = true;
  recog.continuous = false;

  let finalText = "";

  function setListening(on){{
    mic.disabled = on;
    stop.disabled = !on;
    send.disabled = on;
    msg.disabled = on;
  }}

  recog.onstart = () => {{
    finalText = "";
    status.textContent = "Listening…";
    setListening(true);
  }};

  recog.onresult = (event) => {{
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {{
      const chunk = event.results[i][0].transcript;
      if (event.results[i].isFinal) finalText += chunk;
      else interim += chunk;
    }}
    status.textContent = interim ? ("…" + interim) : "Listening…";
  }};

  recog.onerror = (e) => {{
    status.textContent = "Error: " + e.error;
    setListening(false);
  }};

  recog.onend = () => {{
    setListening(false);
    const t = (finalText || "").trim();
    if (t) {{
      status.textContent = "Sending…";
      redirectWithText(t);
    }} else {{
      status.textContent = "";
    }}
  }};

  mic.onclick = () => {{
    status.textContent = "";
    try {{ recog.start(); }} catch(e) {{ status.textContent = "Could not start microphone."; }}
  }};

  stop.onclick = () => {{
    try {{ recog.stop(); }} catch(e) {{}}
  }};
}})();
</script>
"""

# This is displayed under the chat, like WhatsApp.
# Height MUST be > 0 on Streamlit Cloud.
st.components.v1.html(composer_html, height=120)
