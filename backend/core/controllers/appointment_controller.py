"""Appointment controller logic for booking and lifecycle workflows."""

from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status

from backend.commons.logger import logger
from backend.core.controllers.base_controller import BaseController
from backend.core.cruds.appointment_crud import CRUDAppointment
from backend.core.cruds.availability_crud import CRUDDoctorAvailability
from backend.core.cruds.payment_crud import CRUDPayment
from backend.core.cruds.slot_hold_crud import CRUDSlotHold
from backend.core.cruds.user_crud import CRUDUser
from backend.core.models.Appointment import AppointmentStatus, CancelledBy, PaymentStatus
from backend.core.models.DoctorAvailability import AvailabilityType, DayOfWeek
from backend.core.models.Payment import PaymentRecordStatus
from backend.core.models.user_model import DoctorStatus, UserRole

logging = logger(__name__)


class AppointmentController(BaseController):
    """Controller for slot holds, booking, cancellation, and status updates."""

    def __init__(self):
        """Initialize CRUD dependencies used by appointment workflows."""

        self.crud_appointment = CRUDAppointment()
        self.crud_availability = CRUDDoctorAvailability()
        self.crud_slot_hold = CRUDSlotHold()
        self.crud_payment = CRUDPayment()
        self.crud_user = CRUDUser()

    async def create_slot_hold(self, patient_id: str, slot_hold_data: dict) -> dict:
        """Create a temporary slot hold for a patient-selected doctor slot.

        Args:
            patient_id: Patient creating the temporary hold.
            slot_hold_data: Slot-hold payload from the request schema.

        Returns:
            dict: Serialized slot-hold payload.

        Raises:
            HTTPException 400: Doctor slot is already held or booked.
            HTTPException 404: Patient or doctor record does not exist.
        """

        try:
            logging.info("Executing AppointmentController.create_slot_hold")
            await self._assert_patient(patient_id=patient_id)
            await self._assert_active_doctor(doctor_id=slot_hold_data["doctor_id"])
            await self.crud_slot_hold.delete_expired_holds()

            date_time = self._normalize_datetime(slot_hold_data["date_time"])
            # Preserve original offset-aware datetime for local-time slot comparison
            original_date_time = slot_hold_data["date_time"]
            self._ensure_future_datetime(date_time=date_time)
            await self._ensure_slot_available(
                doctor_id=slot_hold_data["doctor_id"],
                date_time=date_time,
                local_date_time=original_date_time,
            )
            active_hold = await self.crud_slot_hold.get_active_hold(
                doctor_id=slot_hold_data["doctor_id"],
                date_time=date_time,
            )
            if active_hold:
                logging.warning(f"Slot hold blocked because slot is already held for doctor {slot_hold_data['doctor_id']}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Selected slot is currently held by another booking attempt",
                )

            existing_appointment = await self.crud_appointment.get_by_doctor_and_datetime(
                doctor_id=slot_hold_data["doctor_id"],
                date_time=date_time,
            )
            if existing_appointment:
                logging.warning(f"Slot hold blocked because appointment already exists for doctor {slot_hold_data['doctor_id']}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Selected slot has already been booked",
                )

            slot_hold = await self.crud_slot_hold.create(
                obj_in={
                    "patient_id": patient_id,
                    "doctor_id": slot_hold_data["doctor_id"],
                    "date_time": date_time,
                    "expires_at": self._utc_now() + timedelta(minutes=10),
                }
            )
            return self._serialize_document(slot_hold)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AppointmentController.create_slot_hold: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def confirm_appointment(self, patient_id: str, confirmation_data: dict) -> dict:
        """Confirm an appointment from an active slot hold and mock payment.

        Args:
            patient_id: Patient confirming the booking.
            confirmation_data: Booking confirmation payload from the request schema.

        Returns:
            dict: Appointment and payment payloads for the confirmed booking.

        Raises:
            HTTPException 400: Slot hold is invalid or expired.
            HTTPException 409: Slot has already been booked.
        """

        try:
            logging.info("Executing AppointmentController.confirm_appointment")
            await self._assert_patient(patient_id=patient_id)
            slot_hold = await self.crud_slot_hold.get_by_id(id=confirmation_data["slot_hold_id"])
            if slot_hold is None:
                logging.warning(f"Slot hold not found: {confirmation_data['slot_hold_id']}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Slot hold not found",
                )
            if slot_hold.patient_id != patient_id:
                logging.warning(f"Patient {patient_id} cannot confirm slot hold {slot_hold.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this slot hold",
                )
            if self._normalize_datetime(slot_hold.expires_at) <= self._utc_now():
                logging.warning(f"Slot hold expired before confirmation: {slot_hold.id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Slot hold has expired",
                )
            # NOTE: slot availability was already validated and the slot locked during
            # create_slot_hold. Re-validating here with the UTC-stored datetime causes
            # an IST/UTC mismatch (e.g. 09:00 IST stored as 03:30 UTC fails the check).
            # The active, unexpired slot hold is the authoritative proof of availability.

            existing_appointment = await self.crud_appointment.get_by_doctor_and_datetime(
                doctor_id=slot_hold.doctor_id,
                date_time=self._normalize_datetime(slot_hold.date_time),
            )
            if existing_appointment:
                logging.warning(f"Booking blocked because slot already booked for hold {slot_hold.id}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Selected slot has already been booked",
                )

            patient = await self.crud_user.get_by_id(id=patient_id)
            await self.crud_user.update(
                id=patient_id,
                obj_in={
                    "name": confirmation_data["patient_name"],
                    "phone": confirmation_data["patient_phone"],
                },
            )

            appointment = await self.crud_appointment.create(
                obj_in={
                    "patient_id": patient_id,
                    "doctor_id": slot_hold.doctor_id,
                    "date_time": self._normalize_datetime(slot_hold.date_time),
                    "status": AppointmentStatus.CONFIRMED,
                    "reason": confirmation_data.get("reason"),
                    "fee": confirmation_data["fee"],
                    "payment_status": PaymentStatus.PAID,
                }
            )
            payment = await self.crud_payment.create(
                obj_in={
                    "appointment_id": str(appointment.id),
                    "amount": confirmation_data["fee"],
                    "transaction_ref": f"MOCK-{str(appointment.id)[-8:].upper()}",
                }
            )
            await self.crud_slot_hold.delete(id=str(slot_hold.id))

            doctor = await self.crud_user.get_by_id(id=slot_hold.doctor_id)
            return {
                "appointment": self._serialize_document(appointment),
                "payment": self._serialize_document(payment),
                "patient_name": patient.name if patient else confirmation_data["patient_name"],
                "doctor_name": doctor.name if doctor else None,
            }
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AppointmentController.confirm_appointment: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def cancel_appointment(
        self,
        appointment_id: str,
        actor_id: str,
        actor_role: UserRole,
        cancel_reason: str,
    ) -> dict:
        """Cancel an appointment while enforcing role-based booking rules.

        Args:
            appointment_id: Appointment being cancelled.
            actor_id: User performing the cancellation.
            actor_role: Role of the acting user.
            cancel_reason: Human-readable cancellation reason.

        Returns:
            dict: Serialized cancelled appointment payload.

        Raises:
            HTTPException 400: Appointment cannot be cancelled in its current state.
            HTTPException 403: Acting user does not own the appointment context.
            HTTPException 404: Appointment record does not exist.
        """

        try:
            logging.info("Executing AppointmentController.cancel_appointment")
            appointment = await self._get_cancellable_appointment(appointment_id=appointment_id)
            await self._assert_actor_can_manage_appointment(
                appointment=appointment,
                actor_id=actor_id,
                actor_role=actor_role,
            )

            if actor_role == UserRole.PATIENT:
                self._enforce_patient_time_window(appointment=appointment)
            if actor_role not in {UserRole.PATIENT, UserRole.DOCTOR}:
                logging.warning(f"Unsupported actor role attempted appointment cancellation: {actor_role}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This role cannot cancel appointments",
                )

            cancelled_by = (
                CancelledBy.PATIENT if actor_role == UserRole.PATIENT else CancelledBy.DOCTOR
            )
            updated_appointment = await self.crud_appointment.update(
                id=appointment_id,
                obj_in={
                    "status": AppointmentStatus.CANCELLED,
                    "cancelled_by": cancelled_by,
                    "cancel_reason": cancel_reason,
                    "payment_status": PaymentStatus.REFUNDED,
                },
            )

            payment = await self.crud_payment.get_by_appointment_id(appointment_id=appointment_id)
            if payment:
                await self.crud_payment.update(
                    id=str(payment.id),
                    obj_in={"status": PaymentRecordStatus.REFUNDED},
                )

            return self._serialize_document(updated_appointment)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AppointmentController.cancel_appointment: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def reschedule_appointment(
        self,
        appointment_id: str,
        actor_id: str,
        actor_role: UserRole,
        reschedule_data: dict,
    ) -> dict:
        """Reschedule an existing appointment to a new free slot.

        Args:
            appointment_id: Appointment being rescheduled.
            actor_id: User requesting the reschedule.
            actor_role: Role of the acting user.
            reschedule_data: Reschedule payload containing the new slot.

        Returns:
            dict: Payload containing both original and new appointment summaries.

        Raises:
            HTTPException 400: Appointment cannot be rescheduled.
            HTTPException 403: Acting user does not own the appointment context.
            HTTPException 409: Requested slot is already booked.
        """

        try:
            logging.info("Executing AppointmentController.reschedule_appointment")
            appointment = await self._get_cancellable_appointment(appointment_id=appointment_id)
            await self._assert_actor_can_manage_appointment(
                appointment=appointment,
                actor_id=actor_id,
                actor_role=actor_role,
            )

            if actor_role == UserRole.PATIENT:
                self._enforce_patient_time_window(appointment=appointment)
            new_date_time = self._normalize_datetime(reschedule_data["new_date_time"])
            self._ensure_future_datetime(date_time=new_date_time)
            await self._ensure_slot_available(
                doctor_id=appointment.doctor_id,
                date_time=new_date_time,
            )
            existing_appointment = await self.crud_appointment.get_by_doctor_and_datetime(
                doctor_id=appointment.doctor_id,
                date_time=new_date_time,
            )
            if existing_appointment:
                logging.warning(f"Reschedule blocked because slot already booked for doctor {appointment.doctor_id}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Requested slot has already been booked",
                )

            new_appointment = await self.crud_appointment.create(
                obj_in={
                    "patient_id": appointment.patient_id,
                    "doctor_id": appointment.doctor_id,
                    "date_time": new_date_time,
                    "status": AppointmentStatus.CONFIRMED,
                    "reason": reschedule_data.get("reason") or appointment.reason,
                    "fee": appointment.fee,
                    "payment_status": appointment.payment_status,
                }
            )
            updated_original = await self.crud_appointment.update(
                id=appointment_id,
                obj_in={
                    "status": AppointmentStatus.RESCHEDULED,
                    "rescheduled_to_id": str(new_appointment.id),
                },
            )
            return {
                "previous_appointment": self._serialize_document(updated_original),
                "new_appointment": self._serialize_document(new_appointment),
            }
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AppointmentController.reschedule_appointment: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def update_appointment_status(
        self,
        appointment_id: str,
        doctor_id: str,
        new_status: AppointmentStatus,
    ) -> dict:
        """Update doctor-managed lifecycle states for a confirmed appointment.

        Args:
            appointment_id: Appointment record identifier.
            doctor_id: Doctor updating the appointment lifecycle.
            new_status: Requested appointment lifecycle state.

        Returns:
            dict: Serialized updated appointment payload.

        Raises:
            HTTPException 400: Requested transition is not allowed.
            HTTPException 403: Acting doctor does not own the appointment.
            HTTPException 404: Appointment record does not exist.
        """

        try:
            logging.info("Executing AppointmentController.update_appointment_status")
            appointment = await self.crud_appointment.get_by_id(id=appointment_id)
            if appointment is None:
                logging.warning(f"Appointment not found for status update: {appointment_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Appointment not found",
                )
            if appointment.doctor_id != doctor_id:
                logging.warning(f"Doctor {doctor_id} cannot update appointment {appointment_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this appointment",
                )
            if appointment.status != AppointmentStatus.CONFIRMED:
                logging.warning(f"Appointment {appointment_id} is not in CONFIRMED state")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only confirmed appointments can be updated by the doctor",
                )
            if new_status not in {AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW}:
                logging.warning(f"Unsupported appointment status transition requested: {new_status}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Doctor can only mark appointments as COMPLETED or NO_SHOW",
                )

            updated_appointment = await self.crud_appointment.update(
                id=appointment_id,
                obj_in={"status": new_status},
            )
            return self._serialize_document(updated_appointment)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AppointmentController.update_appointment_status: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_patient_appointments(self, patient_id: str) -> dict:
        """List appointments belonging to a patient.

        Args:
            patient_id: Patient identifier used for lookup.

        Returns:
            dict: Serialized appointment list payload.
        """

        try:
            logging.info("Executing AppointmentController.list_patient_appointments")
            appointments = await self.crud_appointment.get_by_patient_id(patient_id=patient_id)
            return {"items": self._serialize_documents(appointments)}
        except Exception as error:
            logging.error(f"Error in AppointmentController.list_patient_appointments: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_doctor_appointments(self, doctor_id: str) -> dict:
        """List appointments belonging to a doctor.

        Args:
            doctor_id: Doctor identifier used for lookup.

        Returns:
            dict: Serialized appointment list payload.
        """

        try:
            logging.info("Executing AppointmentController.list_doctor_appointments")
            appointments = await self.crud_appointment.get_by_doctor_id(doctor_id=doctor_id)
            return {"items": self._serialize_documents(appointments)}
        except Exception as error:
            logging.error(f"Error in AppointmentController.list_doctor_appointments: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def get_appointment_detail(self, appointment_id: str) -> dict:
        """Fetch an appointment together with lightweight participant names.

        Args:
            appointment_id: Appointment record identifier.

        Returns:
            dict: Detailed appointment payload with patient and doctor names.

        Raises:
            HTTPException 404: Appointment record does not exist.
        """

        try:
            logging.info("Executing AppointmentController.get_appointment_detail")
            appointment = await self.crud_appointment.get_by_id(id=appointment_id)
            if appointment is None:
                logging.warning(f"Appointment detail lookup failed for {appointment_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Appointment not found",
                )

            patient = await self.crud_user.get_by_id(id=appointment.patient_id)
            doctor = await self.crud_user.get_by_id(id=appointment.doctor_id)
            return {
                "appointment": self._serialize_document(appointment),
                "patient_name": patient.name if patient else None,
                "doctor_name": doctor.name if doctor else None,
            }
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AppointmentController.get_appointment_detail: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def _assert_patient(self, *, patient_id: str) -> None:
        """Ensure the target user exists, is a patient, and is OTP verified.

        Args:
            patient_id: User identifier expected to belong to a patient.

        Raises:
            HTTPException 404: Patient record does not exist.
            HTTPException 400: Patient account is not fully verified.
        """

        patient = await self.crud_user.get_by_id(id=patient_id)
        if patient is None or patient.role != UserRole.PATIENT:
            logging.warning(f"Patient lookup failed for appointment workflow: {patient_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )
        if not patient.is_otp_verified:
            logging.warning(f"Patient {patient_id} is not OTP verified")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient account must be verified before booking",
            )

    async def _assert_active_doctor(self, *, doctor_id: str) -> None:
        """Ensure the target user exists and is an active doctor.

        Args:
            doctor_id: User identifier expected to belong to an active doctor.

        Raises:
            HTTPException 404: Doctor record does not exist.
            HTTPException 400: Doctor account is not active.
        """

        doctor = await self.crud_user.get_by_id(id=doctor_id)
        if doctor is None or doctor.role != UserRole.DOCTOR:
            logging.warning(f"Doctor lookup failed for appointment workflow: {doctor_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found",
            )
        if doctor.doctor_status != DoctorStatus.ACTIVE:
            logging.warning(f"Doctor {doctor_id} is not active for bookings")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Doctor is not currently active for bookings",
            )

    async def _get_cancellable_appointment(self, *, appointment_id: str):
        """Fetch an appointment and ensure it is still manageable.

        Args:
            appointment_id: Appointment record identifier.

        Returns:
            Appointment: Appointment record eligible for lifecycle changes.

        Raises:
            HTTPException 404: Appointment record does not exist.
            HTTPException 400: Appointment is already finalized or cancelled.
        """

        appointment = await self.crud_appointment.get_by_id(id=appointment_id)
        if appointment is None:
            logging.warning(f"Appointment not found: {appointment_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found",
            )
        if appointment.status in {
            AppointmentStatus.CANCELLED,
            AppointmentStatus.RESCHEDULED,
            AppointmentStatus.COMPLETED,
            AppointmentStatus.NO_SHOW,
        }:
            logging.warning(f"Appointment {appointment_id} cannot be modified in state {appointment.status}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment cannot be modified in its current state",
            )
        return appointment

    async def _assert_actor_can_manage_appointment(self, *, appointment, actor_id: str, actor_role: UserRole) -> None:
        """Ensure the acting user is allowed to manage the appointment.

        Args:
            appointment: Appointment record being managed.
            actor_id: Acting user identifier.
            actor_role: Acting user role.

        Raises:
            HTTPException 403: User is not allowed to manage the appointment.
        """

        if actor_role not in {UserRole.PATIENT, UserRole.DOCTOR}:
            logging.warning(f"Unsupported actor role attempted appointment management: {actor_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This role cannot manage appointments",
            )
        if actor_role == UserRole.PATIENT and appointment.patient_id != actor_id:
            logging.warning(f"Patient {actor_id} cannot manage appointment {appointment.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this appointment",
            )
        if actor_role == UserRole.DOCTOR and appointment.doctor_id != actor_id:
            logging.warning(f"Doctor {actor_id} cannot manage appointment {appointment.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this appointment",
            )

    def _enforce_patient_time_window(self, *, appointment) -> None:
        """Ensure patient changes happen at least two hours before the slot.

        Args:
            appointment: Appointment record being updated by the patient.

        Raises:
            HTTPException 400: Appointment is too close to the scheduled time.
        """

        if self._normalize_datetime(appointment.date_time) - self._utc_now() < timedelta(hours=2):
            logging.warning(f"Patient time-window rule blocked changes for appointment {appointment.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patients can cancel or reschedule only up to 2 hours before the appointment",
            )

    def _ensure_future_datetime(self, *, date_time) -> None:
        """Ensure requested appointment slot time is in the future.

        Args:
            date_time: Requested appointment datetime in UTC.

        Raises:
            HTTPException 400: Requested slot is in the past.
        """

        if date_time <= self._utc_now():
            logging.warning(f"Appointment slot rejected because datetime is in the past: {date_time}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment slot must be in the future",
            )

    async def _ensure_slot_available(
        self,
        *,
        doctor_id: str,
        date_time,
        local_date_time=None,
    ) -> None:
        """Validate that a doctor is available for the requested datetime.

        Fetches all availability records for the doctor and filters in Python
        to avoid ODMantic query-encoding issues with enum/str fields.
        Uses local_date_time for HH:MM / day-of-week comparison so the doctor's
        locally-set schedule is matched correctly regardless of UTC offset.
        """

        cmp_dt = local_date_time if local_date_time is not None else date_time
        appointment_time_str = cmp_dt.strftime("%H:%M")
        day_name = cmp_dt.strftime("%A").upper()          # e.g. "FRIDAY"
        date_str = cmp_dt.date().isoformat()              # e.g. "2026-07-04"

        def _to_hhmm(t) -> str:
            """Normalise stored time value (str or time object) to HH:MM."""
            if t is None:
                return "00:00"
            s = str(t)  # covers datetime.time and str alike
            return s[:5]

        # Fetch ALL availability records for this doctor (no filter by day/time)
        all_avail = await self.crud_availability.get_by_doctor_id(doctor_id=doctor_id)

        # 1. Check exception slots for today
        for slot in all_avail:
            avail_type = slot.availability_type.value if hasattr(slot.availability_type, "value") else str(slot.availability_type)
            exc_date = slot.exception_date[:10] if isinstance(slot.exception_date, str) else (
                slot.exception_date.isoformat() if slot.exception_date else None
            )
            if exc_date != date_str:
                continue

            st = _to_hhmm(slot.start_time)
            et = _to_hhmm(slot.end_time)
            if not (st <= appointment_time_str < et):
                continue

            if avail_type == "EXCEPTION_BLOCKED":
                logging.warning(f"Doctor {doctor_id} has blocked exception slot at {cmp_dt}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Doctor is not available for the selected slot",
                )
            if avail_type == "EXCEPTION_AVAILABLE":
                return  # explicitly available — allow booking

        # 2. Check recurring weekly slots for this day
        for slot in all_avail:
            avail_type = slot.availability_type.value if hasattr(slot.availability_type, "value") else str(slot.availability_type)
            if avail_type != "RECURRING":
                continue

            slot_day = slot.day_of_week.value if hasattr(slot.day_of_week, "value") else str(slot.day_of_week)
            if slot_day != day_name:
                continue

            st = _to_hhmm(slot.start_time)
            et = _to_hhmm(slot.end_time)
            if st <= appointment_time_str < et:
                return  # found a matching slot — allow booking

        logging.warning(
            f"Doctor {doctor_id} has no availability for {cmp_dt} (local). "
            f"Day={day_name}, Time={appointment_time_str}. "
            f"Total slots found: {len(all_avail)}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor is not available for the selected slot",
        )
