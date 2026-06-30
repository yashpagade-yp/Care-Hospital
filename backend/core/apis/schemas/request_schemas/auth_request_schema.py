"""Authentication request schemas for the MedCare API layer."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.core.models.user_model import OtpPurpose


class LoginRequest(BaseModel):
    """Shared login payload for admin, doctor, and patient users."""

    email: EmailStr = Field(..., description="User email address used for login")
    password: str = Field(
        ...,
        min_length=8,
        description="Plain-text password submitted for authentication",
    )

    model_config = ConfigDict(extra="forbid")


class ResendOtpRequest(BaseModel):
    """OTP resend payload for registration and password reset flows."""

    email: EmailStr = Field(..., description="Email address that should receive the OTP")
    purpose: OtpPurpose = Field(..., description="Business purpose for the OTP resend")

    model_config = ConfigDict(extra="forbid")


class ForgotPasswordRequest(BaseModel):
    """Forgot-password payload that starts the password reset flow."""

    email: EmailStr = Field(..., description="Email address requesting password reset")

    model_config = ConfigDict(extra="forbid")


class VerifyPasswordResetOtpRequest(BaseModel):
    """OTP verification payload for password reset validation."""

    email: EmailStr = Field(..., description="Email address verifying the reset OTP")
    otp: str = Field(
        ...,
        min_length=4,
        max_length=8,
        description="OTP code sent to the user's email address",
    )

    model_config = ConfigDict(extra="forbid")


class ResetPasswordRequest(BaseModel):
    """Final password reset payload after OTP verification."""

    email: EmailStr = Field(..., description="Email address resetting its password")
    otp: str = Field(
        ...,
        min_length=4,
        max_length=8,
        description="Verified OTP code used to authorize password reset",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        description="New plain-text password to persist after validation",
    )

    model_config = ConfigDict(extra="forbid")

