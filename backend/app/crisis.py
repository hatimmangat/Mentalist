"""
Lightweight crisis keyword/phrase detection. Runs on every incoming user
message before the LLM call; if it fires, crisis-protocol context is
force-injected regardless of vector similarity, and the response is flagged.

This is a safety net, not a diagnostic tool - deliberately biased toward
over-triggering (false positives are cheap; missed detections are not).
"""
import re

CRISIS_PATTERNS = [
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bsuicid\w*\b",
    r"\bwant to die\b",
    r"\bdon'?t want to (be alive|live)\b",
    r"\bno reason to live\b",
    r"\bself[\s-]?harm\w*\b",
    r"\bcut(ting)? myself\b",
    r"\bhurt myself\b",
    r"\bbetter off (without me|dead)\b",
    r"\bcan'?t (go on|do this anymore)\b",
    r"\bgoing to (end it|kill)\b",
    r"\bhave a plan\b.*\b(die|end)\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in CRISIS_PATTERNS]

# Pakistan-specific crisis resources. Helpline numbers and availability can
# change over time - worth double-checking these periodically against the
# organizations' own websites before relying on them in a live deployment.
CRISIS_RESOURCE_MESSAGE = (
    "Umang Pakistan's mental health helpline: 0311-7786264 (daily, evenings). "
    "Rozan's counselling helpline: 0304-111-1741. "
    "If there is immediate danger, please contact Rescue 1122 or go to your nearest emergency room."
)


def detect_crisis(message: str) -> bool:
    return any(pattern.search(message) for pattern in _COMPILED)
