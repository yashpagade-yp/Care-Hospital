from __future__ import annotations

from enum import StrEnum


class Intent(StrEnum):
    BOOK = "book"
    AVAILABILITY = "availability"
    CANCEL = "cancel"
    RESCHEDULE = "reschedule"
    PRESCRIPTION = "prescription"
    FAQ = "faq"
    UNKNOWN = "unknown"


def detect_intent(message: str) -> Intent:
    lowered = message.lower()
    if any(word in lowered for word in {"book", "appointment", "schedule"}):
        return Intent.BOOK
    if "availability" in lowered or "available" in lowered:
        return Intent.AVAILABILITY
    if "cancel" in lowered:
        return Intent.CANCEL
    if "reschedule" in lowered or "change appointment" in lowered:
        return Intent.RESCHEDULE
    if "prescription" in lowered or "medicine" in lowered:
        return Intent.PRESCRIPTION
    if any(word in lowered for word in {"hour", "timing", "address", "location", "faq"}):
        return Intent.FAQ
    return Intent.UNKNOWN


def normalize_intent_label(label: str) -> Intent:
    try:
        return Intent(label.strip().lower())
    except ValueError:
        return Intent.UNKNOWN
