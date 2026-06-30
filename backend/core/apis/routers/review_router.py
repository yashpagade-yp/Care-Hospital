"""Review submission and moderation routes for the MedCare API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.commons.logger import logger
from backend.core.apis.routers.router_dependencies import (
    build_response,
    get_authenticated_user,
    require_roles,
)
from backend.core.apis.schemas.request_schemas.review_request_schema import (
    CreateReviewRequest,
    HideReviewRequest,
)
from backend.core.apis.schemas.responses_schemas.review_response_schema import (
    ReviewListResponse,
    ReviewResponse,
)
from backend.core.controllers.review_controller import ReviewController
from backend.core.models.user_model import UserRole

review_router = APIRouter()
logging = logger(__name__)


@review_router.post(
    "/v1/patients/reviews",
    status_code=status.HTTP_201_CREATED,
    response_model=ReviewResponse,
    tags=["Reviews"],
)
async def create_review(
    request: CreateReviewRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Create a review as the authenticated patient.

    Args:
        request: Review creation payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        ReviewResponse: Created review details.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not a patient.
        HTTPException 404: Appointment does not exist.
        HTTPException 409: Review already exists for the appointment.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/patients/reviews endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.PATIENT})
        response = await ReviewController().create_review(
            patient_id=authenticated_user_details["id"],
            review_data=request.model_dump(),
        )
        return build_response(ReviewResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/patients/reviews endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/patients/reviews endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@review_router.patch(
    "/v1/admin/reviews/{review_id}/visibility",
    response_model=ReviewResponse,
    tags=["Reviews"],
)
async def set_review_visibility(
    review_id: str,
    request: HideReviewRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Hide or unhide a review as an authenticated admin.

    Args:
        review_id: Review record identifier.
        request: Review visibility payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        ReviewResponse: Updated review details.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not an admin.
        HTTPException 404: Review does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling PATCH /v1/admin/reviews/{review_id}/visibility endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.ADMIN})
        response = await ReviewController().set_review_visibility(
            review_id=review_id,
            is_hidden=request.is_hidden,
            admin_user_id=authenticated_user_details["id"],
        )
        return build_response(ReviewResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in PATCH /v1/admin/reviews/{review_id}/visibility endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in PATCH /v1/admin/reviews/{review_id}/visibility endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@review_router.get(
    "/v1/doctors/{doctor_id}/reviews",
    response_model=ReviewListResponse,
    tags=["Reviews"],
)
async def list_doctor_reviews(doctor_id: str):
    """List visible reviews for a doctor.

    Args:
        doctor_id: Doctor identifier referenced by the route.

    Returns:
        ReviewListResponse: Public-facing visible reviews for the doctor.

    Raises:
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling GET /v1/doctors/{doctor_id}/reviews endpoint")
        response = await ReviewController().list_doctor_reviews(
            doctor_id=doctor_id,
            include_hidden=False,
        )
        return build_response(ReviewListResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in GET /v1/doctors/{doctor_id}/reviews endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in GET /v1/doctors/{doctor_id}/reviews endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@review_router.get(
    "/v1/admin/doctors/{doctor_id}/reviews",
    response_model=ReviewListResponse,
    tags=["Reviews"],
)
async def list_doctor_reviews_for_admin(
    doctor_id: str,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """List all reviews for a doctor, including hidden ones, as an admin.

    Args:
        doctor_id: Doctor identifier referenced by the route.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        ReviewListResponse: Collection of doctor reviews including moderated ones.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not an admin.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling GET /v1/admin/doctors/{doctor_id}/reviews endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.ADMIN})
        response = await ReviewController().list_doctor_reviews(
            doctor_id=doctor_id,
            include_hidden=True,
        )
        return build_response(ReviewListResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in GET /v1/admin/doctors/{doctor_id}/reviews endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in GET /v1/admin/doctors/{doctor_id}/reviews endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
