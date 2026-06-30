"""Payment controller logic for mock Phase 1 payment workflows."""

from __future__ import annotations

import secrets

from fastapi import HTTPException, status

from backend.commons.logger import logger
from backend.core.controllers.base_controller import BaseController
from backend.core.cruds.appointment_crud import CRUDAppointment
from backend.core.cruds.payment_crud import CRUDPayment

logging = logger(__name__)


class PaymentController(BaseController):
    """Controller for mock payment record creation and lookup."""

    def __init__(self):
        """Initialize CRUD dependencies used by payment workflows."""

        self.crud_payment = CRUDPayment()
        self.crud_appointment = CRUDAppointment()

    async def create_mock_payment(self, appointment_id: str, amount: float) -> dict:
        """Create a mock payment record for a confirmed appointment.

        Args:
            appointment_id: Appointment linked to the payment.
            amount: Amount being recorded for the mock payment.

        Returns:
            dict: Serialized payment payload.

        Raises:
            HTTPException 404: Appointment does not exist.
            HTTPException 409: Payment record already exists.
        """

        try:
            logging.info("Executing PaymentController.create_mock_payment")
            appointment = await self.crud_appointment.get_by_id(id=appointment_id)
            if appointment is None:
                logging.warning(f"Payment creation blocked for missing appointment {appointment_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Appointment not found",
                )

            existing_payment = await self.crud_payment.get_by_appointment_id(
                appointment_id=appointment_id
            )
            if existing_payment:
                logging.warning(f"Duplicate payment blocked for appointment {appointment_id}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Payment already exists for this appointment",
                )

            payment = await self.crud_payment.create(
                obj_in={
                    "appointment_id": appointment_id,
                    "amount": amount,
                    "transaction_ref": self._generate_transaction_ref(),
                }
            )
            return self._serialize_document(payment)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in PaymentController.create_mock_payment: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def get_payment_by_appointment(self, appointment_id: str) -> dict:
        """Fetch the payment record linked to an appointment.

        Args:
            appointment_id: Appointment identifier used for lookup.

        Returns:
            dict: Serialized payment payload.

        Raises:
            HTTPException 404: Payment record does not exist.
        """

        try:
            logging.info("Executing PaymentController.get_payment_by_appointment")
            payment = await self.crud_payment.get_by_appointment_id(appointment_id=appointment_id)
            if payment is None:
                logging.warning(f"Payment not found for appointment {appointment_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found",
                )

            return self._serialize_document(payment)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in PaymentController.get_payment_by_appointment: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    @staticmethod
    def _generate_transaction_ref() -> str:
        """Generate a mock payment transaction reference.

        Returns:
            str: Human-readable transaction reference string.
        """

        return f"MOCK-{secrets.token_hex(8).upper()}"
