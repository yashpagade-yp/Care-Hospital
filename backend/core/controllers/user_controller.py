"""User and onboarding controller logic for the MedCare backend."""

from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status

from backend.commons.auth import (
    encrypt_password,
    generate_otp,
    hash_otp,
    verify_hashed_otp,
)
from backend.commons.logger import logger
from backend.core.controllers.base_controller import BaseController
from backend.core.cruds.availability_crud import CRUDDoctorAvailability
from backend.core.cruds.invitation_crud import CRUDDoctorInvitation
from backend.core.cruds.user_crud import CRUDUser
from backend.core.models.DoctorAvailability import AvailabilityType
from backend.core.models.Invitation import InvitationStatus
from backend.core.models.user_model import DoctorStatus, OtpPurpose, UserRole
from backend.core.utils.email.email_helper import send_email
from backend.core.utils.email.email_template_generator import generate_email_template

logging = logger(__name__)


class UserController(BaseController):
    """Controller for patient registration and doctor onboarding workflows."""

    def __init__(self):
        """Initialize CRUD dependencies used by user workflows."""

        self.crud_user = CRUDUser()
        self.crud_invitation = CRUDDoctorInvitation()
        self.crud_availability = CRUDDoctorAvailability()

    async def register_patient(self, patient_data: dict) -> dict:
        """Register a new patient account and issue a verification OTP.

        Args:
            patient_data: Patient registration payload from the request schema.

        Returns:
            dict: Serialized patient summary payload with a success message.

        Raises:
            HTTPException 409: Patient email already exists.
            HTTPException 500: Registration failed unexpectedly.
        """

        try:
            logging.info("Executing UserController.register_patient")
            email = patient_data["email"].lower()
            existing_user = await self.crud_user.get_by_email(email=email)
            if existing_user:
                logging.warning(f"Patient registration blocked for existing email {email}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists",
                )

            otp_payload, plain_otp = self._issue_otp_payload(
                purpose=OtpPurpose.PATIENT_REGISTER_VERIFY,
            )
            await self._send_otp_email(
                email=email,
                recipient_name=patient_data["name"],
                otp_code=plain_otp,
                purpose=OtpPurpose.PATIENT_REGISTER_VERIFY,
            )
            user = await self.crud_user.create(
                obj_in={
                    "name": patient_data["name"],
                    "phone": patient_data["phone"],
                    "email": email,
                    "password_hash": encrypt_password(patient_data["password"]),
                    "role": UserRole.PATIENT,
                    "is_otp_verified": False,
                    "otp": otp_payload,
                }
            )
            response = self._serialize_user_document(user)
            response["message"] = "Patient registered successfully. Verify OTP to activate the account."
            return response
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in UserController.register_patient: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def verify_patient_otp(self, email: str, otp: str) -> dict:
        """Verify the OTP sent during patient registration.

        Args:
            email: Patient email address receiving the OTP.
            otp: Plain OTP code entered by the patient.

        Returns:
            dict: Serialized patient profile payload after verification.

        Raises:
            HTTPException 400: OTP is missing, invalid, or expired.
            HTTPException 404: Patient account does not exist.
        """

        try:
            logging.info("Executing UserController.verify_patient_otp")
            user = await self._get_user_by_email_and_role(
                email=email,
                role=UserRole.PATIENT,
            )
            await self._validate_otp(
                user=user,
                otp=otp,
                expected_purpose=OtpPurpose.PATIENT_REGISTER_VERIFY,
            )

            updated_user = await self.crud_user.update(
                id=str(user.id),
                obj_in={
                    "is_otp_verified": True,
                    "otp": {
                        **user.otp.model_dump(),
                        "verified_at": self._utc_now(),
                    },
                },
            )
            return self._serialize_user_document(updated_user)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in UserController.verify_patient_otp: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def set_doctor_credentials(self, doctor_data: dict) -> dict:
        """Create a doctor account after validating an invitation token.

        Args:
            doctor_data: Doctor credential setup payload from onboarding.

        Returns:
            dict: Serialized doctor payload with onboarding progress message.

        Raises:
            HTTPException 400: Invitation is invalid, expired, or email mismatched.
            HTTPException 409: Doctor account already exists.
        """

        try:
            logging.info("Executing UserController.set_doctor_credentials")
            email = doctor_data["email"].lower()
            invitation = await self.crud_invitation.get_by_token(token=doctor_data["token"])
            invitation = await self._ensure_invitation_usable(invitation=invitation)

            if invitation.doctor_email.lower() != email:
                logging.warning(
                    f"Doctor invitation email mismatch for token {doctor_data['token'][:8]}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invitation email does not match the provided email",
                )

            existing_user = await self.crud_user.get_by_email(email=email)
            if existing_user:
                logging.warning(f"Doctor credential setup blocked for existing email {email}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Doctor account already exists",
                )

            otp_payload, plain_otp = self._issue_otp_payload(
                purpose=OtpPurpose.DOCTOR_INVITE_VERIFY,
            )
            await self._send_otp_email(
                email=email,
                recipient_name=email.split("@")[0],
                otp_code=plain_otp,
                purpose=OtpPurpose.DOCTOR_INVITE_VERIFY,
            )
            user = await self.crud_user.create(
                obj_in={
                    "name": email.split("@")[0],
                    "email": email,
                    "password_hash": encrypt_password(doctor_data["password"]),
                    "role": UserRole.DOCTOR,
                    "is_otp_verified": False,
                    "doctor_status": DoctorStatus.REGISTERED,
                    "otp": otp_payload,
                }
            )
            await self.crud_invitation.update(
                id=str(invitation.id),
                obj_in={"status": InvitationStatus.ACCEPTED},
            )

            response = self._serialize_user_document(user)
            response["message"] = "Doctor credentials saved successfully. Verify OTP to continue onboarding."
            return response
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in UserController.set_doctor_credentials: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def verify_doctor_otp(self, email: str, otp: str) -> dict:
        """Verify the OTP issued during doctor onboarding.

        Args:
            email: Doctor email address receiving the OTP.
            otp: Plain OTP code entered by the doctor.

        Returns:
            dict: Serialized doctor profile payload after verification.

        Raises:
            HTTPException 400: OTP is missing, invalid, or expired.
            HTTPException 404: Doctor account does not exist.
        """

        try:
            logging.info("Executing UserController.verify_doctor_otp")
            user = await self._get_user_by_email_and_role(
                email=email,
                role=UserRole.DOCTOR,
            )
            await self._validate_otp(
                user=user,
                otp=otp,
                expected_purpose=OtpPurpose.DOCTOR_INVITE_VERIFY,
            )

            updated_user = await self.crud_user.update(
                id=str(user.id),
                obj_in={
                    "is_otp_verified": True,
                    "otp": {
                        **user.otp.model_dump(),
                        "verified_at": self._utc_now(),
                    },
                },
            )
            return self._serialize_user_document(updated_user)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in UserController.verify_doctor_otp: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def complete_doctor_profile(self, profile_data: dict) -> dict:
        """Complete the one-time doctor profile setup and initial availability.

        Args:
            profile_data: Doctor professional profile and working-slot payload.

        Returns:
            dict: Serialized doctor profile payload after activation.

        Raises:
            HTTPException 400: Doctor onboarding is incomplete or profile already exists.
            HTTPException 404: Doctor account does not exist.
        """

        try:
            logging.info("Executing UserController.complete_doctor_profile")
            user = await self._get_user_by_email_and_role(
                email=profile_data["email"],
                role=UserRole.DOCTOR,
            )
            if not user.is_otp_verified:
                logging.warning(f"Doctor profile completion blocked for unverified email {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Doctor OTP verification is required before completing the profile",
                )

            if user.specialty or user.qualification or user.experience_years is not None:
                logging.warning(f"Doctor profile already completed for user {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Doctor profile has already been completed",
                )

            updated_user = await self.crud_user.update(
                id=str(user.id),
                obj_in={
                    "name": profile_data["name"],
                    "qualification": profile_data["qualification"],
                    "specialty": profile_data["specialty"],
                    "experience_years": profile_data["experience_years"],
                    "services": profile_data["services"],
                    "doctor_status": DoctorStatus.ACTIVE,
                },
            )

            for slot in profile_data.get("working_slots", []):
                existing_slots = await self.crud_availability.get_recurring_slots(
                    doctor_id=str(updated_user.id),
                    day_of_week=slot["day_of_week"],
                )
                has_duplicate = any(
                    existing_slot.start_time == slot["start_time"]
                    and existing_slot.end_time == slot["end_time"]
                    for existing_slot in existing_slots
                )
                if has_duplicate:
                    continue

                await self.crud_availability.create(
                    obj_in={
                        "doctor_id": str(updated_user.id),
                        "availability_type": AvailabilityType.RECURRING,
                        "day_of_week": slot["day_of_week"],
                        # Convert time objects to HH:MM strings for MongoDB
                        "start_time": slot["start_time"].strftime("%H:%M") if hasattr(slot["start_time"], "strftime") else str(slot["start_time"])[:5],
                        "end_time": slot["end_time"].strftime("%H:%M") if hasattr(slot["end_time"], "strftime") else str(slot["end_time"])[:5],
                    }
                )

            return self._serialize_user_document(updated_user)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in UserController.complete_doctor_profile: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def get_user_profile(self, user_id: str) -> dict:
        """Fetch a user profile by unique identifier.

        Args:
            user_id: Persisted user record identifier.

        Returns:
            dict: Serialized user profile payload.

        Raises:
            HTTPException 404: User record does not exist.
        """

        try:
            logging.info("Executing UserController.get_user_profile")
            user = await self.crud_user.get_by_id(id=user_id)
            if user is None:
                logging.warning(f"User not found: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            return self._serialize_user_document(user)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in UserController.get_user_profile: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_doctors(self) -> dict:
        """List doctor accounts for admin and patient dashboard views.

        Returns:
            dict: Serialized doctor profile list payload.
        """

        try:
            logging.info("Executing UserController.list_doctors")
            doctors = await self.crud_user.get_doctors()
            return {"items": self._serialize_user_documents(doctors)}
        except Exception as error:
            logging.error(f"Error in UserController.list_doctors: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_patients(self) -> dict:
        """List patient accounts for operational views.

        Returns:
            dict: Serialized patient profile list payload.
        """

        try:
            logging.info("Executing UserController.list_patients")
            patients = await self.crud_user.get_patients()
            return {"items": self._serialize_user_documents(patients)}
        except Exception as error:
            logging.error(f"Error in UserController.list_patients: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    def _issue_otp_payload(self, *, purpose: OtpPurpose) -> tuple[dict, str]:
        """Build a hashed OTP payload and return the plain OTP once for email use.

        Args:
            purpose: OTP business purpose stored on the account.

        Returns:
            tuple[dict, str]: Persistable OTP payload and the plain OTP code.
        """

        otp_code = generate_otp()
        expires_at = self._utc_now() + timedelta(minutes=10)
        return (
            {
                "otp_code": hash_otp(otp_code),
                "purpose": purpose,
                "expires_at": expires_at,
                "verified_at": None,
                "created_at": self._utc_now(),
            },
            otp_code,
        )

    async def _get_user_by_email_and_role(self, *, email: str, role: UserRole):
        """Read a user record by email and enforce the expected role.

        Args:
            email: Email address used for the lookup.
            role: Expected role for the user record.

        Returns:
            User: Matching user record.

        Raises:
            HTTPException 404: User does not exist.
            HTTPException 400: Role does not match the requested workflow.
        """

        user = await self.crud_user.get_by_email(email=email.lower())
        if user is None:
            logging.warning(f"User not found for email {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if user.role != role:
            logging.warning(f"User role mismatch for email {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User role does not match this workflow",
            )
        return user

    async def _ensure_invitation_usable(self, *, invitation):
        """Validate that a doctor invitation exists and can still be used.

        Args:
            invitation: Doctor invitation persistence object.

        Returns:
            DoctorInvitation: Valid invitation record.

        Raises:
            HTTPException 400: Invitation is missing, revoked, accepted, or expired.
        """

        if invitation is None:
            logging.warning("Doctor invitation token lookup returned no record")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation token is invalid",
            )

        if self._normalize_datetime(invitation.expires_at) <= self._utc_now():
            await self.crud_invitation.update(
                id=str(invitation.id),
                obj_in={"status": InvitationStatus.EXPIRED},
            )
            logging.warning(f"Doctor invitation expired: {invitation.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation has expired",
            )

        if invitation.status != InvitationStatus.PENDING:
            logging.warning(f"Doctor invitation status invalid: {invitation.status}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation is no longer available",
            )

        return invitation

    async def _validate_otp(self, *, user, otp: str, expected_purpose: OtpPurpose) -> None:
        """Validate stored OTP state for a patient or doctor account.

        Args:
            user: User record containing embedded OTP state.
            otp: Plain OTP value provided by the user.
            expected_purpose: Required OTP purpose for the workflow.

        Raises:
            HTTPException 400: OTP state is missing, invalid, or expired.
        """

        if user.otp is None:
            logging.warning(f"OTP not found for user {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP was not issued for this account",
            )
        if user.otp.purpose != expected_purpose:
            logging.warning(f"OTP purpose mismatch for user {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP does not match this verification flow",
            )
        if self._normalize_datetime(user.otp.expires_at) <= self._utc_now():
            logging.warning(f"OTP expired for user {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired",
            )
        if not verify_hashed_otp(otp, user.otp.otp_code):
            logging.warning(f"Invalid OTP supplied for user {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP is invalid",
            )

    async def _send_otp_email(
        self,
        *,
        email: str,
        recipient_name: str,
        otp_code: str,
        purpose: OtpPurpose,
    ) -> None:
        """Send an OTP email for patient registration or doctor onboarding.

        Args:
            email: Recipient email address.
            recipient_name: Display name used in the email body.
            otp_code: Plain OTP to deliver to the recipient.
            purpose: Workflow that triggered the OTP email.

        Raises:
            HTTPException 500: OTP email delivery failed.
        """

        if purpose == OtpPurpose.PATIENT_REGISTER_VERIFY:
            title = "Verify your MedCare patient account"
            description = "Use this one-time password to complete your patient registration. The code expires in 10 minutes."
        else:
            title = "Verify your MedCare doctor onboarding"
            description = "Use this one-time password to continue your doctor onboarding flow. The code expires in 10 minutes."

        template = generate_email_template(
            name=recipient_name,
            subject=title,
            title=title,
            description=description,
            action_code=otp_code,
        )
        try:
            await send_email(
                subject=template["subject"],
                to_email=email,
                text=template["text"],
                html=template["html"],
            )
        except Exception as error:
            logging.error(f"Error in UserController._send_otp_email: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP email",
            )

    async def delete_doctor(self, doctor_id: str, admin_user_id: str) -> dict:
        """Permanently delete a doctor account from the platform.

        Admin-only action. Verifies the requesting user is an admin and the
        target user is a doctor before removing the record from the database.

        Args:
            doctor_id: The doctor user identifier to delete.
            admin_user_id: The admin user performing the deletion.

        Returns:
            dict: Confirmation message payload.

        Raises:
            HTTPException 403: Acting user is not an admin.
            HTTPException 404: Doctor not found or target is not a doctor.
        """

        try:
            logging.info("Executing UserController.delete_doctor")
            admin = await self.crud_user.get_by_id(id=admin_user_id)
            if admin is None or admin.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can remove doctor accounts",
                )
            doctor = await self.crud_user.get_by_id(id=doctor_id)
            if doctor is None or doctor.role != UserRole.DOCTOR:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Doctor not found",
                )
            await self.crud_user.delete(id=doctor_id)
            return {"message": "Doctor account removed successfully"}
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in UserController.delete_doctor: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def suspend_doctor(self, doctor_id: str, admin_user_id: str) -> dict:
        """Suspend a doctor account so they cannot receive new bookings.

        Admin-only action. Sets doctor_status to SUSPENDED on the target doctor.

        Args:
            doctor_id: The doctor user identifier to suspend.
            admin_user_id: The admin user performing the suspension.

        Returns:
            dict: Updated doctor profile payload.

        Raises:
            HTTPException 403: Acting user is not an admin.
            HTTPException 404: Doctor not found or target is not a doctor.
        """

        try:
            logging.info("Executing UserController.suspend_doctor")
            admin = await self.crud_user.get_by_id(id=admin_user_id)
            if admin is None or admin.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can suspend doctor accounts",
                )
            doctor = await self.crud_user.get_by_id(id=doctor_id)
            if doctor is None or doctor.role != UserRole.DOCTOR:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Doctor not found",
                )
            updated_doctor = await self.crud_user.update(
                id=doctor_id,
                obj_in={"doctor_status": DoctorStatus.SUSPENDED},
            )
            return self._serialize_user_document(updated_doctor)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in UserController.suspend_doctor: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    def _serialize_user_document(self, user) -> dict:
        """Serialize a user record and normalize doctor-only list fields.

        Doctor onboarding returns partially completed accounts before profile
        setup finishes, so list-shaped doctor fields are normalized for stable
        API responses during that intermediate state.

        Args:
            user: Persisted user model instance to serialize.

        Returns:
            dict: Response-safe user payload with doctor list fields normalized.
        """

        payload = self._serialize_document(user)
        if payload.get("role") == UserRole.DOCTOR and payload.get("services") is None:
            payload["services"] = []
        return payload

    def _serialize_user_documents(self, users: list) -> list[dict]:
        """Serialize multiple user records with doctor field normalization.

        Args:
            users: Sequence of persisted user models.

        Returns:
            list[dict]: Response-safe serialized user payloads.
        """

        return [self._serialize_user_document(user) for user in users]
