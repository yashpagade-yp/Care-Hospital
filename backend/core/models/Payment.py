"""Payment persistence model for the MedCare platform.

This model stores mock payment records linked to appointments during Phase 1.
"""

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model


class PaymentRecordStatus(str, Enum):
    """Defines the supported payment record states."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, Enum):
    """Defines the supported payment methods for Phase 1."""

    MOCK = "MOCK"


class Payment(Model):
    """Represents a payment transaction linked to an appointment.

    The model stores the mock payment result and generated transaction
    reference for Phase 1 booking flows.
    """

    appointment_id: str = Field(..., description="Identifier of the linked appointment")
    amount: float = Field(..., ge=0, description="Amount paid for the appointment")
    status: PaymentRecordStatus = Field(
        default=PaymentRecordStatus.SUCCESS,
        description="Outcome of the mock payment transaction",
    )
    method: PaymentMethod = Field(
        default=PaymentMethod.MOCK,
        description="Payment method used for the transaction",
    )
    transaction_ref: str = Field(
        ...,
        description="Generated transaction reference for the mock payment",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the payment record was created",
    )

    model_config = {
        "collection": "payments",
        "extra": "forbid",
    }
