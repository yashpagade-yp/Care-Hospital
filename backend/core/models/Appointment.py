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

    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    RESCHEDULED = "RESCHEDULED"


class PaymentStatus(str, Enum):
    """Defines the payment states stored on an appointment."""

    PAID = "PAID"
    REFUNDED = "REFUNDED"


class QueueStatus(str, Enum):
    """Defines where an appointment sits in the doctor's daily queue."""

    WAITING = "WAITING"
    MISSED = "MISSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CancelledBy(str, Enum):
    """Defines who cancelled the appointment."""

    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"


class Appointment(Model):
    """Represents a booked appointment between a patient and a doctor.

    The model is created only after the temporary slot hold succeeds and mock
    payment is completed, then stores the confirmed booking lifecycle.
    """

    patient_id: str = Field(..., description="Identifier of the patient user")
    doctor_id: str = Field(..., description="Identifier of the doctor user")
    telegram_user_id: Optional[str] = Field(
        default=None,
        description="Telegram user identifier for guest bookings before registration",
    )
    patient_name: Optional[str] = Field(
        default=None,
        description="Patient name snapshot captured at booking time",
    )
    patient_phone: Optional[str] = Field(
        default=None,
        description="Patient phone snapshot captured at booking time",
    )
    patient_age: Optional[int] = Field(
        default=None,
        ge=0,
        le=120,
        description="Patient age confirmed during booking",
    )
    patient_gender: Optional[str] = Field(
        default=None,
        description="Patient gender confirmed during booking",
    )
    patient_blood_group: Optional[str] = Field(
        default=None,
        description="Optional patient blood group captured during booking",
    )
    date_time: datetime = Field(..., description="Scheduled date and time of the appointment")
    status: AppointmentStatus = Field(
        default=AppointmentStatus.CONFIRMED,
        description="Current lifecycle state of the confirmed appointment",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Optional patient-provided reason for the visit",
    )
    queue_number: Optional[int] = Field(
        default=None,
        ge=1,
        description="Patient token number in the doctor's daily queue",
    )
    queue_date: Optional[str] = Field(
        default=None,
        description="Doctor queue date used to group daily patient tokens",
    )
    queue_status: QueueStatus = Field(
        default=QueueStatus.WAITING,
        description="Current queue state for this appointment",
    )
    missed_count: int = Field(
        default=0,
        ge=0,
        description="Number of times the patient missed their queue turn",
    )
    fee: float = Field(..., ge=0, description="Appointment consultation fee")
    payment_status: PaymentStatus = Field(
        default=PaymentStatus.PAID,
        description="Mock payment state captured for the confirmed appointment",
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
