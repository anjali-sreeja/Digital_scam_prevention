"""
Streamlit UI
Run:
    streamlit run app.py
"""

import streamlit as st
import os
import sys
import tempfile

# Allow backend imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

st.set_page_config(page_title="Guardian Angel", layout="centered")

# ─────────────────────────────────────────────
# LOAD AGENTS
# ─────────────────────────────────────────────

@st.cache_resource
def load_guardian():
    from backend.detector import GuardianAgent
    return GuardianAgent()

@st.cache_resource
def load_voice():
    from backend.voice_detector import VoiceScamDetector
    return VoiceScamDetector()

guardian = load_guardian()
voice_det = load_voice()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.title(" Guardian Angel")
st.caption("SMS + Voice Call Scam Detection (Digital Arrest Scams)")

tabs = st.tabs([" SMS Detection", " Voice Call Detection"])

# ─────────────────────────────────────────────
# TAB 1 — SMS
# ─────────────────────────────────────────────

with tabs[0]:

    message = st.text_area(
        "Paste SMS / WhatsApp Message:",
        height=150
    )

    if st.button(" Analyze SMS", type="primary"):
        if not message.strip():
            st.warning("Please paste a message first.")
        else:
            result = guardian.analyze(message)

            st.markdown("---")
            st.subheader("Result")

            st.metric("Risk Score", f"{result['risk_score']}%")
            st.write("Risk Level:", result["risk_level"])

            if result["risk_level"] == "SCAM":
                st.error(" This is a SCAM!")
            elif result["risk_level"] == "SUSPICIOUS":
                st.warning(" Suspicious message.")
            else:
                st.success(" Looks Safe.")

            if result["red_flags"]:
                st.subheader(" Red Flags")
                for f in result["red_flags"]:
                    st.write("-", f)

# ─────────────────────────────────────────────
# TAB 2 — VOICE
# ─────────────────────────────────────────────

with tabs[1]:

    st.subheader("Upload Audio File")

    uploaded = st.file_uploader(
        "Upload .mp3 / .m4a / .wav",
        type=["mp3", "m4a", "wav", "ogg", "flac"]
    )

    language = st.selectbox(
        "Language (optional)",
        ["Auto", "English", "Hindi", "Kannada"]
    )

    lang_map = {
        "Auto": None,
        "English": "en",
        "Hindi": "hi",
        "Kannada": "kn"
    }

    if st.button(" Analyze Voice", type="primary"):
        if uploaded is None:
            st.warning("Upload audio file first.")
        else:
            suffix = os.path.splitext(uploaded.name)[1]

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name

            with st.spinner("Transcribing & Analyzing..."):
                result = voice_det.analyze_file(
                    tmp_path,
                    language=lang_map[language]
                )

            os.remove(tmp_path)

            st.markdown("---")
            st.subheader("Voice Analysis Result")

            if not result.get("stt_success"):
                st.error("Transcription failed.")
                st.write(result.get("stt_error"))
            else:
                st.metric("Risk Score", f"{result['risk_score']}%")
                st.write("Risk Level:", result["risk_level"])

                if result["risk_level"] == "SCAM":
                    st.error(" This is a SCAM CALL!")
                elif result["risk_level"] == "SUSPICIOUS":
                    st.warning(" Suspicious Call.")
                else:
                    st.success("Looks Safe.")

                st.subheader("Transcript")
                st.write(result["transcript"])

                if result["red_flags"]:
                    st.subheader(" Red Flags")
                    for f in result["red_flags"]:
                        st.write("-", f)