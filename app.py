import streamlit as st
import urllib.parse

st.set_page_config(page_title="FortisVoice (No Key Demo)", page_icon="🎙️", layout="centered")

# ---------- Simple rule-based chatbot (NO model) ----------
def rule_bot(text: str) -> str:
    t = (text or "").lower().strip()

    if not t:
        return "Mujhe aapki awaz clear nahi mili. Dobara bol dein."

    # Greetings
    if any(x in t for x in ["assalam", "salam", "hello", "hi", "aoa"]):
        return "Wa alaikum assalam! Batao bhai, kya help chahiye?"

    # Common intents
    if "name" in t:
        return "Mera naam FortisVoice hai."
    if "time" in t or "clock" in t:
        return "Main yahan system time access nahi kar sakta, lekin aap apne device pe time dekh sakte ho."
    if "streamlit" in t and ("deploy" in t or "deployment" in t):
        return "Streamlit deploy ke liye app.py aur requirements.txt repo me push karo, phir Streamlit Community Cloud se deploy kar do."

    # Default fallback
    return f"Main ne suna: '{text}'. Ab aap batao, is pe kya karna hai—code chahiye ya steps?"


# ---------- Read transcript passed via query param ----------
# JS will redirect to /?t=<transcript>
qp = st.query_params
incoming = qp.get("t", "")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🎙️ FortisVoice (No API Key / No Model Demo)")
st.caption("Mic uses Web Speech API (browser). Chat responses are rule-based (no AI model).")

# ---------- Mic + TTS UI (browser-side) ----------
# This HTML uses Web Speech API for speech-to-text and speechSynthesis for text-to-speech.
# On final transcript, it redirects the page with ?t=<transcript> so Streamlit can read it.
mic_html = """
<div style="display:flex; gap:10px; align-items:center; margin: 8px 0 0 0;">
  <button id="startBtn" style="padding:10px 14px; border-radius:10px; border:1px solid #ccc; cursor:pointer;">
    🎤 Start
  </button>
  <button id="stopBtn" style="padding:10px 14px; border-radius:10px; border:1px solid #ccc; cursor:pointer;" disabled>
    ⏹ Stop
  </button>
  <span id="status" style="font-family: system-ui; opacity: 0.8;"></span>
</div>

<script>
(function(){
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const statusEl = document.getElementById("status");
  const startBtn = document.getElementById("startBtn");
  const stopBtn  = document.getElementById("stopBtn");

  if (!SpeechRecognition) {
    statusEl.textContent = "❌ SpeechRecognition not supported. Please use Chrome.";
    startBtn.disabled = true;
    return;
  }

  let recog = new SpeechRecognition();
  recog.lang = "en-US"; // You can change to "ur-PK" if supported in your browser
  recog.interimResults = true;
  recog.continuous = false;

  let finalText = "";

  recog.onstart = () => {
    finalText = "";
    statusEl.textContent = "Listening...";
    startBtn.disabled = true;
    stopBtn.disabled = false;
  };

  recog.onresult = (event) => {
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const chunk = event.results[i][0].transcript;
      if (event.results[i].isFinal) finalText += chunk;
      else interim += chunk;
    }
    statusEl.textContent = interim ? ("…" + interim) : "Listening...";
  };

  recog.onerror = (e) => {
    statusEl.textContent = "❌ Error: " + e.error;
    startBtn.disabled = false;
    stopBtn.disabled = true;
  };

  recog.onend = () => {
    startBtn.disabled = false;
    stopBtn.disabled = true;
    if (finalText && finalText.trim().length > 0) {
      // redirect with query param
      const t = encodeURIComponent(finalText.trim());
      const base = window.location.origin + window.location.pathname;
      window.location.href = base + "?t=" + t;
    } else {
      statusEl.textContent = "Stopped.";
    }
  };

  startBtn.onclick = () => recog.start();
  stopBtn.onclick = () => recog.stop();
})();
</script>
"""
st.components.v1.html(mic_html, height=90)

# ---------- If we got a transcript, append as user message and respond ----------
if incoming:
    # Clear query param after reading (so refresh doesn't re-add)
    # Streamlit doesn't support direct clearing without rerun; we can just ignore if same as last.
    last_incoming = st.session_state.get("last_incoming", "")
    if incoming != last_incoming:
        st.session_state.last_incoming = incoming
        st.session_state.messages.append({"role": "user", "content": incoming})
        reply = rule_bot(incoming)
        st.session_state.messages.append({"role": "assistant", "content": reply})

# ---------- Chat UI ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# ---------- Manual text input fallback ----------
user_text = st.chat_input("Type here (fallback) ...")
if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    reply = rule_bot(user_text)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# ---------- Speak last assistant message button ----------
st.divider()
st.subheader("🔊 Speak last reply")

last_assistant = ""
for m in reversed(st.session_state.messages):
    if m["role"] == "assistant":
        last_assistant = m["content"]
        break

speak_html = f"""
<button style="padding:10px 14px; border-radius:10px; border:1px solid #ccc; cursor:pointer;"
onclick="
  const msg = new SpeechSynthesisUtterance({last_assistant!r});
  msg.rate = 1.0;
  msg.pitch = 1.0;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(msg);
">
🔊 Speak
</button>
<span style="margin-left:10px; opacity:0.7;">(Uses browser TTS)</span>
"""
st.components.v1.html(speak_html, height=70)

st.info(
    "Note: Ye demo bina API key ke chalega, lekin chatbot 'AI' nahi hai—sirf rule-based replies. "
    "Agar tumhein real AI chahiye, tumhein koi model (local) ya API (Groq/OpenAI) integrate karni hogi."
)

