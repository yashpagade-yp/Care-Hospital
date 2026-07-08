"""Persistence operations for prescription records."""

from __future__ import annotations

from odmantic.query import desc

from backend.commons.logger import logger
from backend.core.cruds.base_crud import BaseCRUD
from backend.core.models.Prescription import Prescription

logging = logger(__name__)


class CRUDPrescription(BaseCRUD[Prescription]):
    """Database access layer for prescription records."""

    def __init__(self):
        """Initialize the prescription CRUD helper."""

        super().__init__(Prescription)

    async def get_by_appointment_id(self, *, appointment_id: str) -> Prescription | None:
        """Read a prescription linked to an appointment.

        Args:
            appointment_id: Appointment identifier linked to the prescription.

        Returns:
            Prescription | None: Matching prescription when present.
        """

        logging.info("Executing CRUDPrescription.get_by_appointment_id")
        return await self.get_one(Prescription.appointment_id == appointment_id)

    async def get_by_patient_id(self, *, patient_id: str) -> list[Prescription]:
        """Read prescriptions belonging to a patient.

        Args:
            patient_id: Patient user identifier.

        Returns:
            list[Prescription]: Matching prescription records.
        """

        logging.info("Executing CRUDPrescription.get_by_patient_id")
        return await self.get_many(
            Prescription.patient_id == patient_id,
            sort=desc(Prescription.created_at),
        )

    async def get_by_doctor_id(self, *, doctor_id: str) -> list[Prescription]:
        """Read prescriptions created by a doctor.

        Args:
            doctor_id: Doctor user identifier.

        Returns:
            list[Prescription]: Matching prescription records.
        """

        logging.info("Executing CRUDPrescription.get_by_doctor_id")
        return await self.get_many(
            Prescription.doctor_id == doctor_id,
            sort=desc(Prescription.created_at),
        )
