"""Doctor availability persistence model for the MedCare platform.

This model stores recurring doctor schedule slots and optional exception-based
availability entries used during appointment booking.
"""

from datetime import date, datetime, time, timezone
from enum import Enum
from typing import Optional

from odmantic import Field, Model


class DayOfWeek(str, Enum):
    """Defines the supported working days for recurring doctor schedules."""

    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class DoctorAvailability(Model):
    """Represents a doctor availability slot stored in the database.

    The model supports both recurring weekly slots and exception-based entries
    for specific dates.
    """

    doctor_id: str = Field(
        ...,
        description="Identifier of the doctor user who owns this availability slot",
    )
    day_of_week: DayOfWeek = Field(
        ...,
        description="Recurring working day for the availability slot",
    )
    start_time: time = Field(..., description="Slot start time")
    end_time: time = Field(..., description="Slot end time")
    is_exception: bool = Field(
        default=False,
        description="Indicates whether this entry is a date-specific exception",
    )
    exception_date: Optional[date] = Field(
        default=None,
        description="Specific date for exception-based availability entries",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the availability record was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the availability record was last updated",
    )

    model_config = {
        "collection": "doctor_availabilities",
        "extra": "forbid",
    }
