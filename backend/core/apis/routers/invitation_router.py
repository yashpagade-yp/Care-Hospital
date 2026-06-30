"""Doctor invitation routes for the MedCare API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.commons.logger import logger
from backend.core.apis.routers.router_dependencies import (
    build_response,
    get_authenticated_user,
    require_roles,
)
from backend.core.apis.schemas.request_schemas.invitation_request_schema import (
    CreateDoctorInvitationRequest,
    ResendDoctorInvitationRequest,
    RevokeDoctorInvitationRequest,
    ValidateDoctorInvitationRequest,
)
from backend.core.apis.schemas.responses_schemas.common_response_schema import MessageResponse
from backend.core.apis.schemas.responses_schemas.invitation_response_schema import (
    DoctorInvitationListResponse,
    DoctorInvitationResponse,
    ValidateDoctorInvitationResponse,
)
from backend.core.controllers.invitation_controller import InvitationController
from backend.core.models.user_model import UserRole

invitation_router = APIRouter()
logging = logger(__name__)


@invitation_router.post(
    "/v1/admin/invitations",
    status_code=status.HTTP_201_CREATED,
    response_model=DoctorInvitationResponse,
    tags=["Invitations"],
)
async def create_doctor_invitation(
    request: CreateDoctorInvitationRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Create a doctor invitation as an authenticated admin.

    Args:
        request: Doctor invitation creation payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        DoctorInvitationResponse: Created invitation details.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not an admin.
        HTTPException 409: Pending invitation or user already exists.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/admin/invitations endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.ADMIN})
        response = await InvitationController().create_doctor_invitation(
            doctor_email=request.doctor_email,
            admin_user_id=authenticated_user_details["id"],
        )
        return build_response(DoctorInvitationResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/admin/invitations endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/admin/invitations endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@invitation_router.get(
    "/v1/admin/invitations",
    response_model=DoctorInvitationListResponse,
    tags=["Invitations"],
)
async def list_invitations(
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """List doctor invitations for admins.

    Args:
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        DoctorInvitationListResponse: Collection of doctor invitation records.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not an admin.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling GET /v1/admin/invitations endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.ADMIN})
        response = await InvitationController().list_invitations()
        return build_response(DoctorInvitationListResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in GET /v1/admin/invitations endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in GET /v1/admin/invitations endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@invitation_router.post(
    "/v1/admin/invitations/resend",
    response_model=DoctorInvitationResponse,
    tags=["Invitations"],
)
async def resend_doctor_invitation(
    request: ResendDoctorInvitationRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Resend a doctor invitation as an authenticated admin.

    Args:
        request: Invitation resend payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        DoctorInvitationResponse: Updated invitation details.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not an admin.
        HTTPException 404: Invitation record does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/admin/invitations/resend endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.ADMIN})
        response = await InvitationController().resend_doctor_invitation(
            invitation_id=request.invitation_id,
            admin_user_id=authenticated_user_details["id"],
        )
        return build_response(DoctorInvitationResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/admin/invitations/resend endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/admin/invitations/resend endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@invitation_router.post(
    "/v1/admin/invitations/revoke",
    response_model=MessageResponse,
    tags=["Invitations"],
)
async def revoke_doctor_invitation(
    request: RevokeDoctorInvitationRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Revoke a doctor invitation as an authenticated admin.

    Args:
        request: Invitation revoke payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        MessageResponse: Human-readable revocation confirmation.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not an admin.
        HTTPException 404: Invitation record does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/admin/invitations/revoke endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.ADMIN})
        response = await InvitationController().revoke_doctor_invitation(
            invitation_id=request.invitation_id,
            admin_user_id=authenticated_user_details["id"],
        )
        return build_response(MessageResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/admin/invitations/revoke endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/admin/invitations/revoke endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@invitation_router.post(
    "/v1/invitations/validate",
    response_model=ValidateDoctorInvitationResponse,
    tags=["Invitations"],
)
async def validate_doctor_invitation(request: ValidateDoctorInvitationRequest):
    """Validate a doctor invitation token before onboarding continues.

    Args:
        request: Invitation token validation payload.

    Returns:
        ValidateDoctorInvitationResponse: Token validity details.

    Raises:
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/invitations/validate endpoint")
        response = await InvitationController().validate_doctor_invitation(
            token=request.token
        )
        return build_response(ValidateDoctorInvitationResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/invitations/validate endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/invitations/validate endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
