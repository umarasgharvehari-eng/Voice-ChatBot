import re
import streamlit as st
from bokeh.models import Button, CustomJS
from bokeh.layouts import column
from streamlit_bokeh_events import streamlit_bokeh_events

st.set_page_config(
    page_title="FortisVoice • Voice Chatbot",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- CSS (full page + WhatsApp-ish) ----------
st.markdown(
    """
<style>
.block-container { padding-top: 1rem; padding-bottom: 5.5rem; max-width: 1100px; }

.header-card{
  border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(16,185,129,0.10));
  padding: 16px 16px;
  border-radius: 18px;
  margin-bottom: 12px;
}
.header-title{ font-size: 1.45rem; font-weight: 800; margin: 0; color:#fff; }
.header-sub{ margin: 6px 0 0 0; opacity: 0.85; color:#fff; }

.chat-shell{
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.03);
  border-radius: 18px;
  padding: 12px;
  height: calc(100vh - 260px);
  min-height: 520px;
  overflow-y: auto;
}

.composer-shell{
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.03);
  border-radius: 18px;
  padding: 10px 12px;
  margin-top: 12px;
}

.stChatMessage { border-radius: 16px; }

div.stButton > button{
  border-radius: 999px !important;
  height: 48px !important;
  width: 48px !important;
  padding: 0 !important;
  font-size: 18px !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Language detection ----------
URDU_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")

def detect_lang(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "en"
    if URDU_ARABIC_RE.search(t):
        return "ur"
    tl = t.lower()
    roman_urdu_markers = ["bhai","mujhe","kya","hain","hai","nahi","kar","kr","chahiye","banao","ban","aoa","salam"]
    score = sum(1 for w in roman_urdu_markers if w in tl)
    return "ur" if score >= 2 else "en"

def bot_reply(user_text: str) -> str:
    lang = detect_lang(user_text)
    t = (user_text or "").strip()
    tl = t.lower()

    if not t:
        return "I didn’t catch that clearly. Please say it again." if lang == "en" else "Mujhe aapki awaz clear nahi mili. Dobara bol dein."

    if any(x in tl for x in ["assalam","asalam","salam","aoa","hello","hi","hey"]):
        return "Hi! How can I help you today?" if lang == "en" else "Wa alaikum assalam! Batao bhai, kis cheez mein help chahiye?"

    if any(x in tl for x in ["no api","without api","no key","without key","no model","without model","api key"]):
        return (
            "Voice input/output can work without an API key using the browser’s Web Speech API. "
            "But real AI chat needs a model/API. A rule-based bot works without it."
            if lang == "en"
            else
            "Voice input/output bina API key ke possible hai (browser Web Speech API). Lekin real AI chat ke liye model/API chahiye hota hai. Rule-based bot chal sakta hai."
        )

    return (
        f"I heard: “{t}”. Do you want a quick answer or detailed steps?"
        if lang == "en"
        else
        f"Main ne suna: “{t}”. Ab batao—short answer chahiye ya detailed steps?"
    )

# ---------- State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "draft" not in st.session_state:
    st.session_state.draft = ""
if "auto_speak" not in st.session_state:
    st.session_state.auto_speak = True

def push_user_message(text: str):
    text = (text or "").strip()
    if not text:
        return
    st.session_state.messages.append({"role":"user", "content": text})
    reply = bot_reply(text)
    st.session_state.messages.append({"role":"assistant", "content": reply})

    if st.session_state.auto_speak:
        st.components.v1.html(
            f"""
<script>
setTimeout(() => {{
  const msg = new SpeechSynthesisUtterance({reply!r});
  msg.rate = 1.0; msg.pitch = 1.0;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(msg);
}}, 200);
</script>
""",
            height=0,
        )

# ---------- Sidebar ----------
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
        st.session_state.draft = ""
        st.rerun()

# ---------- Header ----------
st.markdown(
    """
<div class="header-card">
  <p class="header-title">🎙️ FortisVoice</p>
  <p class="header-sub">Full-page WhatsApp-style chat (Streamlit Cloud safe).</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- Chat area ----------
st.markdown('<div class="chat-shell" id="chatShell">', unsafe_allow_html=True)
if not st.session_state.messages:
    st.write("Send a text message or tap the mic.")
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])
st.markdown("</div>", unsafe_allow_html=True)

# auto-scroll
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

# ---------- Composer row ----------
st.markdown('<div class="composer-shell">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([8, 1, 1], vertical_alignment="center")

with c1:
    st.session_state.draft = st.text_input(
        "",
        value=st.session_state.draft,
        placeholder="Message...",
        label_visibility="collapsed",
    )

with c2:
    send = st.button("➤", help="Send")

with c3:
    # Bokeh mic button that emits transcript to Streamlit (NO navigation)
    mic_btn = Button(label="🎤", button_type="primary", width=48, height=48)

    mic_btn.js_on_event("button_click", CustomJS(code=f"""
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {{
            document.dispatchEvent(new CustomEvent("SPEECH_TEXT", {{ detail: {{ text: "" }} }}));
            return;
        }}
        const recog = new SpeechRecognition();
        recog.lang = "{recog_lang}";
        recog.interimResults = false;
        recog.continuous = false;

        let finalText = "";

        recog.onresult = (event) => {{
            finalText = event.results[0][0].transcript || "";
        }};
        recog.onerror = (e) => {{
            finalText = "";
        }};
        recog.onend = () => {{
            document.dispatchEvent(new CustomEvent("SPEECH_TEXT", {{ detail: {{ text: finalText }} }}));
        }};

        try {{ recog.start(); }} catch(e) {{
            document.dispatchEvent(new CustomEvent("SPEECH_TEXT", {{ detail: {{ text: "" }} }}));
        }}
    """))

    result = streamlit_bokeh_events(
        column(mic_btn),
        events="SPEECH_TEXT",
        key="speech",
        refresh_on_update=False,
        override_height=60,
        debounce_time=0,
    )

st.markdown("</div>", unsafe_allow_html=True)

# ---------- Handle send ----------
if send:
    push_user_message(st.session_state.draft)
    st.session_state.draft = ""
    st.rerun()

# ---------- Handle mic transcript ----------
if result and "SPEECH_TEXT" in result:
    spoken = (result["SPEECH_TEXT"].get("text") or "").strip()
    if spoken:
        push_user_message(spoken)
        st.rerun()
