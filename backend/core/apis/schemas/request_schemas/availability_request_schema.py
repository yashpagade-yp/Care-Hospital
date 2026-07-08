"""Doctor availability request schemas for the MedCare API layer."""

from datetime import date, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.core.models.DoctorAvailability import AvailabilityType, DayOfWeek


class AvailabilityUpsertRequest(BaseModel):
    """Availability create or update payload for recurring and exception entries."""

    availability_type: AvailabilityType = Field(
        ...,
        description="Whether the entry is recurring, exception available, or exception blocked",
    )
    day_of_week: Optional[DayOfWeek] = Field(
        default=None,
        description="Recurring day for weekly availability entries",
    )
    start_time: time = Field(..., description="Start time for the availability window")
    end_time: time = Field(..., description="End time for the availability window")
    exception_date: Optional[date] = Field(
        default=None,
        description="Specific date used only for exception-based availability entries",
    )

    @model_validator(mode="after")
    def validate_type_specific_fields(self) -> "AvailabilityUpsertRequest":
        """Validate recurring versus exception field combinations."""
        if self.availability_type == AvailabilityType.RECURRING:
            if self.day_of_week is None:
                raise ValueError("day_of_week is required for recurring availability")
            if self.exception_date is not None:
                raise ValueError("exception_date is not allowed for recurring availability")
        else:
            if self.exception_date is None:
                raise ValueError("exception_date is required for exception availability")
        return self

    model_config = ConfigDict(extra="forbid")


class UpdateAvailabilityRequest(BaseModel):
    """Availability update payload for doctors editing an existing slot."""

    start_time: Optional[time] = Field(
        default=None,
        description="Updated start time for the availability entry",
    )
    end_time: Optional[time] = Field(
        default=None,
        description="Updated end time for the availability entry",
    )
    day_of_week: Optional[DayOfWeek] = Field(
        default=None,
        description="Updated recurring day if the entry is recurring",
    )
    exception_date: Optional[date] = Field(
        default=None,
        description="Updated exception date if the entry is exception-based",
    )

    model_config = ConfigDict(extra="forbid")


class AdminOverrideAvailabilityRequest(BaseModel):
    """Admin emergency override payload for doctor availability."""

    doctor_id: str = Field(..., description="Doctor whose availability is being overridden")
    availability_type: AvailabilityType = Field(
        ...,
        description="Type of override entry being added by the admin",
    )
    start_time: time = Field(..., description="Start time for the override window")
    end_time: time = Field(..., description="End time for the override window")
    exception_date: date = Field(..., description="Specific date for the override window")
    reason: Optional[str] = Field(
        default=None,
        description="Optional operational reason for the admin override",
    )

    model_config = ConfigDict(extra="forbid")

