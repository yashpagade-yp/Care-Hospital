"""Prescription controller logic for consultation follow-up workflows."""

from __future__ import annotations

from fastapi import HTTPException, status

from backend.commons.logger import logger
from backend.core.controllers.base_controller import BaseController
from backend.core.cruds.appointment_crud import CRUDAppointment
from backend.core.cruds.prescription_crud import CRUDPrescription
from backend.core.models.Appointment import AppointmentStatus

logging = logger(__name__)


class PrescriptionController(BaseController):
    """Controller for doctor-created prescription records."""

    def __init__(self):
        """Initialize CRUD dependencies used by prescription workflows."""

        self.crud_prescription = CRUDPrescription()
        self.crud_appointment = CRUDAppointment()

    async def create_prescription(self, doctor_id: str, prescription_data: dict) -> dict:
        """Create a prescription for a completed appointment.

        Args:
            doctor_id: Doctor creating the prescription.
            prescription_data: Prescription payload from the request schema.

        Returns:
            dict: Serialized created prescription payload.

        Raises:
            HTTPException 400: Appointment is not eligible for prescription creation.
            HTTPException 404: Appointment does not exist.
            HTTPException 409: Prescription already exists for the appointment.
        """

        try:
            logging.info("Executing PrescriptionController.create_prescription")
            appointment = await self.crud_appointment.get_by_id(
                id=prescription_data["appointment_id"]
            )
            if appointment is None:
                logging.warning(
                    f"Prescription creation blocked for missing appointment {prescription_data['appointment_id']}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Appointment not found",
                )
            if appointment.doctor_id != doctor_id:
                logging.warning(
                    f"Doctor {doctor_id} cannot create prescription for appointment {appointment.id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this appointment",
                )
            if appointment.status != AppointmentStatus.COMPLETED:
                logging.warning(f"Prescription blocked because appointment {appointment.id} is not completed")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Prescription can be created only for completed appointments",
                )

            existing_prescription = await self.crud_prescription.get_by_appointment_id(
                appointment_id=prescription_data["appointment_id"]
            )
            if existing_prescription:
                logging.warning(
                    f"Prescription already exists for appointment {prescription_data['appointment_id']}"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Prescription already exists for this appointment",
                )

            prescription = await self.crud_prescription.create(
                obj_in={
                    "appointment_id": prescription_data["appointment_id"],
                    "doctor_id": doctor_id,
                    "patient_id": appointment.patient_id,
                    "medicines": prescription_data.get("medicines", []),
                    "notes": prescription_data.get("notes"),
                }
            )
            return self._serialize_document(prescription)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in PrescriptionController.create_prescription: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def update_prescription(
        self,
        prescription_id: str,
        doctor_id: str,
        update_data: dict,
    ) -> dict:
        """Update an existing prescription owned by the doctor.

        Args:
            prescription_id: Prescription record identifier.
            doctor_id: Doctor updating the prescription.
            update_data: Partial update payload for the prescription.

        Returns:
            dict: Serialized updated prescription payload.

        Raises:
            HTTPException 403: Prescription is not owned by the doctor.
            HTTPException 404: Prescription record does not exist.
        """

        try:
            logging.info("Executing PrescriptionController.update_prescription")
            prescription = await self.crud_prescription.get_by_id(id=prescription_id)
            if prescription is None:
                logging.warning(f"Prescription not found: {prescription_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Prescription not found",
                )
            if prescription.doctor_id != doctor_id:
                logging.warning(f"Doctor {doctor_id} cannot update prescription {prescription_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this prescription",
                )

            updated_prescription = await self.crud_prescription.update(
                id=prescription_id,
                obj_in=update_data,
            )
            return self._serialize_document(updated_prescription)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in PrescriptionController.update_prescription: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def get_prescription_by_appointment(self, appointment_id: str) -> dict:
        """Fetch a prescription linked to a completed appointment.

        Args:
            appointment_id: Appointment identifier linked to the prescription.

        Returns:
            dict: Serialized prescription payload.

        Raises:
            HTTPException 404: Prescription record does not exist.
        """

        try:
            logging.info("Executing PrescriptionController.get_prescription_by_appointment")
            prescription = await self.crud_prescription.get_by_appointment_id(
                appointment_id=appointment_id
            )
            if prescription is None:
                logging.warning(f"Prescription not found for appointment {appointment_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Prescription not found",
                )

            return self._serialize_document(prescription)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in PrescriptionController.get_prescription_by_appointment: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_prescriptions_for_patient(self, patient_id: str) -> dict:
        """List prescriptions visible to a patient.

        Args:
            patient_id: Patient identifier used for lookup.

        Returns:
            dict: Serialized prescription list payload.
        """

        try:
            logging.info("Executing PrescriptionController.list_prescriptions_for_patient")
            prescriptions = await self.crud_prescription.get_by_patient_id(patient_id=patient_id)
            return {"items": self._serialize_documents(prescriptions)}
        except Exception as error:
            logging.error(f"Error in PrescriptionController.list_prescriptions_for_patient: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_prescriptions_for_doctor(self, doctor_id: str) -> dict:
        """List prescriptions created by a doctor.

        Args:
            doctor_id: Doctor identifier used for lookup.

        Returns:
            dict: Serialized prescription list payload.
        """

        try:
            logging.info("Executing PrescriptionController.list_prescriptions_for_doctor")
            prescriptions = await self.crud_prescription.get_by_doctor_id(doctor_id=doctor_id)
            return {"items": self._serialize_documents(prescriptions)}
        except Exception as error:
            logging.error(f"Error in PrescriptionController.list_prescriptions_for_doctor: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )
