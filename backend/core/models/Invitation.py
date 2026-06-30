"""Doctor invitation persistence model for the MedCare platform.

This model stores invite records used by admins to onboard doctors through
secure, time-bound invitation links.
"""

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import EmailStr


class InvitationStatus(str, Enum):
    """Defines the supported lifecycle states for doctor invitations.

    These states help the system track whether an invitation can still be used
    during doctor onboarding.
    """

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class DoctorInvitation(Model):
    """Represents an admin-issued doctor invitation stored in the database.

    Each invitation is tied to a doctor email, contains a unique secure token,
    and expires after a configured time window.
    """

    doctor_email: EmailStr = Field(
        ...,
        description="Doctor email address to which the invitation is sent",
    )
    token: str = Field(
        ...,
        unique=True,
        description="Unique secure token embedded in the invitation link",
    )
    status: InvitationStatus = Field(
        default=InvitationStatus.PENDING,
        description="Current state of the doctor invitation",
    )
    invited_by_admin_id: str = Field(
        ...,
        description="Identifier of the admin user who created the invitation",
    )
    expires_at: datetime = Field(
        ...,
        description="UTC timestamp when the invitation becomes invalid",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the invitation record was created",
    )

    model_config = {
        "collection": "doctor_invitations",
        "extra": "forbid",
    }
