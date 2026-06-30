"""Persistence operations for doctor invitation records."""

from __future__ import annotations

from odmantic.query import desc

from backend.commons.logger import logger
from backend.core.cruds.base_crud import BaseCRUD
from backend.core.models.Invitation import DoctorInvitation, InvitationStatus

logging = logger(__name__)


class CRUDDoctorInvitation(BaseCRUD[DoctorInvitation]):
    """Database access layer for doctor invitation records."""

    def __init__(self):
        """Initialize the doctor invitation CRUD helper."""

        super().__init__(DoctorInvitation)

    async def get_by_email(self, *, email: str) -> list[DoctorInvitation]:
        """Read invitation records for a doctor email address.

        Args:
            email: Doctor email tied to invitation records.

        Returns:
            list[DoctorInvitation]: Matching invitation records.
        """

        logging.info("Executing CRUDDoctorInvitation.get_by_email")
        return await self.get_many(
            DoctorInvitation.doctor_email == email,
            sort=desc(DoctorInvitation.created_at),
        )

    async def get_by_token(self, *, token: str) -> DoctorInvitation | None:
        """Read a doctor invitation by secure invitation token.

        Args:
            token: Unique invitation token from the onboarding link.

        Returns:
            DoctorInvitation | None: Matching invitation record when present.
        """

        logging.info("Executing CRUDDoctorInvitation.get_by_token")
        return await self.get_one(DoctorInvitation.token == token)

    async def get_pending_by_email(self, *, email: str) -> DoctorInvitation | None:
        """Read the latest pending invitation for a doctor email.

        Args:
            email: Doctor email tied to invitation records.

        Returns:
            DoctorInvitation | None: Pending invitation if one exists.
        """

        logging.info("Executing CRUDDoctorInvitation.get_pending_by_email")
        invitations = await self.get_many(
            DoctorInvitation.doctor_email == email,
            DoctorInvitation.status == InvitationStatus.PENDING,
            sort=desc(DoctorInvitation.created_at),
            limit=1,
        )
        return invitations[0] if invitations else None
