"""Authentication response schemas for the MedCare API layer."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.core.models.user_model import OtpPurpose, UserRole
from backend.core.apis.schemas.responses_schemas.user_response_schema import UserSummaryResponse


class LoginResponse(BaseModel):
    """Shared login response payload."""

    access_token: str = Field(..., description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="Authentication token type")
    role: UserRole = Field(..., description="Role detected for the authenticated user")
    user: UserSummaryResponse = Field(..., description="Basic authenticated user details")

    model_config = ConfigDict(extra="forbid")


class OtpSentResponse(BaseModel):
    """OTP dispatch response payload."""

    message: str = Field(..., description="Human-readable OTP dispatch message")
    email: EmailStr = Field(..., description="Destination email that received the OTP")
    purpose: OtpPurpose = Field(..., description="Business purpose of the issued OTP")

    model_config = ConfigDict(extra="forbid")


class PasswordResetResponse(BaseModel):
    """Password reset progress response payload."""

    message: str = Field(..., description="Human-readable password reset result message")

    model_config = ConfigDict(extra="forbid")

