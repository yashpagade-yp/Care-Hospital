"""Payment request schemas for the MedCare API layer."""

from pydantic import BaseModel, ConfigDict, Field


class CreateMockPaymentRequest(BaseModel):
    """Mock payment creation payload for operational or internal flows."""

    appointment_id: str = Field(..., description="Appointment linked to the payment")
    amount: float = Field(..., ge=0, description="Amount recorded for the mock payment")

    model_config = ConfigDict(extra="forbid")
