"""Doctor availability controller logic for the MedCare backend."""

from __future__ import annotations

from datetime import datetime, time, timezone

from fastapi import HTTPException, status

from backend.commons.logger import logger
from backend.core.controllers.base_controller import BaseController
from backend.core.cruds.appointment_crud import CRUDAppointment
from backend.core.cruds.availability_crud import CRUDDoctorAvailability
from backend.core.cruds.user_crud import CRUDUser
from backend.core.models.Appointment import AppointmentStatus
from backend.core.models.user_model import UserRole

logging = logger(__name__)


class AvailabilityController(BaseController):
    """Controller for doctor-managed and admin-managed availability changes."""

    def __init__(self):
        """Initialize CRUD dependencies used by availability workflows."""

        self.crud_appointment = CRUDAppointment()
        self.crud_availability = CRUDDoctorAvailability()
        self.crud_user = CRUDUser()

    async def create_doctor_availability(self, doctor_id: str, availability_data: dict) -> dict:
        """Create a doctor availability entry after basic domain validation.

        Args:
            doctor_id: Doctor creating or owning the availability entry.
            availability_data: Availability payload from the request schema.

        Returns:
            dict: Serialized created availability payload.

        Raises:
            HTTPException 400: Time range is invalid or duplicate slot exists.
            HTTPException 404: Doctor record does not exist.
        """

        try:
            logging.info("Executing AvailabilityController.create_doctor_availability")
            await self._assert_doctor(doctor_id=doctor_id)
            self._validate_time_range(
                start_time=availability_data["start_time"],
                end_time=availability_data["end_time"],
            )
            await self._ensure_unique_slot(
                doctor_id=doctor_id,
                availability_data=availability_data,
            )
            # Convert time/date objects to strings for MongoDB storage
            sanitized = dict(availability_data)
            sanitized["start_time"] = self._time_to_str(sanitized["start_time"])
            sanitized["end_time"] = self._time_to_str(sanitized["end_time"])
            if sanitized.get("exception_date") is not None:
                sanitized["exception_date"] = self._date_to_str(sanitized["exception_date"])
            availability = await self.crud_availability.create(
                obj_in={"doctor_id": doctor_id, **sanitized}
            )
            return self._serialize_document(availability)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AvailabilityController.create_doctor_availability: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def update_doctor_availability(
        self,
        availability_id: str,
        doctor_id: str,
        update_data: dict,
    ) -> dict:
        """Update an existing doctor availability entry owned by the caller.

        Args:
            availability_id: Availability record identifier.
            doctor_id: Doctor attempting the update.
            update_data: Partial update payload for the availability entry.

        Returns:
            dict: Serialized updated availability payload.

        Raises:
            HTTPException 403: Availability entry is not owned by the doctor.
            HTTPException 404: Availability record does not exist.
            HTTPException 400: Updated time range is invalid.
        """

        try:
            logging.info("Executing AvailabilityController.update_doctor_availability")
            availability = await self.crud_availability.get_by_id(id=availability_id)
            if availability is None:
                logging.warning(f"Availability not found: {availability_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Availability not found",
                )
            if availability.doctor_id != doctor_id:
                logging.warning(f"Doctor {doctor_id} cannot update availability {availability_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this availability entry",
                )

            start_time = update_data.get("start_time", availability.start_time)
            end_time = update_data.get("end_time", availability.end_time)
            self._validate_time_range(start_time=start_time, end_time=end_time)
            await self._ensure_no_booked_appointments_for_availability(availability=availability)
            merged_data = {
                "availability_type": availability.availability_type,
                "day_of_week": update_data.get("day_of_week", availability.day_of_week),
                "start_time": self._time_to_str(start_time),
                "end_time": self._time_to_str(end_time),
                "exception_date": self._date_to_str(
                    update_data.get("exception_date", availability.exception_date)
                ) if update_data.get("exception_date", availability.exception_date) is not None else None,
            }
            await self._ensure_unique_slot(
                doctor_id=doctor_id,
                availability_data=merged_data,
                exclude_id=availability_id,
            )
            sanitized_update = dict(update_data)
            if "start_time" in sanitized_update:
                sanitized_update["start_time"] = self._time_to_str(sanitized_update["start_time"])
            if "end_time" in sanitized_update:
                sanitized_update["end_time"] = self._time_to_str(sanitized_update["end_time"])
            if "exception_date" in sanitized_update and sanitized_update["exception_date"] is not None:
                sanitized_update["exception_date"] = self._date_to_str(sanitized_update["exception_date"])
            updated_availability = await self.crud_availability.update(
                id=availability_id,
                obj_in=sanitized_update,
            )
            return self._serialize_document(updated_availability)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AvailabilityController.update_doctor_availability: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_doctor_availability(self, doctor_id: str) -> dict:
        """List availability entries belonging to a specific doctor."""

        try:
            logging.info("Executing AvailabilityController.list_doctor_availability")
            await self._assert_doctor(doctor_id=doctor_id)
            availability_items = await self.crud_availability.get_by_doctor_id(doctor_id=doctor_id)
            return {"items": self._serialize_documents(availability_items)}
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AvailabilityController.list_doctor_availability: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def delete_doctor_availability(self, availability_id: str, doctor_id: str) -> bool:
        """Delete a doctor availability entry owned by the caller.

        Args:
            availability_id: Availability record identifier to delete.
            doctor_id: Doctor attempting the deletion.

        Returns:
            bool: True if deleted, False if not found.

        Raises:
            HTTPException 403: Availability entry is not owned by the doctor.
        """

        try:
            logging.info("Executing AvailabilityController.delete_doctor_availability")
            availability = await self.crud_availability.get_by_id(id=availability_id)
            if availability is None:
                return False
            if availability.doctor_id != doctor_id:
                logging.warning(f"Doctor {doctor_id} cannot delete availability {availability_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this availability entry",
                )
            return await self.crud_availability.delete(id=availability_id)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AvailabilityController.delete_doctor_availability: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def create_admin_override(self, override_data: dict, admin_user_id: str) -> dict:
        """Create an emergency admin override availability entry for a doctor.

        Args:
            override_data: Admin override payload from the request schema.
            admin_user_id: Admin creating the override.

        Returns:
            dict: Serialized created availability payload.

        Raises:
            HTTPException 403: Acting user is not an admin.
            HTTPException 404: Doctor record does not exist.
        """

        try:
            logging.info("Executing AvailabilityController.create_admin_override")
            await self._assert_admin(admin_user_id=admin_user_id)
            await self._assert_doctor(doctor_id=override_data["doctor_id"])
            self._validate_time_range(
                start_time=override_data["start_time"],
                end_time=override_data["end_time"],
            )
            await self._ensure_unique_slot(
                doctor_id=override_data["doctor_id"],
                availability_data=override_data,
            )

            if override_data.get("reason"):
                logging.info(
                    f"Applying admin availability override for doctor {override_data['doctor_id']}: {override_data['reason']}"
                )

            availability = await self.crud_availability.create(
                obj_in={
                    "doctor_id": override_data["doctor_id"],
                    "availability_type": override_data["availability_type"],
                    "start_time": self._time_to_str(override_data["start_time"]),
                    "end_time": self._time_to_str(override_data["end_time"]),
                    "exception_date": self._date_to_str(override_data["exception_date"]),
                    "day_of_week": None,
                }
            )
            return self._serialize_document(availability)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AvailabilityController.create_admin_override: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    @staticmethod
    def _validate_time_range(*, start_time, end_time) -> None:
        """Validate that the provided availability window is non-empty."""
        # Accept both time objects and HH:MM strings
        st = start_time if isinstance(start_time, str) else start_time.isoformat()[:5]
        et = end_time if isinstance(end_time, str) else end_time.isoformat()[:5]
        if st >= et:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_time must be earlier than end_time",
            )

    @staticmethod
    def _time_to_str(t) -> str:
        """Convert a datetime.time or HH:MM string to a HH:MM string."""
        if isinstance(t, str):
            return t[:5]  # already a string — just normalise to HH:MM
        return t.strftime("%H:%M")

    @staticmethod
    def _date_to_str(d) -> str | None:
        """Convert a datetime.date or ISO string to a YYYY-MM-DD string."""
        if d is None:
            return None
        if isinstance(d, str):
            return d[:10]
        return d.isoformat()

    async def _ensure_unique_slot(
        self,
        *,
        doctor_id: str,
        availability_data: dict,
        exclude_id: str | None = None,
    ) -> None:
        """Prevent duplicate availability entries for the same doctor window.

        Args:
            doctor_id: Doctor owning the entry.
            availability_data: Availability payload being created.
            exclude_id: Existing availability identifier excluded from matching.

        Raises:
            HTTPException 409: Matching availability entry already exists.
        """

        if availability_data.get("day_of_week") is not None:
            existing_items = await self.crud_availability.get_recurring_slots(
                doctor_id=doctor_id,
                day_of_week=availability_data["day_of_week"],
            )
        else:
            existing_items = await self.crud_availability.get_exception_slots(
                doctor_id=doctor_id,
                exception_date=availability_data["exception_date"],
            )

        has_duplicate = any(
            str(existing_item.id) != exclude_id
            and
            existing_item.availability_type == availability_data["availability_type"]
            and existing_item.start_time == availability_data["start_time"]
            and existing_item.end_time == availability_data["end_time"]
            for existing_item in existing_items
        )
        if has_duplicate:
            logging.warning(f"Duplicate availability blocked for doctor {doctor_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Availability entry already exists for this window",
            )

    async def _ensure_no_booked_appointments_for_availability(self, *, availability) -> None:
        """Block availability edits when future booked appointments depend on the slot.

        Args:
            availability: Existing availability record being edited.

        Raises:
            HTTPException 400: A future booked appointment still depends on the slot.
        """

        appointments = await self.crud_appointment.get_by_doctor_id(
            doctor_id=availability.doctor_id
        )
        relevant_statuses = {
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.NO_SHOW,
            AppointmentStatus.COMPLETED,
        }
        now = datetime.now(timezone.utc)
        for appointment in appointments:
            appointment_datetime = self._normalize_datetime(appointment.date_time)
            if appointment.status not in relevant_statuses or appointment_datetime < now:
                continue
            if self._appointment_matches_availability(
                appointment_datetime=appointment_datetime,
                availability=availability,
            ):
                logging.warning(
                    f"Availability {availability.id} cannot be updated because appointment {appointment.id} depends on it"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cancel or reschedule booked appointments before editing this availability slot",
                )

    @staticmethod
    def _appointment_matches_availability(*, appointment_datetime: datetime, availability) -> bool:
        """Check whether an appointment falls inside an availability slot.

        Args:
            appointment_datetime: Appointment time being checked.
            availability: Existing availability record.

        Returns:
            bool: True when the appointment depends on the availability slot.
        """

        appointment_time_str = appointment_datetime.strftime("%H:%M")
        # start_time / end_time are stored as HH:MM strings
        st = availability.start_time[:5] if isinstance(availability.start_time, str) else availability.start_time.strftime("%H:%M")
        et = availability.end_time[:5] if isinstance(availability.end_time, str) else availability.end_time.strftime("%H:%M")
        time_matches = st <= appointment_time_str < et
        if not time_matches:
            return False
        if availability.exception_date is not None:
            # exception_date stored as YYYY-MM-DD string
            ed = availability.exception_date[:10] if isinstance(availability.exception_date, str) else availability.exception_date.isoformat()
            return appointment_datetime.date().isoformat() == ed
        if availability.day_of_week is not None:
            return appointment_datetime.strftime("%A").upper() == availability.day_of_week.value
        return False

    async def _assert_doctor(self, *, doctor_id: str) -> None:
        """Ensure the target user exists and is a doctor.

        Args:
            doctor_id: User identifier expected to belong to a doctor.

        Raises:
            HTTPException 404: Doctor record does not exist.
        """

        doctor = await self.crud_user.get_by_id(id=doctor_id)
        if doctor is None or doctor.role != UserRole.DOCTOR:
            logging.warning(f"Doctor lookup failed for availability workflow: {doctor_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found",
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
            logging.warning(f"Availability admin check failed for user {admin_user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create availability overrides",
            )
