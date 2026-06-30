"""Persistence operations for temporary slot-hold records."""

from __future__ import annotations

from datetime import datetime, timezone

from odmantic.query import desc

from backend.commons.logger import logger
from backend.core.cruds.base_crud import BaseCRUD
from backend.core.database.database import get_engine
from backend.core.models.SlotHold import SlotHold

logging = logger(__name__)


class CRUDSlotHold(BaseCRUD[SlotHold]):
    """Database access layer for temporary slot-hold records."""

    def __init__(self):
        """Initialize the slot-hold CRUD helper."""

        super().__init__(SlotHold)

    async def get_active_hold(
        self,
        *,
        doctor_id: str,
        date_time: datetime,
    ) -> SlotHold | None:
        """Read the currently active hold for a doctor slot.

        Args:
            doctor_id: Doctor user identifier.
            date_time: Exact slot date and time being checked.

        Returns:
            SlotHold | None: Matching active slot hold when present.
        """

        logging.info("Executing CRUDSlotHold.get_active_hold")
        return await self.get_one(
            SlotHold.doctor_id == doctor_id,
            SlotHold.date_time == date_time,
            SlotHold.expires_at > datetime.now(timezone.utc),
        )

    async def get_by_patient_id(self, *, patient_id: str) -> list[SlotHold]:
        """Read slot holds created by a patient.

        Args:
            patient_id: Patient user identifier.

        Returns:
            list[SlotHold]: Matching slot-hold records.
        """

        logging.info("Executing CRUDSlotHold.get_by_patient_id")
        return await self.get_many(
            SlotHold.patient_id == patient_id,
            sort=desc(SlotHold.created_at),
        )

    async def delete_expired_holds(self) -> int:
        """Delete slot-hold records that have already expired.

        Returns:
            int: Number of expired holds removed from the database.
        """

        try:
            logging.info("Executing CRUDSlotHold.delete_expired_holds")
            expired_holds = await self.get_many(
                SlotHold.expires_at < datetime.now(timezone.utc)
            )
            engine = get_engine()
            for slot_hold in expired_holds:
                await engine.delete(slot_hold)

            return len(expired_holds)
        except Exception as error:
            logging.error(f"Error in CRUDSlotHold.delete_expired_holds: {error}")
            raise
