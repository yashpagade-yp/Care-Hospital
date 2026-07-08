"""Persistence operations for appointment records."""

from __future__ import annotations

from datetime import datetime

from odmantic.query import desc

from backend.commons.logger import logger
from backend.core.cruds.base_crud import BaseCRUD
from backend.core.models.Appointment import Appointment, AppointmentStatus

logging = logger(__name__)


class CRUDAppointment(BaseCRUD[Appointment]):
    """Database access layer for appointment records."""

    def __init__(self):
        """Initialize the appointment CRUD helper."""

        super().__init__(Appointment)

    async def get_by_patient_id(self, *, patient_id: str) -> list[Appointment]:
        """Read appointments belonging to a patient.

        Args:
            patient_id: Patient user identifier.

        Returns:
            list[Appointment]: Matching patient appointments.
        """

        logging.info("Executing CRUDAppointment.get_by_patient_id")
        return await self.get_many(
            Appointment.patient_id == patient_id,
            sort=desc(Appointment.date_time),
        )

    async def get_by_doctor_id(self, *, doctor_id: str) -> list[Appointment]:
        """Read appointments belonging to a doctor.

        Args:
            doctor_id: Doctor user identifier.

        Returns:
            list[Appointment]: Matching doctor appointments.
        """

        logging.info("Executing CRUDAppointment.get_by_doctor_id")
        return await self.get_many(
            Appointment.doctor_id == doctor_id,
            sort=desc(Appointment.date_time),
        )

    async def get_by_doctor_and_datetime(
        self,
        *,
        doctor_id: str,
        date_time: datetime,
    ) -> Appointment | None:
        """Read an appointment for a specific doctor slot.

        Args:
            doctor_id: Doctor user identifier.
            date_time: Exact scheduled appointment time.

        Returns:
            Appointment | None: Matching appointment when present.
        """

        logging.info("Executing CRUDAppointment.get_by_doctor_and_datetime")
        return await self.get_one(
            Appointment.doctor_id == doctor_id,
            Appointment.date_time == date_time,
        )

    async def get_by_status(self, *, status: AppointmentStatus) -> list[Appointment]:
        """Read appointments filtered by lifecycle status.

        Args:
            status: Appointment lifecycle state.

        Returns:
            list[Appointment]: Matching appointments.
        """

        logging.info("Executing CRUDAppointment.get_by_status")
        return await self.get_many(
            Appointment.status == status,
            sort=desc(Appointment.date_time),
        )

    async def get_all(self) -> list[Appointment]:
        """Read all appointments for admin operational views.

        Returns:
            list[Appointment]: All appointment records ordered by scheduled time.
        """

        logging.info("Executing CRUDAppointment.get_all")
        return await self.get_many(sort=desc(Appointment.date_time))
