from __future__ import annotations

import re

TECH_TERMS = (
    "ai",
    "artificial intelligence",
    "machine learning",
    "software",
    "digital",
    "automation",
    "telemetry",
    "iot",
    "connected",
    "cloud",
    "data",
    "dashboard",
    "robot",
    "sensor",
    "algorithm",
    "tech",
    "technology",
    "research",
    "innovation",
    "smart",
    "app",
    "platform",
    "saas",
)


def tech_score(*parts: str) -> int:
    blob = " ".join(p for p in parts if p).casefold()
    score = 0
    for term in TECH_TERMS:
        if term in blob:
            score += 3 if term in {"ai", "artificial intelligence", "software", "automation", "telemetry", "iot"} else 1
    if re.search(r"\bai\b", blob):
        score += 4
    return score
