"""Dashboard routes for the MedCare API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.commons.logger import logger
from backend.core.apis.routers.router_dependencies import (
    build_response,
    get_authenticated_user,
    require_roles,
)
from backend.core.apis.schemas.responses_schemas.dashboard_response_schema import (
    AdminDashboardResponse,
    DoctorDashboardResponse,
    PatientDashboardResponse,
)
from backend.core.controllers.dashboard_controller import DashboardController
from backend.core.models.user_model import UserRole

dashboard_router = APIRouter()
logging = logger(__name__)


@dashboard_router.get(
    "/v1/patient-dashboard",
    response_model=PatientDashboardResponse,
    tags=["Dashboards"],
)
async def get_patient_dashboard(
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Fetch the authenticated patient's dashboard payload.

    Args:
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        PatientDashboardResponse: Patient dashboard summary.
    """

    try:
        logging.info("Calling GET /v1/patient-dashboard endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.PATIENT})
        response = await DashboardController().get_patient_dashboard(
            patient_id=authenticated_user_details["id"]
        )
        return build_response(PatientDashboardResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in GET /v1/patient-dashboard endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in GET /v1/patient-dashboard endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@dashboard_router.get(
    "/v1/doctor-dashboard",
    response_model=DoctorDashboardResponse,
    tags=["Dashboards"],
)
async def get_doctor_dashboard(
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Fetch the authenticated doctor's dashboard payload.

    Args:
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        DoctorDashboardResponse: Doctor dashboard summary.
    """

    try:
        logging.info("Calling GET /v1/doctor-dashboard endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.DOCTOR})
        response = await DashboardController().get_doctor_dashboard(
            doctor_id=authenticated_user_details["id"]
        )
        return build_response(DoctorDashboardResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in GET /v1/doctor-dashboard endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in GET /v1/doctor-dashboard endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@dashboard_router.get(
    "/v1/admin-dashboard",
    response_model=AdminDashboardResponse,
    tags=["Dashboards"],
)
async def get_admin_dashboard(
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Fetch the authenticated admin dashboard payload.

    Args:
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        AdminDashboardResponse: Admin dashboard summary.
    """

    try:
        logging.info("Calling GET /v1/admin-dashboard endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.ADMIN})
        response = await DashboardController().get_admin_dashboard(
            admin_user_id=authenticated_user_details["id"]
        )
        return build_response(AdminDashboardResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in GET /v1/admin-dashboard endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in GET /v1/admin-dashboard endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
