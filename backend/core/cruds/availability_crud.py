"""Persistence operations for doctor availability records."""

from __future__ import annotations


from backend.commons.logger import logger
from backend.core.cruds.base_crud import BaseCRUD
from backend.core.models.DoctorAvailability import (
    AvailabilityType,
    DayOfWeek,
    DoctorAvailability,
)

logging = logger(__name__)


class CRUDDoctorAvailability(BaseCRUD[DoctorAvailability]):
    """Database access layer for doctor availability records."""

    def __init__(self):
        """Initialize the doctor availability CRUD helper."""

        super().__init__(DoctorAvailability)

    async def get_by_doctor_id(self, *, doctor_id: str) -> list[DoctorAvailability]:
        """Read all availability entries for a doctor.

        Args:
            doctor_id: Doctor user identifier.

        Returns:
            list[DoctorAvailability]: Matching availability entries.
        """

        logging.info("Executing CRUDDoctorAvailability.get_by_doctor_id")
        return await self.get_many(
            DoctorAvailability.doctor_id == doctor_id,
            sort=DoctorAvailability.start_time,
        )

    async def get_recurring_slots(
        self,
        *,
        doctor_id: str,
        day_of_week: DayOfWeek,
    ) -> list[DoctorAvailability]:
        """Read recurring schedule slots for a doctor and weekday.

        Args:
            doctor_id: Doctor user identifier.
            day_of_week: Weekly schedule day to filter on.

        Returns:
            list[DoctorAvailability]: Matching recurring slots.
        """

        logging.info("Executing CRUDDoctorAvailability.get_recurring_slots")
        return await self.get_many(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.availability_type == AvailabilityType.RECURRING,
            DoctorAvailability.day_of_week == day_of_week,
            sort=DoctorAvailability.start_time,
        )

    async def get_exception_slots(
        self,
        *,
        doctor_id: str,
        exception_date: str,
    ) -> list[DoctorAvailability]:
        """Read date-specific availability overrides for a doctor.

        Args:
            doctor_id: Doctor user identifier.
            exception_date: Specific calendar date for the exception lookup.

        Returns:
            list[DoctorAvailability]: Matching exception availability entries.
        """

        logging.info("Executing CRUDDoctorAvailability.get_exception_slots")
        return await self.get_many(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.exception_date == exception_date,
            sort=DoctorAvailability.start_time,
        )
