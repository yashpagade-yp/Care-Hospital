"""Authentication and password-reset controller logic for the MedCare backend."""

from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status

from backend.commons.auth import (
    encrypt_password,
    generate_otp,
    hash_otp,
    signJWT,
    verify_hashed_otp,
    verify_password,
)
from backend.commons.logger import logger
from backend.core.controllers.base_controller import BaseController
from backend.core.cruds.user_crud import CRUDUser
from backend.core.models.user_model import DoctorStatus, OtpPurpose, UserRole
from backend.core.utils.email.email_helper import send_email
from backend.core.utils.email.email_template_generator import generate_email_template

logging = logger(__name__)


class AuthController(BaseController):
    """Controller for login, OTP resend, and password reset workflows."""

    def __init__(self):
        """Initialize CRUD dependencies used by auth workflows."""

        self.crud_user = CRUDUser()

    async def login(self, email: str, password: str) -> dict:
        """Verify credentials for all roles and dispatch a login OTP.

        Phase 1 of the two-step login flow. Validates email and password,
        then sends a LOGIN_VERIFY OTP to the user's registered email address.
        No access token is returned at this stage.

        Args:
            email: Email address used for login.
            password: Plain-text password submitted by the user.

        Returns:
            dict: OTP dispatch metadata — message, email, and purpose.

        Raises:
            HTTPException 401: Credentials are invalid.
            HTTPException 403: Doctor profile setup is incomplete.
        """

        try:
            logging.info("Executing AuthController.login")
            user = await self.crud_user.get_by_email(email=email.lower())
            if user is None or not verify_password(password, user.password_hash):
                logging.warning(f"Login failed for email {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            if user.role in {UserRole.PATIENT, UserRole.DOCTOR} and not user.is_otp_verified:
                logging.warning(f"Login blocked because registration is incomplete for {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Please complete your registration before logging in",
                )

            if user.role == UserRole.DOCTOR and user.doctor_status != DoctorStatus.ACTIVE:
                logging.warning(f"Doctor login blocked because profile setup is incomplete for {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your doctor profile setup must be completed before you can log in",
                )

            otp_payload, otp_code = self._issue_otp_payload(purpose=OtpPurpose.LOGIN_VERIFY)
            await self._send_otp_email(
                email=user.email,
                recipient_name=user.name,
                otp_code=otp_code,
                purpose=OtpPurpose.LOGIN_VERIFY,
            )
            await self.crud_user.update(
                id=str(user.id),
                obj_in={"otp": otp_payload},
            )
            return {
                "message": "A 6-digit verification code has been sent to your email",
                "email": user.email,
                "purpose": OtpPurpose.LOGIN_VERIFY,
            }
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AuthController.login: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def verify_login_otp(self, email: str, otp: str) -> dict:
        """Verify the login OTP and issue the access token.

        Phase 2 of the two-step login flow. Validates the LOGIN_VERIFY OTP
        and returns the signed JWT access token with role and user summary.

        Args:
            email: Email address verifying the login OTP.
            otp: Plain 6-digit OTP submitted by the user.

        Returns:
            dict: Auth response payload with access token, role, and user summary.

        Raises:
            HTTPException 400: OTP is invalid or expired.
            HTTPException 404: User does not exist.
        """

        try:
            logging.info("Executing AuthController.verify_login_otp")
            user = await self._get_user_by_email(email=email)
            await self._validate_otp(
                user=user,
                otp=otp,
                expected_purpose=OtpPurpose.LOGIN_VERIFY,
            )
            return {
                "access_token": signJWT(user_role=user.role.value, id=str(user.id)),
                "token_type": "bearer",
                "role": user.role,
                "user": self._serialize_document(user),
            }
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AuthController.verify_login_otp: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def resend_otp(self, email: str, purpose: OtpPurpose) -> dict:
        """Reissue an OTP for registration or password reset workflows.

        Args:
            email: Email address that should receive the OTP.
            purpose: Business purpose for the newly issued OTP.

        Returns:
            dict: OTP dispatch response payload.

        Raises:
            HTTPException 404: User does not exist for the requested flow.
            HTTPException 400: User role does not match the OTP purpose.
        """

        try:
            logging.info("Executing AuthController.resend_otp")
            user = await self.crud_user.get_by_email(email=email.lower())
            if user is None:
                logging.warning(f"OTP resend failed because user was not found for {email}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            self._assert_otp_purpose_matches_user(user_role=user.role, purpose=purpose)
            otp_payload, otp_code = self._issue_otp_payload(purpose=purpose)
            await self._send_otp_email(
                email=user.email,
                recipient_name=user.name,
                otp_code=otp_code,
                purpose=purpose,
            )
            await self.crud_user.update(
                id=str(user.id),
                obj_in={"otp": otp_payload},
            )
            return {
                "message": "OTP sent successfully",
                "email": user.email,
                "purpose": purpose,
            }
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AuthController.resend_otp: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def forgot_password(self, email: str) -> dict:
        """Start a password reset flow without revealing account existence.

        Args:
            email: Email address requesting password reset.

        Returns:
            dict: Generic password reset OTP dispatch response payload.
        """

        try:
            logging.info("Executing AuthController.forgot_password")
            user = await self.crud_user.get_by_email(email=email.lower())
            if user is not None:
                otp_payload, otp_code = self._issue_otp_payload(
                    purpose=OtpPurpose.PASSWORD_RESET_VERIFY
                )
                await self._send_otp_email(
                    email=user.email,
                    recipient_name=user.name,
                    otp_code=otp_code,
                    purpose=OtpPurpose.PASSWORD_RESET_VERIFY,
                )
                await self.crud_user.update(
                    id=str(user.id),
                    obj_in={"otp": otp_payload},
                )
            else:
                logging.warning(f"Forgot-password requested for non-existent email {email}")

            return {
                "message": "If the email is registered, a password reset OTP has been sent",
                "email": email.lower(),
                "purpose": OtpPurpose.PASSWORD_RESET_VERIFY,
            }
        except Exception as error:
            logging.error(f"Error in AuthController.forgot_password: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def verify_password_reset_otp(self, email: str, otp: str) -> dict:
        """Validate an OTP issued for password reset.

        Args:
            email: Email address verifying the reset OTP.
            otp: Plain OTP code submitted by the user.

        Returns:
            dict: Human-readable verification response payload.

        Raises:
            HTTPException 400: OTP is invalid or expired.
            HTTPException 404: User does not exist.
        """

        try:
            logging.info("Executing AuthController.verify_password_reset_otp")
            user = await self._get_user_by_email(email=email)
            await self._validate_otp(
                user=user,
                otp=otp,
                expected_purpose=OtpPurpose.PASSWORD_RESET_VERIFY,
            )
            return {"message": "Password reset OTP verified successfully"}
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AuthController.verify_password_reset_otp: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def reset_password(self, email: str, otp: str, new_password: str) -> dict:
        """Reset a user's password after validating the reset OTP.

        Args:
            email: Email address resetting its password.
            otp: Verified password reset OTP.
            new_password: New plain-text password to persist.

        Returns:
            dict: Human-readable password reset completion payload.

        Raises:
            HTTPException 400: OTP is invalid or expired.
            HTTPException 404: User does not exist.
        """

        try:
            logging.info("Executing AuthController.reset_password")
            user = await self._get_user_by_email(email=email)
            await self._validate_otp(
                user=user,
                otp=otp,
                expected_purpose=OtpPurpose.PASSWORD_RESET_VERIFY,
            )
            updated_otp_payload = {
                **user.otp.model_dump(),
                "verified_at": self._utc_now(),
            }
            await self.crud_user.update(
                id=str(user.id),
                obj_in={
                    "password_hash": encrypt_password(new_password),
                    "otp": updated_otp_payload,
                },
            )
            return {"message": "Password reset successfully"}
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AuthController.reset_password: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    def _issue_otp_payload(self, *, purpose: OtpPurpose) -> tuple[dict, str]:
        """Build a hashed OTP payload and return the plain OTP for email delivery.

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

    async def _get_user_by_email(self, *, email: str):
        """Read a user record by email.

        Args:
            email: Email address used for the lookup.

        Returns:
            User: Matching user record.

        Raises:
            HTTPException 404: User does not exist.
        """

        user = await self.crud_user.get_by_email(email=email.lower())
        if user is None:
            logging.warning(f"User not found for email {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    def _assert_otp_purpose_matches_user(self, *, user_role: UserRole, purpose: OtpPurpose) -> None:
        """Ensure the requested OTP purpose fits the user's role workflow.

        Args:
            user_role: Role stored on the user account.
            purpose: Requested OTP business purpose.

        Raises:
            HTTPException 400: OTP purpose does not match the user role.
        """

        if purpose == OtpPurpose.PATIENT_REGISTER_VERIFY and user_role != UserRole.PATIENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP purpose does not match this user",
            )
        if purpose == OtpPurpose.DOCTOR_INVITE_VERIFY and user_role != UserRole.DOCTOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP purpose does not match this user",
            )

    async def _validate_otp(self, *, user, otp: str, expected_purpose: OtpPurpose) -> None:
        """Validate stored OTP state for the requested auth workflow.

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
        """Send an OTP email for resend or password-reset workflows.

        Args:
            email: Recipient email address.
            recipient_name: Display name used in the email body.
            otp_code: Plain OTP to deliver by email.
            purpose: Workflow that triggered the OTP.

        Raises:
            HTTPException 500: OTP email delivery failed.
        """

        if purpose == OtpPurpose.PASSWORD_RESET_VERIFY:
            title = "Reset your MedCare password"
            description = "Use this one-time code to reset your MedCare password. The code expires in 10 minutes."
        elif purpose == OtpPurpose.DOCTOR_INVITE_VERIFY:
            title = "Verify your MedCare doctor onboarding"
            description = "Use this one-time code to continue your doctor onboarding. The code expires in 10 minutes."
        elif purpose == OtpPurpose.LOGIN_VERIFY:
            title = "Your MedCare login code"
            description = "Use this 6-digit code to complete your login. The code expires in 10 minutes. If you did not request this, please ignore this email."
        else:
            title = "Verify your MedCare account"
            description = "Use this one-time code to verify your MedCare account. The code expires in 10 minutes."

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
            logging.error(f"Error in AuthController._send_otp_email: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP email",
            )
