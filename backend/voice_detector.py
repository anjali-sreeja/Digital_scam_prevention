"""
VOICE DETECTOR — Audio Call Scam Detection
File: backend/voice_detector.py
"""

import os
import sys
from typing import Optional

# Ensure project root is accessible
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.detector import GuardianAgent


# ─────────────────────────────────────────────
# TRANSCRIPTION ENGINE
# ─────────────────────────────────────────────

class TranscriptionEngine:

    def __init__(self, engine: str = "auto", whisper_model: str = "small"):
        self.engine_name = engine
        self.whisper_model_size = whisper_model
        self._engine_loaded = None
        self._whisper = None

        if engine == "auto":
            self._auto_detect()
        else:
            self._engine_loaded = engine

    def _auto_detect(self):
        try:
            import whisper
            self._engine_loaded = "whisper"
            print("✅ Using Whisper STT")
        except ImportError:
            try:
                import speech_recognition
                self._engine_loaded = "google"
                print("✅ Using Google SpeechRecognition")
            except ImportError:
                self._engine_loaded = "mock"
                print("⚠️ No STT library found. Using mock mode.")

    # ─────────────────────────────────────────
    # WHISPER
    # ─────────────────────────────────────────

    def _load_whisper(self):
        if self._whisper is None:
            import whisper
            print(f"📥 Loading Whisper model ({self.whisper_model_size})...")
            self._whisper = whisper.load_model(self.whisper_model_size)
        return self._whisper

    def _transcribe_whisper(self, audio_path: str, language: str = None):
        try:
            model = self._load_whisper()
            options = {}
            if language:
                options["language"] = language
            result = model.transcribe(audio_path, **options)

            return {
                "text": result["text"].strip(),
                "language": result.get("language", language or "unknown"),
                "engine": "whisper",
                "success": True,
                "error": None,
            }

        except Exception as e:
            return {
                "text": "",
                "language": language or "unknown",
                "engine": "whisper",
                "success": False,
                "error": str(e),
            }

    # ─────────────────────────────────────────
    # GOOGLE
    # ─────────────────────────────────────────

    def _transcribe_google(self, audio_path: str, language: str = None):
        try:
            import speech_recognition as sr
            r = sr.Recognizer()

            with sr.AudioFile(audio_path) as source:
                audio_data = r.record(source)

            lang_code = language or "en-IN"
            text = r.recognize_google(audio_data, language=lang_code)

            return {
                "text": text,
                "language": language or "en",
                "engine": "google",
                "success": True,
                "error": None,
            }

        except Exception as e:
            return {
                "text": "",
                "language": language or "en",
                "engine": "google",
                "success": False,
                "error": str(e),
            }

    # ─────────────────────────────────────────
    # MOCK
    # ─────────────────────────────────────────

    def _transcribe_mock(self, audio_path: str):
        return {
            "text": "Hello this is CBI officer. You are under digital arrest. Do not disconnect.",
            "language": "en",
            "engine": "mock",
            "success": True,
            "error": None,
        }

    # ─────────────────────────────────────────
    # MAIN ENTRY
    # ─────────────────────────────────────────

    def transcribe_file(self, audio_path: str, language: str = None):

        if not os.path.exists(audio_path):
            return {
                "text": "",
                "language": language or "unknown",
                "engine": self._engine_loaded,
                "success": False,
                "error": "Audio file not found",
            }

        if self._engine_loaded == "whisper":
            return self._transcribe_whisper(audio_path, language)

        elif self._engine_loaded == "google":
            return self._transcribe_google(audio_path, language)

        else:
            return self._transcribe_mock(audio_path)


# ─────────────────────────────────────────────
# VOICE SCAM DETECTOR
# ─────────────────────────────────────────────

class VoiceScamDetector:

    def __init__(self, stt_engine: str = "auto"):
        # GuardianAgent auto-loads scam_model (1).pkl from root
        self.guardian = GuardianAgent()
        self.stt = TranscriptionEngine(engine=stt_engine)
        print("✅ VoiceScamDetector Ready")

    def analyze_file(self, audio_path: str, language: str = None):

        trans = self.stt.transcribe_file(audio_path, language)

        if not trans["success"] or not trans["text"].strip():
            return {
                "risk_score": 0,
                "risk_level": "UNKNOWN",
                "is_scam": False,
                "transcript": trans["text"],
                "error": trans["error"],
            }

        result = self.guardian.analyze(trans["text"])

        result.update({
            "transcript": trans["text"],
            "language": trans["language"],
            "stt_engine": trans["engine"],
            "audio_file": os.path.basename(audio_path),
        })

        return result

    def analyze_transcript(self, text: str):
        result = self.guardian.analyze(text)
        result["transcript"] = text
        result["stt_engine"] = "direct_text"
        return result


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":

    print("🎙 Testing Voice Detector\n")

    vd = VoiceScamDetector(stt_engine="mock")

    test_text = "Hello I am from CBI. You are under digital arrest. Do not disconnect."

    result = vd.analyze_transcript(test_text)

    print("Transcript:", result["transcript"])
    print("Risk Level:", result["risk_level"])
    print("Score     :", result["risk_score"])