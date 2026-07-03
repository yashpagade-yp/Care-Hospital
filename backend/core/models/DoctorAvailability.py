"""Doctor availability persistence model for the MedCare platform.

This model stores recurring doctor schedule slots and optional exception-based
availability entries used during appointment booking.
"""

from datetime import datetime, timezone
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


class AvailabilityType(str, Enum):
    """Defines the supported availability entry types.

    The type distinguishes recurring weekly availability from date-specific
    overrides that either add extra time or block time exceptionally.
    """

    RECURRING = "RECURRING"
    EXCEPTION_AVAILABLE = "EXCEPTION_AVAILABLE"
    EXCEPTION_BLOCKED = "EXCEPTION_BLOCKED"


class DoctorAvailability(Model):
    """Represents a doctor availability slot stored in the database.

    The model supports both recurring weekly slots and exception-based entries
    for specific dates.
    """

    doctor_id: str = Field(
        ...,
        description="Identifier of the doctor user who owns this availability slot",
    )
    availability_type: AvailabilityType = Field(
        default=AvailabilityType.RECURRING,
        description="Type of recurring slot or date-specific override being stored",
    )
    day_of_week: Optional[DayOfWeek] = Field(
        default=None,
        description="Recurring working day for weekly availability entries",
    )
    start_time: str = Field(..., description="Slot start time as HH:MM string")
    end_time: str = Field(..., description="Slot end time as HH:MM string")
    exception_date: Optional[str] = Field(
        default=None,
        description="Specific date (YYYY-MM-DD) used only for date-specific availability overrides",
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
