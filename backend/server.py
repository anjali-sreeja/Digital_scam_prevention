"""
STEP 4 — FASTAPI SERVER (SMS + Voice)
Run:
    uvicorn backend.server:app --reload --port 8000

Docs:
    http://127.0.0.1:8000/docs
"""

import os
import sys
import tempfile
import shutil

# Ensure root folder is accessible
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.detector import GuardianAgent
from backend.voice_detector import VoiceScamDetector


# ─────────────────────────────────────────────
# FASTAPI INIT
# ─────────────────────────────────────────────

app = FastAPI(
    title="Guardian Angel API",
    description="AI Scam Detection — SMS + Voice",
    version="3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# LAZY LOAD (Better Performance)
# ─────────────────────────────────────────────

_agent = None
_voice_detector = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = GuardianAgent()
    return _agent


def get_voice_detector():
    global _voice_detector
    if _voice_detector is None:
        _voice_detector = VoiceScamDetector()
    return _voice_detector


# ─────────────────────────────────────────────
# REQUEST MODEL
# ─────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=5,
        max_length=5000,
        json_schema_extra={
            "example": "Hello I am Inspector Rao from CBI. You are under digital arrest."
        }
    )

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "Guardian Angel Active 🛡️",
        "version": "3.0",
        "docs": "/docs"
    }


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """
    Analyze SMS or voice transcript text
    """
    result = get_agent().analyze(req.message.strip())
    return result


@app.post("/analyze-voice")
async def analyze_voice(
    file: UploadFile = File(...),
    language: str = Form(default=None)
):
    """
    Upload audio file and detect scam

    Supported formats:
    .mp3, .m4a, .wav, .ogg, .flac
    """

    allowed_extensions = ['.mp3', '.m4a', '.wav', '.ogg', '.flac']
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format {ext}. Allowed: {allowed_extensions}"
        )

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    try:
        vd = get_voice_detector()
        result = vd.analyze_file(temp_path, language=language)

        result["original_filename"] = file.filename
        return result

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/examples")
def examples():
    return {
        "sms_scam": [
            "URGENT: Your SBI bank account BLOCKED. Update KYC: http://sbi-kyc.tk",
            "You WON Rs 50 Lakh! Call 9876543210 to claim NOW!"
        ],
        "voice_scam_transcripts": [
            "Hello. I am Inspector Rao from Cyber Crime Unit. You are under digital arrest. Do not disconnect.",
            "Namaste. Main CBI se bol raha hoon. Aap digital arrest mein hain. Phone mat kaatna."
        ],
        "safe": [
            "Hi beta, aaj dinner mein dal chawal banana.",
            "Hello this is Dr. Sharma confirming your 10 AM appointment tomorrow."
        ]
    }