"""Doctor request schemas for the MedCare API layer."""

from datetime import time

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.core.models.DoctorAvailability import DayOfWeek


class DoctorWorkingSlotRequest(BaseModel):
    """Recurring working slot payload used during doctor profile setup."""

    day_of_week: DayOfWeek = Field(..., description="Working day for the recurring slot")
    start_time: time = Field(..., description="Start time for the recurring slot")
    end_time: time = Field(..., description="End time for the recurring slot")

    model_config = ConfigDict(extra="forbid")


class DoctorSetCredentialsRequest(BaseModel):
    """Doctor invitation credential setup payload."""

    token: str = Field(..., description="Invitation token received in the email link")
    email: EmailStr = Field(..., description="Doctor email tied to the invitation")
    password: str = Field(
        ...,
        min_length=8,
        description="Password chosen by the doctor during onboarding",
    )

    model_config = ConfigDict(extra="forbid")


class DoctorVerifyOtpRequest(BaseModel):
    """Doctor onboarding OTP verification payload."""

    email: EmailStr = Field(..., description="Doctor email address verifying the OTP")
    otp: str = Field(
        ...,
        min_length=4,
        max_length=8,
        description="OTP code sent to the invited doctor email",
    )

    model_config = ConfigDict(extra="forbid")


class DoctorCompleteProfileRequest(BaseModel):
    """Doctor one-time professional profile completion payload."""

    name: str = Field(..., min_length=2, description="Doctor full name")
    email: EmailStr = Field(..., description="Doctor email address from the invitation flow")
    qualification: str = Field(
        ...,
        min_length=2,
        description="Doctor academic or professional qualification",
    )
    specialty: str = Field(..., min_length=2, description="Doctor specialty or domain")
    experience_years: int = Field(
        ...,
        ge=0,
        description="Number of professional years of experience",
    )
    services: list[str] = Field(
        default_factory=list,
        description="Services offered by the doctor for patients",
    )
    working_slots: list[DoctorWorkingSlotRequest] = Field(
        default_factory=list,
        description="Initial recurring working slots defined during doctor onboarding",
    )

    model_config = ConfigDict(extra="forbid")

