"""Prescription controller logic for consultation follow-up workflows."""

from __future__ import annotations

from fastapi import HTTPException, status

from backend.commons.logger import logger
from backend.core.controllers.base_controller import BaseController
from backend.core.cruds.appointment_crud import CRUDAppointment
from backend.core.cruds.prescription_crud import CRUDPrescription
from backend.core.cruds.user_crud import CRUDUser
from backend.core.models.Appointment import AppointmentStatus
from backend.core.models.user_model import UserRole

logging = logger(__name__)


class PrescriptionController(BaseController):
    """Controller for doctor-created prescription records."""

    def __init__(self):
        """Initialize CRUD dependencies used by prescription workflows."""

        self.crud_prescription = CRUDPrescription()
        self.crud_appointment = CRUDAppointment()
        self.crud_user = CRUDUser()

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
                    "patient_name": appointment.patient_name,
                    "patient_phone": appointment.patient_phone,
                    "patient_age": appointment.patient_age,
                    "patient_gender": appointment.patient_gender,
                    "patient_blood_group": appointment.patient_blood_group,
                    "visit_reason": appointment.reason,
                    "medicines": prescription_data.get("medicines", []),
                    "notes": prescription_data.get("notes"),
                }
            )
            return await self._serialize_prescription(prescription=prescription)
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
            return await self._serialize_prescription(prescription=updated_prescription)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in PrescriptionController.update_prescription: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def get_prescription_by_appointment(
        self,
        appointment_id: str,
        actor_id: str,
        actor_role: UserRole,
    ) -> dict:
        """Fetch a prescription linked to a completed appointment.

        Args:
            appointment_id: Appointment identifier linked to the prescription.
            actor_id: Authenticated user requesting the prescription.
            actor_role: Role of the authenticated user.

        Returns:
            dict: Serialized prescription payload.

        Raises:
            HTTPException 403: Authenticated user is not related to the appointment.
            HTTPException 404: Prescription record does not exist.
        """

        try:
            logging.info("Executing PrescriptionController.get_prescription_by_appointment")
            appointment = await self.crud_appointment.get_by_id(id=appointment_id)
            if appointment is None:
                logging.warning(f"Prescription lookup blocked for missing appointment {appointment_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Appointment not found",
                )
            if actor_role == UserRole.PATIENT and appointment.patient_id != actor_id:
                logging.warning(
                    f"Patient {actor_id} cannot view prescription for appointment {appointment_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this prescription",
                )
            if actor_role == UserRole.DOCTOR and appointment.doctor_id != actor_id:
                logging.warning(
                    f"Doctor {actor_id} cannot view prescription for appointment {appointment_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this prescription",
                )
            if actor_role not in {UserRole.PATIENT, UserRole.DOCTOR}:
                logging.warning(
                    f"Unsupported role attempted prescription lookup: {actor_role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This role cannot access prescriptions",
                )

            prescription = await self.crud_prescription.get_by_appointment_id(
                appointment_id=appointment_id
            )
            if prescription is None:
                logging.warning(f"Prescription not found for appointment {appointment_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Prescription not found",
                )

            return await self._serialize_prescription(prescription=prescription)
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
            items = []
            for prescription in prescriptions:
                items.append(await self._serialize_prescription(prescription=prescription))
            return {"items": items}
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
            items = []
            for prescription in prescriptions:
                items.append(await self._serialize_prescription(prescription=prescription))
            return {"items": items}
        except Exception as error:
            logging.error(f"Error in PrescriptionController.list_prescriptions_for_doctor: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def _serialize_prescription(self, *, prescription) -> dict:
        """Serialize a prescription with patient fallback values for legacy data.

        Args:
            prescription: Prescription record being serialized.

        Returns:
            dict: Serialized prescription payload enriched for UI rendering.
        """

        payload = self._serialize_document(prescription)
        if payload.get("patient_name") and payload.get("patient_phone") and payload.get("doctor_name"):
            return payload

        patient = await self.crud_user.get_by_id(id=prescription.patient_id)
        doctor = await self.crud_user.get_by_id(id=prescription.doctor_id)
        if patient is not None:
            payload["patient_name"] = payload.get("patient_name") or patient.name
            payload["patient_phone"] = payload.get("patient_phone") or patient.phone
        if doctor is not None:
            payload["doctor_name"] = payload.get("doctor_name") or doctor.name
        return payload
