"""Dashboard aggregation controller logic for the MedCare backend."""

from __future__ import annotations

from fastapi import HTTPException, status
from odmantic.query import desc

from backend.commons.logger import logger
from backend.core.controllers.base_controller import BaseController
from backend.core.cruds.appointment_crud import CRUDAppointment
from backend.core.cruds.invitation_crud import CRUDDoctorInvitation
from backend.core.cruds.review_crud import CRUDReview
from backend.core.cruds.user_crud import CRUDUser
from backend.core.models.Appointment import Appointment, AppointmentStatus
from backend.core.models.Invitation import DoctorInvitation
from backend.core.models.Review import Review
from backend.core.models.user_model import UserRole

logging = logger(__name__)


class DashboardController(BaseController):
    """Controller for patient, doctor, and admin dashboard aggregation."""

    def __init__(self):
        """Initialize CRUD dependencies used by dashboard workflows."""

        self.crud_user = CRUDUser()
        self.crud_appointment = CRUDAppointment()
        self.crud_invitation = CRUDDoctorInvitation()
        self.crud_review = CRUDReview()

    async def get_patient_dashboard(self, patient_id: str) -> dict:
        """Build the patient dashboard payload.

        Args:
            patient_id: Patient identifier whose dashboard is being requested.

        Returns:
            dict: Patient dashboard response payload.
        """

        try:
            logging.info("Executing DashboardController.get_patient_dashboard")
            patient = await self.crud_user.get_by_id(id=patient_id)
            if patient is None or patient.role != UserRole.PATIENT:
                logging.warning(f"Patient dashboard lookup failed for user {patient_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Patient not found",
                )

            doctors = await self.crud_user.get_doctors()
            appointments = await self.crud_appointment.get_by_patient_id(patient_id=patient_id)
            now = self._utc_now()
            review_map = await self._build_doctor_rating_map()

            return {
                "profile": self._serialize_document(patient),
                "doctor_cards": [
                    {
                        "doctor_id": str(doctor.id),
                        "name": doctor.name,
                        "specialty": doctor.specialty,
                        "experience_years": doctor.experience_years,
                        "rating": review_map.get(str(doctor.id)),
                    }
                    for doctor in doctors
                ],
                "upcoming_appointments": self._serialize_documents(
                    [
                        appointment
                        for appointment in appointments
                        if self._normalize_datetime(appointment.date_time) >= now
                        and appointment.status == AppointmentStatus.CONFIRMED
                    ]
                ),
                "appointment_history": self._serialize_documents(
                    [
                        appointment
                        for appointment in appointments
                        if self._normalize_datetime(appointment.date_time) < now
                        or appointment.status != AppointmentStatus.CONFIRMED
                    ]
                ),
            }
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in DashboardController.get_patient_dashboard: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def get_doctor_dashboard(self, doctor_id: str) -> dict:
        """Build the doctor dashboard payload.

        Args:
            doctor_id: Doctor identifier whose dashboard is being requested.

        Returns:
            dict: Doctor dashboard response payload.
        """

        try:
            logging.info("Executing DashboardController.get_doctor_dashboard")
            doctor = await self.crud_user.get_by_id(id=doctor_id)
            if doctor is None or doctor.role != UserRole.DOCTOR:
                logging.warning(f"Doctor dashboard lookup failed for user {doctor_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Doctor not found",
                )

            appointments = await self.crud_appointment.get_by_doctor_id(doctor_id=doctor_id)
            now = self._utc_now()
            patient_lookup = await self._build_user_lookup(
                user_ids=[
                    appointment.patient_id
                    for appointment in appointments
                    if appointment.patient_name is None or appointment.patient_phone is None
                ]
            )
            return {
                "profile": self._serialize_document(doctor),
                "upcoming_appointments": [
                    self._serialize_appointment_for_doctor(
                        appointment=appointment,
                        patient_lookup=patient_lookup,
                    )
                    for appointment in appointments
                    if self._normalize_datetime(appointment.date_time) >= now
                    and appointment.status == AppointmentStatus.CONFIRMED
                ],
                "appointment_history": [
                    self._serialize_appointment_for_doctor(
                        appointment=appointment,
                        patient_lookup=patient_lookup,
                    )
                    for appointment in appointments
                    if self._normalize_datetime(appointment.date_time) < now
                    or appointment.status != AppointmentStatus.CONFIRMED
                ],
            }
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in DashboardController.get_doctor_dashboard: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def get_admin_dashboard(self, admin_user_id: str) -> dict:
        """Build the admin dashboard payload.

        Args:
            admin_user_id: Admin identifier whose dashboard is being requested.

        Returns:
            dict: Admin dashboard response payload.
        """

        try:
            logging.info("Executing DashboardController.get_admin_dashboard")
            admin = await self.crud_user.get_by_id(id=admin_user_id)
            if admin is None or admin.role != UserRole.ADMIN:
                logging.warning(f"Admin dashboard lookup failed for user {admin_user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin not found",
                )

            recent_invitations = await self.crud_invitation.get_many(
                sort=desc(DoctorInvitation.created_at),
                limit=5,
            )
            recent_appointments = await self.crud_appointment.get_many(
                sort=desc(Appointment.created_at),
                limit=5,
            )
            flagged_reviews = await self.crud_review.get_many(
                Review.is_hidden == True,
                sort=desc(Review.created_at),
                limit=5,
            )

            return {
                "profile": self._serialize_document(admin),
                "doctor_count": await self.crud_user.count(self.crud_user.model.role == UserRole.DOCTOR),
                "patient_count": await self.crud_user.count(self.crud_user.model.role == UserRole.PATIENT),
                "invitation_count": await self.crud_invitation.count(),
                "appointment_count": await self.crud_appointment.count(),
                "recent_invitations": self._serialize_documents(recent_invitations),
                "recent_appointments": self._serialize_documents(recent_appointments),
                "flagged_reviews": self._serialize_documents(flagged_reviews),
            }
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in DashboardController.get_admin_dashboard: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def _build_doctor_rating_map(self) -> dict[str, float]:
        """Compute average visible ratings for each doctor.

        Returns:
            dict[str, float]: Mapping of doctor id to average rating.
        """

        reviews = await self.crud_review.get_many(
            Review.is_hidden == False,
            sort=desc(Review.created_at),
        )
        doctor_review_map: dict[str, list[int]] = {}
        for review in reviews:
            doctor_review_map.setdefault(review.doctor_id, []).append(review.rating)
        return {
            doctor_id: round(sum(ratings) / len(ratings), 1)
            for doctor_id, ratings in doctor_review_map.items()
        }

    async def _build_user_lookup(self, *, user_ids: list[str]) -> dict[str, object]:
        """Build a lookup for patient fallback values in doctor dashboard cards.

        Args:
            user_ids: Patient identifiers referenced by doctor appointments.

        Returns:
            dict[str, object]: Mapping of user id to user record.
        """

        lookup: dict[str, object] = {}
        for user_id in set(user_ids):
            user = await self.crud_user.get_by_id(id=user_id)
            if user is not None:
                lookup[user_id] = user
        return lookup

    def _serialize_appointment_for_doctor(self, *, appointment, patient_lookup: dict[str, object]) -> dict:
        """Serialize doctor appointments with patient display context.

        Args:
            appointment: Appointment record being serialized.
            patient_lookup: Mapping of patient id to patient record.

        Returns:
            dict: Serialized appointment payload for doctor workspace views.
        """

        payload = self._serialize_document(appointment)
        patient = patient_lookup.get(appointment.patient_id)
        if not payload.get("patient_name") and patient is not None:
            payload["patient_name"] = patient.name
        if not payload.get("patient_phone") and patient is not None:
            payload["patient_phone"] = patient.phone
        return payload
