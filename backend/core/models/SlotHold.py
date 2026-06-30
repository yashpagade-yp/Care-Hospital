"""Temporary slot-hold persistence model for the MedCare platform.

This model stores short-lived booking locks created while a patient completes
the appointment confirmation and mock payment flow.
"""

from datetime import datetime, timezone

from odmantic import Field, Index, Model


class SlotHold(Model):
    """Represents a temporary reservation for a doctor time slot.

    The hold protects a doctor slot from double-booking for a short window
    before payment succeeds and a confirmed appointment is created.
    """

    patient_id: str = Field(
        ...,
        description="Identifier of the patient attempting to reserve the slot",
    )
    doctor_id: str = Field(
        ...,
        description="Identifier of the doctor whose slot is being held",
    )
    date_time: datetime = Field(
        ...,
        description="Date and time of the slot being held",
    )
    expires_at: datetime = Field(
        ...,
        description="UTC timestamp when the temporary hold automatically expires",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the hold record was created",
    )

    model_config = {
        "collection": "slot_holds",
        "extra": "forbid",
        "indexes": lambda: [
            Index(SlotHold.doctor_id, SlotHold.date_time, unique=True),
            Index(SlotHold.expires_at),
        ],
    }
