"""Doctor availability response schemas for the MedCare API layer."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.core.models.DoctorAvailability import AvailabilityType, DayOfWeek


class DoctorAvailabilityResponse(BaseModel):
    """Doctor availability detail response payload."""

    id: str = Field(..., description="Unique identifier of the availability entry")
    doctor_id: str = Field(..., description="Doctor who owns the availability entry")
    availability_type: AvailabilityType = Field(
        ...,
        description="Type of recurring or exception availability entry",
    )
    day_of_week: DayOfWeek | None = Field(
        default=None,
        description="Recurring working day for weekly availability entries",
    )
    # Stored as HH:MM strings in MongoDB (datetime.time is not encodable by ODMantic)
    start_time: str = Field(..., description="Start time of the availability window (HH:MM)")
    end_time: str = Field(..., description="End time of the availability window (HH:MM)")
    # Stored as YYYY-MM-DD string (datetime.date is not encodable by ODMantic)
    exception_date: str | None = Field(
        default=None,
        description="Specific date for exception-based availability entries (YYYY-MM-DD)",
    )
    created_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the availability record was created",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the availability record was last updated",
    )

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class DoctorAvailabilityListResponse(BaseModel):
    """Doctor availability list response payload."""

    items: list[DoctorAvailabilityResponse] = Field(
        default_factory=list,
        description="Collection of availability entries for the doctor",
    )

    model_config = ConfigDict(extra="forbid")
