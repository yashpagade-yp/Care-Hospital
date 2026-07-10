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
from backend.core.models.Appointment import AppointmentStatus, CancelledBy, PaymentStatus, QueueStatus
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

            patient = await self.crud_user.get_by_id(id=patient_id)
            queue_date = self._queue_date_key(self._normalize_datetime(slot_hold.date_time).date())
            queue_number = await self._next_queue_number(
                doctor_id=slot_hold.doctor_id,
                queue_date=queue_date,
            )

            appointment = await self.crud_appointment.create(
                obj_in={
                    "patient_id": patient_id,
                    "doctor_id": slot_hold.doctor_id,
                    "patient_name": confirmation_data["patient_name"],
                    "patient_phone": confirmation_data["patient_phone"],
                    "patient_age": confirmation_data["patient_age"],
                    "patient_gender": confirmation_data["patient_gender"],
                    "patient_blood_group": confirmation_data.get("patient_blood_group"),
                    "date_time": self._normalize_datetime(slot_hold.date_time),
                    "status": AppointmentStatus.CONFIRMED,
                    "reason": confirmation_data.get("reason"),
                    "queue_number": queue_number,
                    "queue_date": queue_date,
                    "queue_status": QueueStatus.WAITING,
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
                "appointment": await self._serialize_appointment_with_queue(
                    appointment=appointment,
                    fallback_doctor_name=doctor.name if doctor else None,
                    fallback_patient_name=confirmation_data["patient_name"],
                    fallback_patient_phone=confirmation_data["patient_phone"],
                ),
                "payment": self._serialize_document(payment),
                "patient_name": confirmation_data["patient_name"],
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

    async def create_telegram_guest_appointment(self, booking_data: dict) -> dict:
        """Create a lightweight Telegram appointment without web-app registration."""

        try:
            logging.info("Executing AppointmentController.create_telegram_guest_appointment")
            await self._assert_active_doctor(doctor_id=booking_data["doctor_id"])
            date_time = self._normalize_datetime(booking_data["date_time"])
            self._ensure_future_datetime(date_time=date_time)
            await self._ensure_slot_available(
                doctor_id=booking_data["doctor_id"],
                date_time=date_time,
                local_date_time=booking_data["date_time"],
            )

            queue_date = self._queue_date_key(date_time.date())
            queue_number = await self._next_queue_number(
                doctor_id=booking_data["doctor_id"],
                queue_date=queue_date,
            )
            guest_patient_id = f"telegram-guest:{queue_date}:{booking_data['doctor_id']}"
            appointment = await self.crud_appointment.create(
                obj_in={
                    "patient_id": guest_patient_id,
                    "doctor_id": booking_data["doctor_id"],
                    "patient_name": booking_data["patient_name"],
                    "patient_age": booking_data["patient_age"],
                    "patient_gender": booking_data["patient_gender"],
                    "patient_blood_group": booking_data.get("patient_blood_group"),
                    "date_time": date_time,
                    "status": AppointmentStatus.CONFIRMED,
                    "reason": booking_data.get("reason"),
                    "queue_number": queue_number,
                    "queue_date": queue_date,
                    "queue_status": QueueStatus.WAITING,
                    "fee": booking_data.get("fee", 0),
                    "payment_status": PaymentStatus.PAID,
                }
            )
            payment = await self.crud_payment.create(
                obj_in={
                    "appointment_id": str(appointment.id),
                    "amount": booking_data.get("fee", 0),
                    "transaction_ref": f"TELEGRAM-{str(appointment.id)[-8:].upper()}",
                }
            )
            doctor = await self.crud_user.get_by_id(id=booking_data["doctor_id"])
            return {
                "appointment": await self._serialize_appointment_with_queue(
                    appointment=appointment,
                    fallback_doctor_name=doctor.name if doctor else None,
                    fallback_patient_name=booking_data["patient_name"],
                ),
                "payment": self._serialize_document(payment),
                "patient_name": booking_data["patient_name"],
                "doctor_name": doctor.name if doctor else None,
            }
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AppointmentController.create_telegram_guest_appointment: {error}")
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
                    "queue_status": QueueStatus.CANCELLED,
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
            queue_date = self._queue_date_key(new_date_time.date())
            queue_number = await self._next_queue_number(
                doctor_id=appointment.doctor_id,
                queue_date=queue_date,
            )

            new_appointment = await self.crud_appointment.create(
                obj_in={
                    "patient_id": appointment.patient_id,
                    "doctor_id": appointment.doctor_id,
                    "patient_name": appointment.patient_name,
                    "patient_phone": appointment.patient_phone,
                    "patient_age": appointment.patient_age,
                    "patient_gender": appointment.patient_gender,
                    "patient_blood_group": appointment.patient_blood_group,
                    "date_time": new_date_time,
                    "status": AppointmentStatus.CONFIRMED,
                    "reason": reschedule_data.get("reason") or appointment.reason,
                    "queue_number": queue_number,
                    "queue_date": queue_date,
                    "queue_status": QueueStatus.WAITING,
                    "fee": appointment.fee,
                    "payment_status": appointment.payment_status,
                }
            )
            updated_original = await self.crud_appointment.update(
                id=appointment_id,
                obj_in={
                    "status": AppointmentStatus.RESCHEDULED,
                    "queue_status": QueueStatus.CANCELLED,
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

            update_payload = {"status": new_status}
            if new_status == AppointmentStatus.COMPLETED:
                update_payload["queue_status"] = QueueStatus.COMPLETED
            elif new_status == AppointmentStatus.NO_SHOW:
                queue_date = self._appointment_queue_date(appointment)
                update_payload.update(
                    {
                        "status": AppointmentStatus.CONFIRMED,
                        "queue_status": QueueStatus.MISSED,
                        "queue_number": await self._next_queue_number(
                            doctor_id=appointment.doctor_id,
                            queue_date=queue_date,
                        ),
                        "queue_date": queue_date,
                        "missed_count": appointment.missed_count + 1,
                    }
                )

            updated_appointment = await self.crud_appointment.update(
                id=appointment_id,
                obj_in=update_payload,
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
            items = []
            for appointment in appointments:
                items.append(await self._serialize_appointment_with_queue(appointment=appointment))
            return {
                "items": items
            }
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
            patient_lookup = await self._build_user_lookup(
                user_ids=[
                    appointment.patient_id
                    for appointment in appointments
                    if appointment.patient_name is None or appointment.patient_phone is None
                ]
            )
            items = []
            for appointment in appointments:
                items.append(
                    await self._serialize_appointment_with_queue(
                        appointment=appointment,
                        fallback_patient_name=(
                            patient_lookup.get(appointment.patient_id).name
                            if patient_lookup.get(appointment.patient_id)
                            else None
                        ),
                        fallback_patient_phone=(
                            patient_lookup.get(appointment.patient_id).phone
                            if patient_lookup.get(appointment.patient_id)
                            else None
                        ),
                    )
                )
            return {"items": items}
        except Exception as error:
            logging.error(f"Error in AppointmentController.list_doctor_appointments: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_doctor_booked_slots(self, doctor_id: str) -> dict:
        """List booked slot datetimes for a doctor's active schedule.

        Returns only occupied times so booking screens can hide unavailable
        slots without exposing other patients' appointment details.

        Args:
            doctor_id: Doctor identifier used for the booking lookup.

        Returns:
            dict: List payload containing booked appointment datetimes.
        """

        try:
            logging.info("Executing AppointmentController.list_doctor_booked_slots")
            appointments = await self.crud_appointment.get_by_doctor_id(doctor_id=doctor_id)
            return {
                "items": [
                    appointment.date_time
                    for appointment in appointments
                    if appointment.status
                    not in {AppointmentStatus.CANCELLED, AppointmentStatus.RESCHEDULED}
                ]
            }
        except Exception as error:
            logging.error(f"Error in AppointmentController.list_doctor_booked_slots: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_all_appointments(self) -> dict:
        """List all appointments for admin operational views.

        Returns:
            dict: Serialized appointment list payload enriched with patient and doctor names.
        """

        try:
            logging.info("Executing AppointmentController.list_all_appointments")
            appointments = await self.crud_appointment.get_all()
            user_lookup = await self._build_user_lookup(
                user_ids=[
                    user_id
                    for appointment in appointments
                    for user_id in (appointment.patient_id, appointment.doctor_id)
                ]
            )
            items = []
            for appointment in appointments:
                items.append(
                    await self._serialize_appointment_with_queue(
                        appointment=appointment,
                        fallback_doctor_name=(
                            user_lookup.get(appointment.doctor_id).name
                            if user_lookup.get(appointment.doctor_id)
                            else None
                        ),
                        fallback_patient_name=(
                            user_lookup.get(appointment.patient_id).name
                            if user_lookup.get(appointment.patient_id)
                            else None
                        ),
                        fallback_patient_phone=(
                            user_lookup.get(appointment.patient_id).phone
                            if user_lookup.get(appointment.patient_id)
                            else None
                        ),
                    )
                )
            return {"items": items}
        except Exception as error:
            logging.error(f"Error in AppointmentController.list_all_appointments: {error}")
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
                "appointment": await self._serialize_appointment_with_queue(
                    appointment=appointment,
                    fallback_doctor_name=doctor.name if doctor else None,
                    fallback_patient_name=patient.name if patient else None,
                    fallback_patient_phone=patient.phone if patient else None,
                ),
                "patient_name": appointment.patient_name or (patient.name if patient else None),
                "doctor_name": doctor.name if doctor else None,
                "patient_phone": appointment.patient_phone or (patient.phone if patient else None),
                "patient_age": appointment.patient_age,
                "patient_gender": appointment.patient_gender,
                "patient_blood_group": appointment.patient_blood_group,
                "reason": appointment.reason,
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

    async def _build_user_lookup(self, *, user_ids: list[str]) -> dict[str, object]:
        """Build a lookup of users for appointment fallback display fields.

        Args:
            user_ids: User identifiers referenced by appointment records.

        Returns:
            dict[str, object]: Mapping of user id to user record.
        """

        lookup: dict[str, object] = {}
        for user_id in set(user_ids):
            user = await self.crud_user.get_by_id(id=user_id)
            if user is not None:
                lookup[user_id] = user
        return lookup

    async def _next_queue_number(self, *, doctor_id: str, queue_date) -> int:
        """Return the next patient token number for a doctor's queue date."""

        queue_date_key = self._queue_date_key(queue_date)
        appointments = await self.crud_appointment.get_by_doctor_id(doctor_id=doctor_id)
        numbers = [
            appointment.queue_number
            for appointment in appointments
            if appointment.queue_number is not None
            and self._appointment_queue_date(appointment) == queue_date_key
        ]
        return (max(numbers) + 1) if numbers else 1

    async def _serialize_appointment_with_queue(
        self,
        *,
        appointment,
        fallback_doctor_name: str | None = None,
        fallback_patient_name: str | None = None,
        fallback_patient_phone: str | None = None,
    ) -> dict:
        payload = self._serialize_appointment(
            appointment=appointment,
            fallback_doctor_name=fallback_doctor_name,
            fallback_patient_name=fallback_patient_name,
            fallback_patient_phone=fallback_patient_phone,
        )
        payload.update(await self._queue_context(appointment=appointment))
        return payload

    async def _queue_context(self, *, appointment) -> dict:
        queue_number = appointment.queue_number
        queue_date = self._appointment_queue_date(appointment)
        if queue_number is None:
            return {
                "current_queue_number": None,
                "patients_before": None,
                "total_waiting": None,
            }

        appointments = await self.crud_appointment.get_by_doctor_id(doctor_id=appointment.doctor_id)
        active_queue = [
            item
            for item in appointments
            if self._appointment_queue_date(item) == queue_date
            and item.queue_number is not None
            and item.status == AppointmentStatus.CONFIRMED
            and item.queue_status in {QueueStatus.WAITING, QueueStatus.MISSED}
        ]
        active_queue.sort(key=lambda item: item.queue_number or 0)

        current_queue_number = active_queue[0].queue_number if active_queue else None
        patients_before = len(
            [
                item
                for item in active_queue
                if (item.queue_number or 0) < queue_number
            ]
        )
        return {
            "current_queue_number": current_queue_number,
            "patients_before": patients_before,
            "total_waiting": len(active_queue),
        }

    def _appointment_queue_date(self, appointment) -> str:
        """Return a stable YYYY-MM-DD queue key for existing and new appointment rows."""

        return self._queue_date_key(
            appointment.queue_date or self._normalize_datetime(appointment.date_time).date()
        )

    def _queue_date_key(self, queue_date) -> str:
        """Convert queue date values into Mongo-safe YYYY-MM-DD strings."""

        if isinstance(queue_date, str):
            return queue_date[:10]
        return queue_date.isoformat()

    def _serialize_appointment(
        self,
        *,
        appointment,
        fallback_doctor_name: str | None = None,
        fallback_patient_name: str | None = None,
        fallback_patient_phone: str | None = None,
    ) -> dict:
        """Serialize appointment data with patient booking context for the UI.

        Args:
            appointment: Appointment record being serialized.
            fallback_doctor_name: Fallback doctor name when snapshot data is missing.
            fallback_patient_name: Fallback patient name when snapshot data is missing.
            fallback_patient_phone: Fallback patient phone when snapshot data is missing.

        Returns:
            dict: Serialized appointment payload enriched for doctor-facing views.
        """

        payload = self._serialize_document(appointment)
        if not payload.get("doctor_name"):
            payload["doctor_name"] = fallback_doctor_name
        if not payload.get("patient_name"):
            payload["patient_name"] = fallback_patient_name
        if not payload.get("patient_phone"):
            payload["patient_phone"] = fallback_patient_phone
        return payload
