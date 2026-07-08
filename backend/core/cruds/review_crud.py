"""Persistence operations for review records."""

from __future__ import annotations

from odmantic.query import desc

from backend.commons.logger import logger
from backend.core.cruds.base_crud import BaseCRUD
from backend.core.models.Review import Review

logging = logger(__name__)


class CRUDReview(BaseCRUD[Review]):
    """Database access layer for review records."""

    def __init__(self):
        """Initialize the review CRUD helper."""

        super().__init__(Review)

    async def get_by_appointment_id(self, *, appointment_id: str) -> Review | None:
        """Read a review linked to an appointment.

        Args:
            appointment_id: Appointment identifier being reviewed.

        Returns:
            Review | None: Matching review record when present.
        """

        logging.info("Executing CRUDReview.get_by_appointment_id")
        return await self.get_one(Review.appointment_id == appointment_id)

    async def get_by_doctor_id(
        self,
        *,
        doctor_id: str,
        include_hidden: bool = False,
    ) -> list[Review]:
        """Read reviews submitted for a doctor.

        Args:
            doctor_id: Doctor user identifier.
            include_hidden: Whether hidden reviews should be included.

        Returns:
            list[Review]: Matching review records.
        """

        logging.info("Executing CRUDReview.get_by_doctor_id")
        filters = [Review.doctor_id == doctor_id]
        if not include_hidden:
            filters.append(Review.is_hidden == False)

        return await self.get_many(*filters, sort=desc(Review.created_at))
