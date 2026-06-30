"""Dashboard response schemas for the MedCare API layer."""

from pydantic import BaseModel, ConfigDict, Field

from backend.core.apis.schemas.responses_schemas.appointment_response_schema import (
    AppointmentListItemResponse,
)
from backend.core.apis.schemas.responses_schemas.invitation_response_schema import (
    DoctorInvitationResponse,
)
from backend.core.apis.schemas.responses_schemas.review_response_schema import ReviewResponse
from backend.core.apis.schemas.responses_schemas.user_response_schema import (
    AdminProfileResponse,
    DoctorProfileResponse,
    PatientProfileResponse,
)


class DoctorCardResponse(BaseModel):
    """Patient-facing doctor card response payload."""

    doctor_id: str = Field(..., description="Unique identifier of the doctor")
    name: str = Field(..., description="Doctor display name")
    specialty: str | None = Field(default=None, description="Doctor specialty")
    experience_years: int | None = Field(
        default=None,
        description="Years of experience shown on the doctor card",
    )
    rating: float | None = Field(
        default=None,
        ge=0,
        le=5,
        description="Average doctor rating displayed to patients",
    )

    model_config = ConfigDict(extra="forbid")


class PatientDashboardResponse(BaseModel):
    """Patient dashboard response payload."""

    profile: PatientProfileResponse = Field(..., description="Patient profile summary")
    doctor_cards: list[DoctorCardResponse] = Field(
        default_factory=list,
        description="Patient-facing doctor discovery cards",
    )
    upcoming_appointments: list[AppointmentListItemResponse] = Field(
        default_factory=list,
        description="Patient upcoming appointments",
    )
    appointment_history: list[AppointmentListItemResponse] = Field(
        default_factory=list,
        description="Patient historical appointments",
    )

    model_config = ConfigDict(extra="forbid")


class DoctorDashboardResponse(BaseModel):
    """Doctor dashboard response payload."""

    profile: DoctorProfileResponse = Field(..., description="Doctor profile summary")
    upcoming_appointments: list[AppointmentListItemResponse] = Field(
        default_factory=list,
        description="Doctor upcoming appointments",
    )
    appointment_history: list[AppointmentListItemResponse] = Field(
        default_factory=list,
        description="Doctor historical appointments",
    )

    model_config = ConfigDict(extra="forbid")


class AdminDashboardResponse(BaseModel):
    """Admin dashboard response payload."""

    profile: AdminProfileResponse = Field(..., description="Admin profile summary")
    doctor_count: int = Field(..., ge=0, description="Total number of doctors in the system")
    invitation_count: int = Field(
        ...,
        ge=0,
        description="Total number of tracked doctor invitations",
    )
    appointment_count: int = Field(
        ...,
        ge=0,
        description="Total number of appointments in the system",
    )
    recent_invitations: list[DoctorInvitationResponse] = Field(
        default_factory=list,
        description="Recent invitation records for quick admin review",
    )
    recent_appointments: list[AppointmentListItemResponse] = Field(
        default_factory=list,
        description="Recent appointment records for operational oversight",
    )
    flagged_reviews: list[ReviewResponse] = Field(
        default_factory=list,
        description="Moderated or flagged reviews surfaced to admin",
    )

    model_config = ConfigDict(extra="forbid")
