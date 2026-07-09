"""User and profile response schemas for the MedCare API layer."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.core.models.user_model import DoctorStatus, UserRole


class UserSummaryResponse(BaseModel):
    """Shared compact user response payload."""

    id: str = Field(..., description="Unique identifier of the user")
    name: str = Field(..., description="Full name of the user")
    email: EmailStr = Field(..., description="Email address of the user")
    phone: str | None = Field(default=None, description="Primary phone number of the user")
    role: UserRole = Field(..., description="Role assigned to the user account")
    created_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the user record was created",
    )

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class PatientProfileResponse(UserSummaryResponse):
    """Patient profile response payload."""

    dob: date | None = Field(default=None, description="Date of birth of the patient")

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class DoctorProfileResponse(UserSummaryResponse):
    """Doctor profile response payload."""

    qualification: str | None = Field(
        default=None,
        description="Professional qualification of the doctor",
    )
    specialty: str | None = Field(default=None, description="Specialty of the doctor")
    experience_years: int | None = Field(
        default=None,
        description="Years of experience for the doctor",
    )
    services: list[str] = Field(
        default_factory=list,
        description="Services offered by the doctor",
    )
    doctor_status: DoctorStatus | None = Field(
        default=None,
        description="Post-registration lifecycle status of the doctor",
    )

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AdminProfileResponse(UserSummaryResponse):
    """Admin profile response payload."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class DoctorListResponse(BaseModel):
    """Doctor list response payload."""

    items: list[DoctorProfileResponse] = Field(
        default_factory=list,
        description="Collection of doctor profile records",
    )

    model_config = ConfigDict(extra="forbid")


class PublicDoctorProfileResponse(BaseModel):
    """Public-safe doctor profile response payload."""

    id: str = Field(..., description="Unique identifier of the doctor")
    name: str = Field(..., description="Display name of the doctor")
    qualification: str | None = Field(
        default=None,
        description="Professional qualification of the doctor",
    )
    specialty: str | None = Field(default=None, description="Specialty of the doctor")
    experience_years: int | None = Field(
        default=None,
        description="Years of experience for the doctor",
    )
    services: list[str] = Field(
        default_factory=list,
        description="Public-facing services offered by the doctor",
    )
    doctor_status: DoctorStatus | None = Field(
        default=None,
        description="Doctor lifecycle status visible to the public",
    )

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class PublicDoctorListResponse(BaseModel):
    """Public-safe doctor list response payload."""

    items: list[PublicDoctorProfileResponse] = Field(
        default_factory=list,
        description="Collection of public doctor profile records",
    )

    model_config = ConfigDict(extra="forbid")


class PatientListResponse(BaseModel):
    """Patient list response payload."""

    items: list[PatientProfileResponse] = Field(
        default_factory=list,
        description="Collection of patient profile records",
    )

    model_config = ConfigDict(extra="forbid")

