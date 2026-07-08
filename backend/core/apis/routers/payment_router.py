"""Payment routes for the MedCare API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.commons.logger import logger
from backend.core.apis.routers.router_dependencies import (
    build_response,
    get_authenticated_user,
    require_roles,
)
from backend.core.apis.schemas.request_schemas.payment_request_schema import (
    CreateMockPaymentRequest,
)
from backend.core.apis.schemas.responses_schemas.payment_response_schema import (
    PaymentResponse,
)
from backend.core.controllers.payment_controller import PaymentController
from backend.core.models.user_model import UserRole

payment_router = APIRouter()
logging = logger(__name__)


@payment_router.post(
    "/v1/admin/payments/mock",
    status_code=status.HTTP_201_CREATED,
    response_model=PaymentResponse,
    tags=["Payments"],
)
async def create_mock_payment(
    request: CreateMockPaymentRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Create a mock payment record for admin or internal operational use.

    Args:
        request: Mock payment creation payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        PaymentResponse: Created payment details.
    """

    try:
        logging.info("Calling POST /v1/admin/payments/mock endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.ADMIN})
        response = await PaymentController().create_mock_payment(
            appointment_id=request.appointment_id,
            amount=request.amount,
        )
        return build_response(PaymentResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/admin/payments/mock endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/admin/payments/mock endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@payment_router.get(
    "/v1/admin/appointments/{appointment_id}/payment",
    response_model=PaymentResponse,
    tags=["Payments"],
)
async def get_payment_by_appointment(
    appointment_id: str,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Fetch payment details for an appointment from admin views.

    Args:
        appointment_id: Appointment identifier linked to the payment.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        PaymentResponse: Payment details linked to the appointment.
    """

    try:
        logging.info(f"Calling GET /v1/admin/appointments/{appointment_id}/payment endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.ADMIN})
        response = await PaymentController().get_payment_by_appointment(
            appointment_id=appointment_id
        )
        return build_response(PaymentResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in GET /v1/admin/appointments/{appointment_id}/payment endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in GET /v1/admin/appointments/{appointment_id}/payment endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
