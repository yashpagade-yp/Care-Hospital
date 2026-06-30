"""Doctor invitation controller logic for the MedCare backend."""

from __future__ import annotations

import secrets
from datetime import timedelta

from fastapi import HTTPException, status

from backend.commons.logger import logger
from backend.core.controllers.base_controller import BaseController
from backend.core.cruds.invitation_crud import CRUDDoctorInvitation
from backend.core.cruds.user_crud import CRUDUser
from backend.core.models.Invitation import InvitationStatus
from backend.core.models.user_model import UserRole

logging = logger(__name__)


class InvitationController(BaseController):
    """Controller for admin-managed doctor invitation workflows."""

    def __init__(self):
        """Initialize CRUD dependencies used by invitation workflows."""

        self.crud_invitation = CRUDDoctorInvitation()
        self.crud_user = CRUDUser()

    async def create_doctor_invitation(self, doctor_email: str, admin_user_id: str) -> dict:
        """Create a new doctor invitation for an admin-selected email.

        Args:
            doctor_email: Target doctor email to invite.
            admin_user_id: Admin user creating the invitation.

        Returns:
            dict: Serialized invitation payload.

        Raises:
            HTTPException 403: Acting user is not an admin.
            HTTPException 409: Active invitation or doctor account already exists.
        """

        try:
            logging.info("Executing InvitationController.create_doctor_invitation")
            await self._assert_admin(admin_user_id=admin_user_id)
            email = doctor_email.lower()

            existing_user = await self.crud_user.get_by_email(email=email)
            if existing_user:
                logging.warning(f"Invitation blocked for existing user email {email}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists",
                )

            pending_invitation = await self.crud_invitation.get_pending_by_email(email=email)
            if pending_invitation and self._normalize_datetime(pending_invitation.expires_at) > self._utc_now():
                logging.warning(f"Pending invitation already exists for {email}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A pending invitation already exists for this email",
                )

            invitation = await self.crud_invitation.create(
                obj_in={
                    "doctor_email": email,
                    "token": self._generate_token(),
                    "status": InvitationStatus.PENDING,
                    "invited_by_admin_id": admin_user_id,
                    "expires_at": self._utc_now() + timedelta(hours=72),
                }
            )
            return self._serialize_document(invitation)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InvitationController.create_doctor_invitation: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_invitations(self) -> dict:
        """List doctor invitations for operational admin views.

        Returns:
            dict: Serialized invitation list payload.
        """

        try:
            logging.info("Executing InvitationController.list_invitations")
            invitations = await self.crud_invitation.get_many()
            return {"invitations": self._serialize_documents(invitations)}
        except Exception as error:
            logging.error(f"Error in InvitationController.list_invitations: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def resend_doctor_invitation(self, invitation_id: str, admin_user_id: str) -> dict:
        """Regenerate token and expiry for an invitation being resent.

        Args:
            invitation_id: Persisted invitation identifier.
            admin_user_id: Admin user resending the invitation.

        Returns:
            dict: Serialized updated invitation payload.

        Raises:
            HTTPException 404: Invitation record does not exist.
            HTTPException 403: Acting user is not an admin.
        """

        try:
            logging.info("Executing InvitationController.resend_doctor_invitation")
            await self._assert_admin(admin_user_id=admin_user_id)
            invitation = await self.crud_invitation.get_by_id(id=invitation_id)
            if invitation is None:
                logging.warning(f"Invitation not found for resend: {invitation_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invitation not found",
                )

            updated_invitation = await self.crud_invitation.update(
                id=invitation_id,
                obj_in={
                    "token": self._generate_token(),
                    "status": InvitationStatus.PENDING,
                    "expires_at": self._utc_now() + timedelta(hours=72),
                },
            )
            return self._serialize_document(updated_invitation)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InvitationController.resend_doctor_invitation: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def revoke_doctor_invitation(self, invitation_id: str, admin_user_id: str) -> dict:
        """Revoke a doctor invitation so it can no longer be used.

        Args:
            invitation_id: Persisted invitation identifier.
            admin_user_id: Admin user revoking the invitation.

        Returns:
            dict: Message payload confirming revocation.

        Raises:
            HTTPException 404: Invitation record does not exist.
            HTTPException 403: Acting user is not an admin.
        """

        try:
            logging.info("Executing InvitationController.revoke_doctor_invitation")
            await self._assert_admin(admin_user_id=admin_user_id)
            invitation = await self.crud_invitation.get_by_id(id=invitation_id)
            if invitation is None:
                logging.warning(f"Invitation not found for revoke: {invitation_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invitation not found",
                )

            await self.crud_invitation.update(
                id=invitation_id,
                obj_in={"status": InvitationStatus.REVOKED},
            )
            return {"message": "Doctor invitation revoked successfully"}
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InvitationController.revoke_doctor_invitation: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def validate_doctor_invitation(self, token: str) -> dict:
        """Validate a doctor invitation token before onboarding continues.

        Args:
            token: Invitation token received by the doctor.

        Returns:
            dict: Validation payload including token status and expiry.
        """

        try:
            logging.info("Executing InvitationController.validate_doctor_invitation")
            invitation = await self.crud_invitation.get_by_token(token=token)
            if invitation is None:
                logging.warning("Invitation validation failed because token was not found")
                return {"valid": False, "doctor_email": None, "expires_at": None, "status": None}

            current_status = invitation.status
            if self._normalize_datetime(invitation.expires_at) <= self._utc_now():
                current_status = InvitationStatus.EXPIRED
                if invitation.status == InvitationStatus.PENDING:
                    invitation = await self.crud_invitation.update(
                        id=str(invitation.id),
                        obj_in={"status": InvitationStatus.EXPIRED},
                    )

            return {
                "valid": current_status == InvitationStatus.PENDING,
                "doctor_email": invitation.doctor_email,
                "expires_at": invitation.expires_at,
                "status": current_status,
            }
        except Exception as error:
            logging.error(f"Error in InvitationController.validate_doctor_invitation: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def _assert_admin(self, admin_user_id: str) -> None:
        """Ensure the acting user exists and has the admin role.

        Args:
            admin_user_id: User identifier being checked.

        Raises:
            HTTPException 403: User is not allowed to manage invitations.
        """

        admin_user = await self.crud_user.get_by_id(id=admin_user_id)
        if admin_user is None or admin_user.role != UserRole.ADMIN:
            logging.warning(f"Invitation admin check failed for user {admin_user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can manage doctor invitations",
            )

    @staticmethod
    def _generate_token() -> str:
        """Generate a secure invitation token string.

        Returns:
            str: URL-safe token for doctor invitation links.
        """

        return secrets.token_urlsafe(32)
