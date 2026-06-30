"""Doctor invitation request schemas for the MedCare API layer."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateDoctorInvitationRequest(BaseModel):
    """Doctor invitation creation payload for admins."""

    doctor_email: EmailStr = Field(..., description="Email address of the invited doctor")

    model_config = ConfigDict(extra="forbid")


class ResendDoctorInvitationRequest(BaseModel):
    """Doctor invitation resend payload for admins."""

    invitation_id: str = Field(..., description="Unique identifier of the invitation")

    model_config = ConfigDict(extra="forbid")


class RevokeDoctorInvitationRequest(BaseModel):
    """Doctor invitation revoke payload for admins."""

    invitation_id: str = Field(..., description="Unique identifier of the invitation")

    model_config = ConfigDict(extra="forbid")


class ValidateDoctorInvitationRequest(BaseModel):
    """Invitation token validation payload used by doctors."""

    token: str = Field(..., description="Invitation token received in the doctor email")

    model_config = ConfigDict(extra="forbid")

