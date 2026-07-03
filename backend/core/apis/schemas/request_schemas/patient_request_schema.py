"""Patient request schemas for the MedCare API layer."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PatientRegisterRequest(BaseModel):
    """Patient self-registration payload."""

    name: str = Field(..., min_length=2, description="Full name of the patient")
    phone: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="Primary phone number of the patient",
    )
    email: EmailStr = Field(..., description="Unique email address for the patient")
    password: str = Field(
        ...,
        min_length=8,
        description="Plain-text password chosen by the patient",
    )

    model_config = ConfigDict(extra="ignore")


class PatientVerifyOtpRequest(BaseModel):
    """Patient email OTP verification payload."""

    email: EmailStr = Field(..., description="Email address that received the OTP")
    otp: str = Field(
        ...,
        min_length=4,
        max_length=8,
        description="OTP code sent for patient email verification",
    )

    model_config = ConfigDict(extra="forbid")

