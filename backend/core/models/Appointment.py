"""Appointment persistence model for the MedCare platform.

This model stores the booking relationship between a patient and a doctor,
including status, payment state, and cancellation or reschedule details.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from odmantic import Field, Model


class AppointmentStatus(str, Enum):
    """Defines the supported appointment lifecycle states."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    RESCHEDULED = "RESCHEDULED"


class PaymentStatus(str, Enum):
    """Defines the payment states stored on an appointment."""

    PENDING = "PENDING"
    PAID = "PAID"
    REFUNDED = "REFUNDED"


class CancelledBy(str, Enum):
    """Defines who cancelled the appointment."""

    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"


class Appointment(Model):
    """Represents a booked appointment between a patient and a doctor.

    The model is the core booking record and stores timing, status, payment,
    and cancellation or reschedule references.
    """

    patient_id: str = Field(..., description="Identifier of the patient user")
    doctor_id: str = Field(..., description="Identifier of the doctor user")
    date_time: datetime = Field(..., description="Scheduled date and time of the appointment")
    status: AppointmentStatus = Field(
        default=AppointmentStatus.CONFIRMED,
        description="Current lifecycle state of the appointment",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Optional patient-provided reason for the visit",
    )
    fee: float = Field(..., ge=0, description="Appointment consultation fee")
    payment_status: PaymentStatus = Field(
        default=PaymentStatus.PENDING,
        description="Mock payment state for the appointment",
    )
    cancelled_by: Optional[CancelledBy] = Field(
        default=None,
        description="Role that cancelled the appointment if cancellation occurred",
    )
    cancel_reason: Optional[str] = Field(
        default=None,
        description="Reason recorded when the appointment is cancelled",
    )
    rescheduled_to_id: Optional[str] = Field(
        default=None,
        description="Identifier of the new appointment created during reschedule",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the appointment record was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the appointment record was last updated",
    )

    model_config = {
        "collection": "appointments",
        "extra": "forbid",
    }
