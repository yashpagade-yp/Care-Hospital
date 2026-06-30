"""Persistence operations for payment records."""

from __future__ import annotations

from backend.commons.logger import logger
from backend.core.cruds.base_crud import BaseCRUD
from backend.core.models.Payment import Payment

logging = logger(__name__)


class CRUDPayment(BaseCRUD[Payment]):
    """Database access layer for payment records."""

    def __init__(self):
        """Initialize the payment CRUD helper."""

        super().__init__(Payment)

    async def get_by_appointment_id(self, *, appointment_id: str) -> Payment | None:
        """Read the payment record linked to an appointment.

        Args:
            appointment_id: Appointment identifier linked to the payment.

        Returns:
            Payment | None: Matching payment record when present.
        """

        logging.info("Executing CRUDPayment.get_by_appointment_id")
        return await self.get_one(Payment.appointment_id == appointment_id)

    async def get_by_transaction_ref(self, *, transaction_ref: str) -> Payment | None:
        """Read a payment by transaction reference.

        Args:
            transaction_ref: Mock payment transaction reference.

        Returns:
            Payment | None: Matching payment record when present.
        """

        logging.info("Executing CRUDPayment.get_by_transaction_ref")
        return await self.get_one(Payment.transaction_ref == transaction_ref)
