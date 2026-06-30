"""Payment response schemas for the MedCare API layer."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.core.models.Payment import PaymentMethod, PaymentRecordStatus


class PaymentResponse(BaseModel):
    """Payment detail response payload."""

    id: str = Field(..., description="Unique identifier of the payment record")
    appointment_id: str = Field(..., description="Appointment linked to the payment")
    amount: float = Field(..., ge=0, description="Amount charged for the appointment")
    status: PaymentRecordStatus = Field(..., description="Mock payment result status")
    method: PaymentMethod = Field(..., description="Payment method used for the transaction")
    transaction_ref: str = Field(..., description="Generated transaction reference")
    created_at: datetime = Field(..., description="UTC timestamp when the payment was created")

    model_config = ConfigDict(from_attributes=True, extra="forbid")

