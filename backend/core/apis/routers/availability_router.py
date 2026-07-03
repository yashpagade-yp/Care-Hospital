"""Doctor availability routes for the MedCare API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.commons.logger import logger
from backend.core.apis.routers.router_dependencies import (
    build_response,
    get_authenticated_user,
    require_roles,
)
from backend.core.apis.schemas.request_schemas.availability_request_schema import (
    AdminOverrideAvailabilityRequest,
    AvailabilityUpsertRequest,
    UpdateAvailabilityRequest,
)
from backend.core.apis.schemas.responses_schemas.availability_response_schema import (
    DoctorAvailabilityListResponse,
    DoctorAvailabilityResponse,
)
from backend.core.controllers.availability_controller import AvailabilityController
from backend.core.models.user_model import UserRole

availability_router = APIRouter()
logging = logger(__name__)


@availability_router.post(
    "/v1/doctors/availability",
    status_code=status.HTTP_201_CREATED,
    response_model=DoctorAvailabilityResponse,
    tags=["Availability"],
)
async def create_doctor_availability(
    request: AvailabilityUpsertRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Create a doctor availability entry for the authenticated doctor.

    Args:
        request: Availability creation payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        DoctorAvailabilityResponse: Created availability entry.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not a doctor.
        HTTPException 404: Doctor record does not exist.
        HTTPException 409: Duplicate availability entry exists.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/doctors/availability endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.DOCTOR})
        response = await AvailabilityController().create_doctor_availability(
            doctor_id=authenticated_user_details["id"],
            availability_data=request.model_dump(),
        )
        return build_response(DoctorAvailabilityResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/doctors/availability endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/doctors/availability endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@availability_router.delete(
    "/v1/doctors/availability/{availability_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Availability"],
)
async def delete_doctor_availability(
    availability_id: str,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Delete an availability entry owned by the authenticated doctor."""

    try:
        logging.info(f"Calling DELETE /v1/doctors/availability/{availability_id} endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.DOCTOR})
        deleted = await AvailabilityController().delete_doctor_availability(
            availability_id=availability_id,
            doctor_id=authenticated_user_details["id"],
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Availability entry not found",
            )
    except HTTPException as http_error:
        logging.error(
            f"Error in DELETE /v1/doctors/availability/{availability_id} endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in DELETE /v1/doctors/availability/{availability_id} endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@availability_router.patch(
    "/v1/doctors/availability/{availability_id}",
    response_model=DoctorAvailabilityResponse,
    tags=["Availability"],
)
async def update_doctor_availability(
    availability_id: str,
    request: UpdateAvailabilityRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Update an availability entry owned by the authenticated doctor.

    Args:
        availability_id: Availability record identifier.
        request: Availability partial update payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        DoctorAvailabilityResponse: Updated availability entry.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not a doctor or does not own the entry.
        HTTPException 404: Availability record does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling PATCH /v1/doctors/availability/{availability_id} endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.DOCTOR})
        response = await AvailabilityController().update_doctor_availability(
            availability_id=availability_id,
            doctor_id=authenticated_user_details["id"],
            update_data=request.model_dump(exclude_none=True),
        )
        return build_response(DoctorAvailabilityResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in PATCH /v1/doctors/availability/{availability_id} endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in PATCH /v1/doctors/availability/{availability_id} endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@availability_router.get(
    "/v1/doctors/{doctor_id}/availability",
    response_model=DoctorAvailabilityListResponse,
    tags=["Availability"],
)
async def list_doctor_availability(
    doctor_id: str,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """List availability entries for a requested doctor.

    Args:
        doctor_id: Doctor identifier referenced by the route.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        DoctorAvailabilityListResponse: Collection of availability entries.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 404: Doctor record does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling GET /v1/doctors/{doctor_id}/availability endpoint")
        require_roles(
            authenticated_user_details,
            allowed_roles={UserRole.ADMIN, UserRole.DOCTOR, UserRole.PATIENT},
        )
        response = await AvailabilityController().list_doctor_availability(
            doctor_id=doctor_id
        )
        return build_response(DoctorAvailabilityListResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in GET /v1/doctors/{doctor_id}/availability endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in GET /v1/doctors/{doctor_id}/availability endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@availability_router.post(
    "/v1/admin/availability/overrides",
    status_code=status.HTTP_201_CREATED,
    response_model=DoctorAvailabilityResponse,
    tags=["Availability"],
)
async def create_admin_override(
    request: AdminOverrideAvailabilityRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Create an admin availability override for a doctor.

    Args:
        request: Admin override payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        DoctorAvailabilityResponse: Created override entry.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not an admin.
        HTTPException 404: Doctor record does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/admin/availability/overrides endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.ADMIN})
        response = await AvailabilityController().create_admin_override(
            override_data=request.model_dump(),
            admin_user_id=authenticated_user_details["id"],
        )
        return build_response(DoctorAvailabilityResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in POST /v1/admin/availability/overrides endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in POST /v1/admin/availability/overrides endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
