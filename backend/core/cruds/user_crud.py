"""Persistence operations for shared user records."""

from __future__ import annotations

from odmantic.query import desc

from backend.commons.logger import logger
from backend.core.cruds.base_crud import BaseCRUD
from backend.core.models.user_model import User, UserRole

logging = logger(__name__)


class CRUDUser(BaseCRUD[User]):
    """Database access layer for shared user account records."""

    def __init__(self):
        """Initialize the user CRUD helper."""

        super().__init__(User)

    async def get_by_email(self, *, email: str) -> User | None:
        """Read a user account by unique email address.

        Args:
            email: User email address used for login and duplicate checks.

        Returns:
            User | None: Matching user record, if present.
        """

        logging.info("Executing CRUDUser.get_by_email")
        return await self.get_one(User.email == email)

    async def get_doctors(self) -> list[User]:
        """Read all doctor accounts from the users collection.

        Returns:
            list[User]: Doctor user records ordered by creation time.
        """

        logging.info("Executing CRUDUser.get_doctors")
        return await self.get_many(
            User.role == UserRole.DOCTOR,
            sort=desc(User.created_at),
        )

    async def get_patients(self) -> list[User]:
        """Read all patient accounts from the users collection.

        Returns:
            list[User]: Patient user records ordered by creation time.
        """

        logging.info("Executing CRUDUser.get_patients")
        return await self.get_many(
            User.role == UserRole.PATIENT,
            sort=desc(User.created_at),
        )

    async def get_admins(self) -> list[User]:
        """Read all admin accounts from the users collection.

        Returns:
            list[User]: Admin user records ordered by creation time.
        """

        logging.info("Executing CRUDUser.get_admins")
        return await self.get_many(
            User.role == UserRole.ADMIN,
            sort=desc(User.created_at),
        )
