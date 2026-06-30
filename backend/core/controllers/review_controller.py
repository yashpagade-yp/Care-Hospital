"""Review controller logic for the MedCare backend."""

from __future__ import annotations

from fastapi import HTTPException, status

from backend.commons.logger import logger
from backend.core.controllers.base_controller import BaseController
from backend.core.cruds.appointment_crud import CRUDAppointment
from backend.core.cruds.review_crud import CRUDReview
from backend.core.cruds.user_crud import CRUDUser
from backend.core.models.Appointment import AppointmentStatus
from backend.core.models.user_model import UserRole

logging = logger(__name__)


class ReviewController(BaseController):
    """Controller for review creation and moderation workflows."""

    def __init__(self):
        """Initialize CRUD dependencies used by review workflows."""

        self.crud_review = CRUDReview()
        self.crud_appointment = CRUDAppointment()
        self.crud_user = CRUDUser()

    async def create_review(self, patient_id: str, review_data: dict) -> dict:
        """Create a patient review for a completed appointment.

        Args:
            patient_id: Patient submitting the review.
            review_data: Review payload from the request schema.

        Returns:
            dict: Serialized created review payload.

        Raises:
            HTTPException 400: Appointment is not eligible for review creation.
            HTTPException 404: Appointment does not exist.
            HTTPException 409: Review already exists for the appointment.
        """

        try:
            logging.info("Executing ReviewController.create_review")
            appointment = await self.crud_appointment.get_by_id(id=review_data["appointment_id"])
            if appointment is None:
                logging.warning(f"Review creation blocked for missing appointment {review_data['appointment_id']}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Appointment not found",
                )
            if appointment.patient_id != patient_id:
                logging.warning(f"Patient {patient_id} cannot review appointment {appointment.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this appointment",
                )
            if appointment.status != AppointmentStatus.COMPLETED:
                logging.warning(f"Review blocked because appointment {appointment.id} is not completed")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Review can be submitted only for completed appointments",
                )

            existing_review = await self.crud_review.get_by_appointment_id(
                appointment_id=review_data["appointment_id"]
            )
            if existing_review:
                logging.warning(f"Review already exists for appointment {appointment.id}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Review already exists for this appointment",
                )

            review = await self.crud_review.create(
                obj_in={
                    "appointment_id": review_data["appointment_id"],
                    "patient_id": patient_id,
                    "doctor_id": appointment.doctor_id,
                    "rating": review_data["rating"],
                    "comment": review_data.get("comment"),
                    "is_hidden": False,
                }
            )
            return self._serialize_document(review)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ReviewController.create_review: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def set_review_visibility(
        self,
        review_id: str,
        is_hidden: bool,
        admin_user_id: str,
    ) -> dict:
        """Hide or unhide a review during admin moderation.

        Args:
            review_id: Review record identifier.
            is_hidden: Visibility state requested by moderation.
            admin_user_id: Admin user applying the moderation decision.

        Returns:
            dict: Serialized updated review payload.

        Raises:
            HTTPException 403: Acting user is not an admin.
            HTTPException 404: Review record does not exist.
        """

        try:
            logging.info("Executing ReviewController.set_review_visibility")
            await self._assert_admin(admin_user_id=admin_user_id)
            review = await self.crud_review.get_by_id(id=review_id)
            if review is None:
                logging.warning(f"Review not found for moderation: {review_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Review not found",
                )

            updated_review = await self.crud_review.update(
                id=review_id,
                obj_in={"is_hidden": is_hidden},
            )
            return self._serialize_document(updated_review)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ReviewController.set_review_visibility: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def _assert_admin(self, *, admin_user_id: str) -> None:
        """Ensure the acting user exists and has the admin role.

        Args:
            admin_user_id: User identifier expected to belong to an admin.

        Raises:
            HTTPException 403: Acting user is not an admin.
        """

        admin = await self.crud_user.get_by_id(id=admin_user_id)
        if admin is None or admin.role != UserRole.ADMIN:
            logging.warning(f"Review moderation admin check failed for user {admin_user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can moderate reviews",
            )

    async def list_doctor_reviews(self, doctor_id: str, include_hidden: bool = False) -> dict:
        """List reviews submitted for a doctor.

        Args:
            doctor_id: Doctor identifier used for lookup.
            include_hidden: Whether moderated reviews should be included.

        Returns:
            dict: Serialized review list payload.
        """

        try:
            logging.info("Executing ReviewController.list_doctor_reviews")
            reviews = await self.crud_review.get_by_doctor_id(
                doctor_id=doctor_id,
                include_hidden=include_hidden,
            )
            return {"items": self._serialize_documents(reviews)}
        except Exception as error:
            logging.error(f"Error in ReviewController.list_doctor_reviews: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )
