import io
from datetime import datetime

import streamlit as st
from openai import OpenAI
from audiorecorder import audiorecorder  # pip install streamlit-audiorecorder


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
# Groq clients (OpenAI-compatible)
# ---------------------------
GROQ_BASE_URL = "https://api.groq.com/openai/v1"  # OpenAI-compatible base URL :contentReference[oaicite:3]{index=3}

def get_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)

# ---------------------------
# Helpers
# ---------------------------
def now_time():
    return datetime.now().strftime("%H:%M")

def sanitize_html(text: str) -> str:
    # Minimal escaping for safe bubble render
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )

def stt_transcribe_wav(groq: OpenAI, wav_bytes: bytes, lang_hint: str = "") -> str:
    """
    Groq Speech-to-Text using OpenAI-compatible endpoint.
    Model examples: whisper-large-v3 / whisper-large-v3-turbo :contentReference[oaicite:4]{index=4}
    """
    # OpenAI python expects a file-like or tuple: (filename, bytes, mimetype)
    # Some versions accept just bytes; tuple is safest.
    transcript = groq.audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=("voice.wav", wav_bytes, "audio/wav"),
        # language is optional; keep empty if you want auto-detect
        language=lang_hint if lang_hint else None,
    )
    # Depending on SDK version, transcript may be str or object with .text
    return getattr(transcript, "text", transcript)

def chat_complete(groq: OpenAI, messages: list[dict]) -> str:
    """
    Groq chat completion via OpenAI-compatible Chat Completions endpoint. :contentReference[oaicite:5]{index=5}
    """
    resp = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3,
    )
    return resp.choices[0].message.content

# ---------------------------
# Session state
# ---------------------------
if "messages" not in st.session_state:
    # message: {role: "user"|"assistant", type:"text"|"audio", content, time}
    st.session_state.messages = []

if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""

# ---------------------------
# Sidebar
# ---------------------------
st.sidebar.title("Settings")

auto_speak = st.sidebar.toggle("Auto-speak assistant reply", value=True)

st.sidebar.markdown("### Groq API")
if st.secrets.get("GROQ_API_KEY", ""):
    st.sidebar.success("GROQ_API_KEY found ✅")
else:
    st.sidebar.warning("GROQ_API_KEY missing. Add it in Streamlit Secrets.")

voice_lang_hint = st.sidebar.selectbox(
    "Voice language hint (optional)",
    options=["", "en", "ur", "hi"],
    index=0,
    help="STT usually auto-detects; this only hints the transcription.",
)

if st.sidebar.button("Clear chat", use_container_width=True):
    st.session_state.messages = []
    st.session_state.last_spoken = ""
    st.rerun()

st.sidebar.caption(
    "Voice recording uses a Streamlit component (not browser postMessage hacks). "
    "STT + Chat uses Groq."
)

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
  padding-bottom: 6.0rem !important;
  max-width: 1200px;
}
.chat-shell {
  width: 100%;
  height: calc(100vh - 12rem);
  background: #efeae2;
  border-radius: 18px;
  padding: 12px 12px 16px 12px;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  border: 1px solid rgba(0,0,0,0.05);
}
.msg-row { display:flex; margin:10px 0; }
.msg-row.user { justify-content:flex-end; }
.msg-row.bot { justify-content:flex-start; }
.bubble {
  max-width: 72%;
  padding: 10px 12px;
  border-radius: 14px;
  line-height: 1.35;
  font-size: 0.98rem;
  position: relative;
  word-wrap: break-word;
}
.bubble.user { background:#d9fdd3; border-top-right-radius: 6px; }
.bubble.bot { background:#ffffff; border-top-left-radius: 6px; }
.time { display:block; margin-top:6px; font-size:0.72rem; opacity:0.55; text-align:right; }
.composer {
  position: fixed; left:0; right:0; bottom:0;
  z-index: 999;
  background: rgba(239,234,226,0.92);
  backdrop-filter: blur(8px);
  border-top: 1px solid rgba(0,0,0,0.08);
  padding: 10px 0;
}
.composer-inner { max-width:1200px; margin:0 auto; padding:0 1rem; }
div[data-testid="stTextInput"] input {
  border-radius: 999px !important;
  padding: 0.70rem 1rem !important;
  border: 1px solid rgba(0,0,0,0.12) !important;
  background: #fff !important;
}
button[kind="primary"], button[kind="secondary"] {
  border-radius: 999px !important;
  height: 44px !important;
}
@media (max-width: 768px) {
  .block-container { max-width: 100% !important; }
  .bubble { max-width: 86%; }
  .chat-shell { height: calc(100vh - 14rem); border-radius: 14px; }
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
      <div style="font-size:0.85rem;opacity:0.65;">WhatsApp-style voice + Groq AI</div>
    </div>
  </div>
  <div style="font-size:0.85rem;opacity:0.6;">Recorder • STT • Chat • TTS</div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Render chat (HTML bubbles; audio uses st.audio below bubble)
# ---------------------------
st.markdown('<div class="chat-shell" id="chatShell">', unsafe_allow_html=True)

for m in st.session_state.messages:
    role_cls = "user" if m["role"] == "user" else "bot"
    bubble_cls = "user" if m["role"] == "user" else "bot"

    if m.get("type") == "audio":
        # Bubble header + audio player
        st.markdown(
            f"""
<div class="msg-row {role_cls}">
  <div class="bubble {bubble_cls}">
    <b>🎤 Voice note</b>
    <span class="time">{m["time"]}</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.audio(m["content"], format="audio/wav")  # content is bytes
    else:
        st.markdown(
            f"""
<div class="msg-row {role_cls}">
  <div class="bubble {bubble_cls}">
    {sanitize_html(m["content"])}
    <span class="time">{m["time"]}</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

st.markdown(
    """
<script>
  const el = document.getElementById("chatShell");
  if (el) { el.scrollTop = el.scrollHeight; }
</script>
""",
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Composer (bottom fixed)
# ---------------------------
st.markdown('<div class="composer"><div class="composer-inner">', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns([7, 1.2, 1.2, 1.2])

with c1:
    user_text = st.text_input(
        "Message",
        value="",
        label_visibility="collapsed",
        placeholder="Type a message…",
        key="text_box",
    )

with c2:
    # WhatsApp-like voice note record
    # Tip from component README: if prompts are empty, it can show visualizer :contentReference[oaicite:6]{index=6}
    audio_seg = audiorecorder(
        start_prompt="🎙️ Record",
        stop_prompt="⏹ Stop",
        pause_prompt="",
        show_visualizer=True,
        key="voice_note",
    )

with c3:
    send_text = st.button("➤ Send", type="primary", use_container_width=True)

with c4:
    speak_last = st.button("🔊 Speak", use_container_width=True)

st.markdown("</div></div>", unsafe_allow_html=True)

# ---------------------------
# Actions
# ---------------------------
groq = get_groq_client()

def append_user_text(text: str):
    st.session_state.messages.append(
        {"role": "user", "type": "text", "content": text, "time": now_time()}
    )

def append_user_audio(wav_bytes: bytes):
    st.session_state.messages.append(
        {"role": "user", "type": "audio", "content": wav_bytes, "time": now_time()}
    )

def append_assistant(text: str):
    st.session_state.messages.append(
        {"role": "assistant", "type": "text", "content": text, "time": now_time()}
    )
    st.session_state.last_spoken = text

def build_chat_messages_for_api():
    # Keep history; include a system prompt
    msgs = [
        {
            "role": "system",
            "content": (
                "You are FortisVoice, a helpful assistant. "
                "Reply naturally. If the user writes Urdu/Roman Urdu, reply in Urdu/Roman Urdu. "
                "Keep answers concise unless user asks for details."
            ),
        }
    ]
    for m in st.session_state.messages:
        if m["role"] == "user" and m.get("type") == "text":
            msgs.append({"role": "user", "content": m["content"]})
        elif m["role"] == "assistant" and m.get("type") == "text":
            msgs.append({"role": "assistant", "content": m["content"]})
        # (Audio messages are converted to text after STT; we don't send raw audio to chat model.)
    return msgs

# Send text
if send_text and user_text.strip():
    if not groq:
        append_user_text(user_text.strip())
        append_assistant("⚠️ GROQ_API_KEY missing. Please add it in Streamlit Secrets.")
        st.rerun()

    append_user_text(user_text.strip())
    msgs = build_chat_messages_for_api()
    reply = chat_complete(groq, msgs)
    append_assistant(reply)
    st.rerun()

# Handle voice note (when audio recorded)
# audiorecorder returns a pydub AudioSegment. len(audio_seg) > 0 indicates data :contentReference[oaicite:7]{index=7}
if audio_seg is not None and len(audio_seg) > 0:
    if not groq:
        # still show the audio bubble, but cannot transcribe/chat
        wav_bytes = audio_seg.export(format="wav").read()
        append_user_audio(wav_bytes)
        append_assistant("⚠️ GROQ_API_KEY missing. Add it in Streamlit Secrets to transcribe & reply.")
        st.rerun()

    wav_bytes = audio_seg.export(format="wav").read()
    append_user_audio(wav_bytes)

    with st.spinner("Transcribing voice note…"):
        transcript = stt_transcribe_wav(groq, wav_bytes, lang_hint=voice_lang_hint)

    # Show transcript as user text (so chat model gets it)
    append_user_text(transcript)

    with st.spinner("Thinking…"):
        msgs = build_chat_messages_for_api()
        reply = chat_complete(groq, msgs)

    append_assistant(reply)
    st.rerun()

# Speak button: speak last assistant message (client-side TTS)
if speak_last:
    # find last assistant text
    last = ""
    for m in reversed(st.session_state.messages):
        if m["role"] == "assistant" and m.get("type") == "text":
            last = m["content"]
            break
    st.session_state.last_spoken = last

# Auto-speak assistant reply (browser TTS)
if auto_speak and st.session_state.last_spoken:
    safe_text = (
        st.session_state.last_spoken
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("\n", " ")
    )
    st.components.v1.html(
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
    st.session_state.last_spoken = ""
