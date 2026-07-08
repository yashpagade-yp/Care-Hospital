from __future__ import annotations


FAQ_RESPONSES = {
    "hours": "Please check the hospital reception for exact visiting hours. If you want, I can still help with appointments or prescription lookup here.",
    "timing": "Hospital timings can vary by department. Please confirm with the hospital directly for final timings.",
    "address": "Please refer to the hospital contact information shared by the hospital administration for the exact address and directions.",
    "location": "Please refer to the hospital contact information shared by the hospital administration for the exact location and directions.",
    "emergency": "For emergencies, please contact local emergency services or the hospital emergency desk immediately. I cannot provide emergency medical advice here.",
}


def answer_faq(message: str) -> str:
    lowered = message.lower()
    for keyword, response in FAQ_RESPONSES.items():
        if keyword in lowered:
            return response
    return (
        "I can help with hospital FAQs, appointments, and existing prescriptions. "
        "If your question is about diagnosis, emergency advice, or changing medicines, please contact the hospital or doctor directly."
    )
