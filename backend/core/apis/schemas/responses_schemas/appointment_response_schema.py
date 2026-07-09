"""Appointment and booking response schemas for the MedCare API layer."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.core.models.Appointment import AppointmentStatus, CancelledBy, PaymentStatus, QueueStatus
from backend.core.apis.schemas.responses_schemas.payment_response_schema import PaymentResponse


class SlotHoldResponse(BaseModel):
    """Temporary slot-hold response payload."""

    id: str = Field(..., description="Unique identifier of the slot-hold record")
    patient_id: str = Field(..., description="Patient who is holding the slot")
    doctor_id: str = Field(..., description="Doctor whose slot is being held")
    date_time: datetime = Field(..., description="Held appointment date and time")
    expires_at: datetime = Field(..., description="UTC timestamp when the hold expires")
    created_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the hold record was created",
    )

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AppointmentResponse(BaseModel):
    """Full appointment detail response payload."""

    id: str = Field(..., description="Unique identifier of the appointment")
    patient_id: str = Field(..., description="Patient linked to the appointment")
    doctor_id: str = Field(..., description="Doctor linked to the appointment")
    doctor_name: str | None = Field(default=None, description="Doctor display name for the appointment")
    patient_name: str | None = Field(default=None, description="Patient display name for the appointment")
    patient_phone: str | None = Field(default=None, description="Patient phone linked to the booking")
    patient_age: int | None = Field(default=None, description="Patient age linked to the booking")
    patient_gender: str | None = Field(default=None, description="Patient gender linked to the booking")
    patient_blood_group: str | None = Field(
        default=None,
        description="Patient blood group linked to the booking",
    )
    date_time: datetime = Field(..., description="Scheduled appointment date and time")
    status: AppointmentStatus = Field(..., description="Current appointment status")
    reason: str | None = Field(default=None, description="Optional visit reason")
    queue_number: int | None = Field(default=None, description="Patient token number in the doctor's queue")
    queue_date: date | None = Field(default=None, description="Queue date for the doctor's patient line")
    queue_status: QueueStatus | None = Field(default=None, description="Current queue state for the appointment")
    missed_count: int = Field(default=0, description="Number of missed queue turns")
    current_queue_number: int | None = Field(default=None, description="Current token being served for this doctor")
    patients_before: int | None = Field(default=None, description="Patients still waiting before this appointment")
    total_waiting: int | None = Field(default=None, description="Total active waiting patients for the doctor queue")
    fee: float = Field(..., description="Consultation fee charged for the appointment")
    payment_status: PaymentStatus = Field(..., description="Payment state for the appointment")
    cancelled_by: CancelledBy | None = Field(
        default=None,
        description="Who cancelled the appointment, when applicable",
    )
    cancel_reason: str | None = Field(
        default=None,
        description="Cancellation reason when the appointment was cancelled",
    )
    rescheduled_to_id: str | None = Field(
        default=None,
        description="Identifier of the new appointment created after rescheduling",
    )
    created_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the appointment record was created",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the appointment record was last updated",
    )

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AppointmentListItemResponse(BaseModel):
    """Compact appointment list response payload."""

    id: str = Field(..., description="Unique identifier of the appointment")
    patient_id: str = Field(..., description="Patient linked to the appointment")
    doctor_id: str = Field(..., description="Doctor linked to the appointment")
    doctor_name: str | None = Field(default=None, description="Doctor display name for list views")
    patient_name: str | None = Field(default=None, description="Patient display name for list views")
    patient_phone: str | None = Field(default=None, description="Patient phone for list views")
    patient_age: int | None = Field(default=None, description="Patient age for list views")
    patient_gender: str | None = Field(default=None, description="Patient gender for list views")
    patient_blood_group: str | None = Field(
        default=None,
        description="Patient blood group for list views",
    )
    reason: str | None = Field(default=None, description="Optional visit reason")
    queue_number: int | None = Field(default=None, description="Patient token number in the doctor's queue")
    queue_date: date | None = Field(default=None, description="Queue date for the doctor's patient line")
    queue_status: QueueStatus | None = Field(default=None, description="Current queue state for the appointment")
    missed_count: int = Field(default=0, description="Number of missed queue turns")
    current_queue_number: int | None = Field(default=None, description="Current token being served for this doctor")
    patients_before: int | None = Field(default=None, description="Patients still waiting before this appointment")
    total_waiting: int | None = Field(default=None, description="Total active waiting patients for the doctor queue")
    date_time: datetime = Field(..., description="Scheduled appointment date and time")
    status: AppointmentStatus = Field(..., description="Current appointment status")
    fee: float = Field(..., description="Consultation fee charged for the appointment")

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AppointmentListResponse(BaseModel):
    """Appointment list response payload."""

    items: list[AppointmentListItemResponse] = Field(
        default_factory=list,
        description="Collection of appointment list items",
    )

    model_config = ConfigDict(extra="forbid")


class BookedSlotListResponse(BaseModel):
    """Booked slot datetime list response payload."""

    items: list[datetime] = Field(
        default_factory=list,
        description="Collection of already-booked doctor slot datetimes",
    )

    model_config = ConfigDict(extra="forbid")


class AppointmentDetailResponse(BaseModel):
    """Expanded appointment response with lightweight participant summaries."""

    appointment: AppointmentResponse = Field(..., description="Appointment details")
    patient_name: str | None = Field(
        default=None,
        description="Patient display name for role-specific views",
    )
    doctor_name: str | None = Field(
        default=None,
        description="Doctor display name for role-specific views",
    )
    patient_phone: str | None = Field(
        default=None,
        description="Patient phone linked to the booking",
    )
    patient_age: int | None = Field(
        default=None,
        description="Patient age linked to the booking",
    )
    patient_gender: str | None = Field(
        default=None,
        description="Patient gender linked to the booking",
    )
    patient_blood_group: str | None = Field(
        default=None,
        description="Patient blood group linked to the booking",
    )
    reason: str | None = Field(
        default=None,
        description="Patient-provided visit reason",
    )

    model_config = ConfigDict(extra="forbid")


class AppointmentConfirmationResponse(BaseModel):
    """Appointment confirmation response payload."""

    appointment: AppointmentResponse = Field(
        ...,
        description="Confirmed appointment details",
    )
    payment: PaymentResponse = Field(
        ...,
        description="Mock payment recorded for the booking",
    )
    patient_name: str | None = Field(
        default=None,
        description="Patient display name confirmed during booking",
    )
    doctor_name: str | None = Field(
        default=None,
        description="Doctor display name linked to the booking",
    )

    model_config = ConfigDict(extra="forbid")


class AppointmentRescheduleResponse(BaseModel):
    """Appointment reschedule response payload."""

    previous_appointment: AppointmentResponse = Field(
        ...,
        description="Original appointment updated to the rescheduled state",
    )
    new_appointment: AppointmentResponse = Field(
        ...,
        description="New appointment created for the replacement slot",
    )

    model_config = ConfigDict(extra="forbid")

