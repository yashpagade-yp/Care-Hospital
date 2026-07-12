from __future__ import annotations

from enum import StrEnum


class Intent(StrEnum):
    DOCTOR_INFO = "doctor_info"
    BOOK = "book"
    REGISTER = "register"
    APPOINTMENTS = "appointments"
    AVAILABILITY = "availability"
    CANCEL = "cancel"
    RESCHEDULE = "reschedule"
    PRESCRIPTION = "prescription"
    FAQ = "faq"
    UNKNOWN = "unknown"


def detect_intent(message: str) -> Intent:
    lowered = message.lower()
    normalized = lowered.strip()
    if "cancel" in lowered:
        return Intent.CANCEL
    if any(word in lowered for word in {"रद्द", "कॅन्सल", "कैंसल"}):
        return Intent.CANCEL
    if "reschedule" in lowered or "change appointment" in lowered:
        return Intent.RESCHEDULE
    if any(word in lowered for word in {"वेळ बदला", "तारीख बदला", "पुन्हा वेळ", "बदलना", "बदलो"}):
        return Intent.RESCHEDULE
    if "prescription" in lowered or "medicine" in lowered:
        return Intent.PRESCRIPTION
    if any(word in lowered for word in {"प्रिस्क्रिप्शन", "औषध", "दवा", "पर्ची"}):
        return Intent.PRESCRIPTION
    if any(
        phrase in lowered
        for phrase in {
            "new user",
            "new patient",
            "patient registration",
            "register patient",
            "registration",
            "create account",
            "create my account",
            "not registered",
            "don't have any past record",
            "do not have any past record",
        }
    ):
        return Intent.REGISTER
    if any(word in lowered for word in {"नोंदणी", "रजिस्टर", "रजिस्ट्रेशन", "नया मरीज", "नवीन रुग्ण"}):
        return Intent.REGISTER
    if any(
        phrase in lowered
        for phrase in {"doctor information", "doctor info", "show me doctors", "show doctors", "list doctors"}
    ):
        return Intent.DOCTOR_INFO
    if normalized in {"doctor", "doctors", "डॉक्टर", "डॉक्टर्स"}:
        return Intent.DOCTOR_INFO
    if "doctor" in lowered and any(
        word in lowered
        for word in {"show", "list", "specialist", "specialty", "specialities", "specialties", "available", "present"}
    ):
        return Intent.DOCTOR_INFO
    if any(
        word in lowered
        for word in {
            "skin",
            "skincare",
            "dermatology",
            "orthopedic",
            "bone",
            "general physician",
            "pediatric",
            "cardiology",
            "neurology",
            "gynecology",
            "ent",
            "eye",
        }
    ) and any(word in lowered for word in {"doctor", "specialist", "specialty", "field"}):
        return Intent.DOCTOR_INFO
    if any(word in lowered for word in {"डॉक्टर", "विशेषज्ञ", "तज्ज्ञ", "स्पेशलिस्ट"}):
        return Intent.DOCTOR_INFO
    if "appointment" in lowered and any(
        word in lowered for word in {"show", "list", "my", "upcoming", "history", "status"}
    ):
        return Intent.APPOINTMENTS
    if any(word in lowered for word in {"book", "schedule"}) and "appointment" in lowered:
        return Intent.BOOK
    if any(word in lowered for word in {"अपॉइंटमेंट", "अपॉईंटमेंट", "भेट", "मुलाकात"}) and any(
        word in lowered for word in {"बुक", "करायची", "करना", "घ्यायची", "चाहिए"}
    ):
        return Intent.BOOK
    if "availability" in lowered:
        return Intent.AVAILABILITY
    if "doctor" in lowered and any(word in lowered for word in {"time", "timing", "hours", "working"}):
        return Intent.AVAILABILITY
    if any(word in lowered for word in {"वेळ", "टाइम", "समय", "उपलब्ध", "available"}):
        return Intent.AVAILABILITY
    if any(word in lowered for word in {"hour", "timing", "address", "location", "faq"}):
        return Intent.FAQ
    if any(word in lowered for word in {"पत्ता", "स्थान", "अस्पताल", "हॉस्पिटल", "रुग्णालय"}):
        return Intent.FAQ
    return Intent.UNKNOWN


def normalize_intent_label(label: str) -> Intent:
    try:
        return Intent(label.strip().lower())
    except ValueError:
        return Intent.UNKNOWN
