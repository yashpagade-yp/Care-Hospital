"""User-related persistence models for the MedCare platform.

These models define the shared user identity shape and embedded OTP state used
across Phase 1 authentication, onboarding, and role-based access flows.
"""

from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from odmantic import Field, Model
from pydantic import BaseModel, ConfigDict, EmailStr


class UserRole(str, Enum):
    """Defines the supported user roles.

    These values drive shared login redirection and role-based access control.
    """

    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"


class DoctorStatus(str, Enum):
    """Defines the onboarding and activation states for doctors.

    This status is stored only after a doctor user account exists and remains
    null for non-doctor roles. Invitation lifecycle is tracked separately in
    the DoctorInvitation model.
    """

    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class OtpPurpose(str, Enum):
    """Defines the supported OTP verification use cases.

    These values identify why the OTP was issued during authentication flows.
    """

    DOCTOR_INVITE_VERIFY = "DOCTOR_INVITE_VERIFY"
    PATIENT_REGISTER_VERIFY = "PATIENT_REGISTER_VERIFY"
    PASSWORD_RESET_VERIFY = "PASSWORD_RESET_VERIFY"


class UserOtp(BaseModel):
    """Represents active OTP verification state stored on a user record.

    The embedded structure keeps temporary OTP data with the related account so
    a separate OTP collection is not required.
    """

    otp_code: str = Field(..., description="Issued OTP code or hashed OTP value")
    purpose: OtpPurpose = Field(
        ..., description="Business purpose for which the OTP was generated"
    )
    expires_at: datetime = Field(..., description="UTC timestamp when the OTP expires")
    verified_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when the OTP was successfully verified",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the OTP state was created",
    )

    model_config = ConfigDict(extra="forbid")


class User(Model):
    """Represents a shared user account stored in the users collection.

    The model stores common identity, authentication, and role fields for
    patients, doctors, and admins. Doctor-specific profile fields are kept in
    this model for Phase 1 simplicity and remain nullable for non-doctor roles.
    """

    name: str = Field(..., description="Full name of the user")
    email: EmailStr = Field(
        ...,
        unique=True,
        description="Globally unique email address used for login",
    )
    phone: Optional[str] = Field(
        default=None,
        description="Primary contact number of the user when collected for the role",
    )
    dob: Optional[date] = Field(
        default=None,
        description="Date of birth captured for patient accounts",
    )
    password_hash: str = Field(
        ...,
        description="Hashed password used for local authentication",
    )
    role: UserRole = Field(..., description="Role assigned to the user account")
    is_otp_verified: bool = Field(
        default=False,
        description="Indicates whether the user's email has been OTP verified",
    )
    otp: Optional[UserOtp] = Field(
        default=None,
        description="Embedded OTP verification state for registration or onboarding",
    )
    specialty: Optional[str] = Field(
        default=None,
        description="Doctor specialty locked after first profile submission",
    )
    qualification: Optional[str] = Field(
        default=None,
        description="Doctor qualification locked after first profile submission",
    )
    experience_years: Optional[int] = Field(
        default=None,
        ge=0,
        description="Doctor years of experience locked after first submission",
    )
    services: Optional[list[str]] = Field(
        default=None,
        description="Services offered by the doctor and locked after setup",
    )
    doctor_status: Optional[DoctorStatus] = Field(
        default=None,
        description="Post-registration lifecycle status used only for doctor accounts",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the user record was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the user record was last updated",
    )

    model_config = {
        "collection": "users",
        "extra": "forbid",
    }
