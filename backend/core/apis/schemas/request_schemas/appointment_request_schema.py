"""Appointment and booking request schemas for the MedCare API layer."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.core.models.Appointment import AppointmentStatus


class CreateSlotHoldRequest(BaseModel):
    """Initial slot-hold request payload during booking step one."""

    doctor_id: str = Field(..., description="Doctor whose slot the patient wants to hold")
    date_time: datetime = Field(..., description="Appointment date and time being reserved")

    model_config = ConfigDict(extra="forbid")


class ConfirmAppointmentRequest(BaseModel):
    """Final booking confirmation payload after patient detail review."""

    slot_hold_id: str = Field(
        ...,
        description="Temporary slot-hold identifier created during booking step one",
    )
    patient_name: str = Field(..., min_length=2, description="Patient name confirmed for the booking")
    patient_phone: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="Patient phone number confirmed for the booking",
    )
    patient_age: int = Field(
        ...,
        ge=0,
        le=120,
        description="Patient age confirmed for the booking",
    )
    patient_gender: str = Field(
        ...,
        min_length=1,
        description="Patient gender confirmed for the booking",
    )
    patient_blood_group: Optional[str] = Field(
        default=None,
        description="Optional patient blood group confirmed for the booking",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Optional reason for the consultation or visit",
    )
    fee: float = Field(..., ge=0, description="Consultation fee charged during mock payment")

    model_config = ConfigDict(extra="forbid")


class TelegramGuestAppointmentRequest(BaseModel):
    """Public Telegram booking payload for lightweight guest appointments."""

    doctor_id: str = Field(..., description="Doctor selected by the Telegram patient")
    date_time: datetime = Field(..., description="Requested appointment date and time")
    patient_name: str = Field(..., min_length=2, description="Patient name captured in Telegram")
    patient_age: int = Field(..., ge=0, le=120, description="Patient age captured in Telegram")
    patient_gender: str = Field(..., min_length=1, description="Patient gender captured in Telegram")
    patient_blood_group: Optional[str] = Field(
        default=None,
        description="Optional patient blood group captured in Telegram",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Optional reason for the consultation or visit",
    )
    fee: float = Field(default=0, ge=0, description="Consultation fee charged during mock payment")

    model_config = ConfigDict(extra="forbid")


class CancelAppointmentRequest(BaseModel):
    """Appointment cancellation payload for patients and doctors."""

    cancel_reason: str = Field(..., min_length=2, description="Reason for appointment cancellation")

    model_config = ConfigDict(extra="forbid")


class RescheduleAppointmentRequest(BaseModel):
    """Appointment reschedule payload for moving a booking to a new slot."""

    new_date_time: datetime = Field(..., description="New appointment date and time requested")
    reason: Optional[str] = Field(
        default=None,
        description="Optional reason for rescheduling the appointment",
    )

    model_config = ConfigDict(extra="forbid")


class UpdateAppointmentStatusRequest(BaseModel):
    """Doctor status update payload for appointment lifecycle changes."""

    status: AppointmentStatus = Field(
        ...,
        description="New appointment status allowed for the requested transition",
    )

    model_config = ConfigDict(extra="forbid")

