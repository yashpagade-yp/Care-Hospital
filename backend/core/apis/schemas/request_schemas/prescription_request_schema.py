"""Prescription request schemas for the MedCare API layer."""

from pydantic import BaseModel, ConfigDict, Field


class CreatePrescriptionRequest(BaseModel):
    """Prescription creation payload used by doctors after consultation."""

    appointment_id: str = Field(..., description="Appointment linked to the prescription")
    medicines: list[str] = Field(
        default_factory=list,
        description="Structured list of medicines prescribed to the patient",
    )
    notes: str | None = Field(
        default=None,
        description="Additional consultation notes or medical instructions",
    )

    model_config = ConfigDict(extra="forbid")


class UpdatePrescriptionRequest(BaseModel):
    """Prescription update payload used by doctors when edits are allowed."""

    medicines: list[str] = Field(
        default_factory=list,
        description="Updated structured list of prescribed medicines",
    )
    notes: str | None = Field(
        default=None,
        description="Updated consultation notes or instructions",
    )

    model_config = ConfigDict(extra="forbid")

