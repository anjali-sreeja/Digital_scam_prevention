import os
import re
import pickle
import urllib.parse


# ─────────────────────────────────────────────
# ML DETECTOR
# ─────────────────────────────────────────────

class MLDetector:

    def __init__(self):
        self.model = None

        # Auto-detect root folder
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(BASE_DIR, "scam_model (1).pkl")

        self._load()

    def _load(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, "rb") as f:
                self.model = pickle.load(f)
            print(f" ML model loaded from: {self.model_path}")
        else:
            print(f" Model not found at: {self.model_path}")

    def _clean(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"http[s]?://\S+", " URL ", text)
        text = re.sub(r"\b(otp|pin|password|cvv)\b", " SENSITIVE ", text)
        text = re.sub(r"digital arrest", " DIGITAL_ARREST ", text)
        text = re.sub(r"[^a-z\s_]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def predict(self, text: str) -> float:
        if self.model is None:
            return 0.5
        return float(self.model.predict_proba([self._clean(text)])[0][1])


# ─────────────────────────────────────────────
# RULE ENGINE
# ─────────────────────────────────────────────

class RuleEngine:

    RULES = (
        (r"digital arrest", 0.50, " Digital arrest claim"),
        (r"do not disconnect|remain on call", 0.40, "Stay on call pressure"),
        (r"cbi|cyber crime|enforcement directorate", 0.40, "Government impersonation"),
        (r"aadhaar|pan.*case|crime", 0.40, "Identity linked to crime"),
        (r"otp|pin|password|cvv", 0.40, "Requesting sensitive info"),
        (r"http[s]?://", 0.30, "Suspicious link"),
    )

    def analyze(self, text: str):
        score = 0.0
        flags = []

        for pattern, weight, label in self.RULES:
            if re.search(pattern, text, re.I):
                score += weight
                flags.append(label)

        return min(score / 1.5, 1.0), flags


# ─────────────────────────────────────────────
# URL CHECKER
# ─────────────────────────────────────────────

class URLChecker:

    def extract(self, text):
        return re.findall(r"http[s]?://\S+", text)

    def analyze(self, text):
        urls = self.extract(text)
        return [{"url": u, "risk": "HIGH"} for u in urls]


# ─────────────────────────────────────────────
# MAIN GUARDIAN AGENT
# ─────────────────────────────────────────────

class GuardianAgent:

    def __init__(self):
        self.ml = MLDetector()
        self.rules = RuleEngine()
        self.urls = URLChecker()

    def analyze(self, message: str) -> dict:

        ml_score = self.ml.predict(message)
        rule_score, flags = self.rules.analyze(message)
        url_results = self.urls.analyze(message)
        url_boost = 0.15 if url_results else 0.0

        combined = (ml_score * 0.55) + (rule_score * 0.35) + url_boost

        if combined < 0.30:
            level = "SAFE"
        elif combined < 0.60:
            level = "SUSPICIOUS"
        else:
            level = "SCAM"

        return {
            "risk_score": round(combined * 100),
            "risk_level": level,
            "is_scam": level == "SCAM",
            "red_flags": flags,
            "url_analysis": url_results
        }


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    agent = GuardianAgent()

    test = "Hello I am from CBI. You are under digital arrest. Do not disconnect."
    result = agent.analyze(test)

    print(result)