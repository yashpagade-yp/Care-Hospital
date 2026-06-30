"""Doctor availability response schemas for the MedCare API layer."""

from datetime import date, datetime, time

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
    start_time: time = Field(..., description="Start time of the availability window")
    end_time: time = Field(..., description="End time of the availability window")
    exception_date: date | None = Field(
        default=None,
        description="Specific date for exception-based availability entries",
    )
    created_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the availability record was created",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the availability record was last updated",
    )

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class DoctorAvailabilityListResponse(BaseModel):
    """Doctor availability list response payload."""

    items: list[DoctorAvailabilityResponse] = Field(
        default_factory=list,
        description="Collection of availability entries for the doctor",
    )

    model_config = ConfigDict(extra="forbid")

