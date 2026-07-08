"""Doctor invitation response schemas for the MedCare API layer."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.core.models.Invitation import InvitationStatus


class DoctorInvitationResponse(BaseModel):
    """Doctor invitation detail response payload."""

    id: str = Field(..., description="Unique identifier of the invitation")
    doctor_email: EmailStr = Field(..., description="Invited doctor email address")
    status: InvitationStatus = Field(..., description="Current invitation lifecycle state")
    expires_at: datetime = Field(..., description="UTC timestamp when the invitation expires")
    created_at: datetime = Field(..., description="UTC timestamp when the invitation was created")

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class DoctorInvitationListResponse(BaseModel):
    """Doctor invitation list response payload."""

    invitations: list[DoctorInvitationResponse] = Field(
        default_factory=list,
        description="Collection of doctor invitation records",
    )

    model_config = ConfigDict(extra="forbid")


class ValidateDoctorInvitationResponse(BaseModel):
    """Invitation token validation response payload."""

    valid: bool = Field(..., description="Whether the invitation token is currently valid")
    doctor_email: EmailStr | None = Field(
        default=None,
        description="Doctor email linked to the invitation when valid",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the invitation expires",
    )
    status: InvitationStatus | None = Field(
        default=None,
        description="Current invitation status for the validated token",
    )

    model_config = ConfigDict(extra="forbid")

