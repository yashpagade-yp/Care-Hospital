"""User, patient, and doctor onboarding routes for the MedCare API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.commons.logger import logger
from backend.core.apis.routers.router_dependencies import (
    build_response,
    get_authenticated_user,
    require_roles,
    require_self_or_roles,
)
from backend.core.apis.schemas.request_schemas.doctor_request_schema import (
    DoctorCompleteProfileRequest,
    DoctorSetCredentialsRequest,
    DoctorVerifyOtpRequest,
)
from backend.core.apis.schemas.request_schemas.patient_request_schema import (
    PatientRegisterRequest,
    PatientVerifyOtpRequest,
)
from backend.core.apis.schemas.responses_schemas.user_response_schema import (
    AdminProfileResponse,
    DoctorListResponse,
    DoctorProfileResponse,
    PatientListResponse,
    PatientProfileResponse,
)
from backend.core.controllers.user_controller import UserController
from backend.core.models.user_model import UserRole

user_router = APIRouter()
logging = logger(__name__)


@user_router.post(
    "/v1/patients/register",
    status_code=status.HTTP_201_CREATED,
    response_model=PatientProfileResponse,
    tags=["Patients"],
)
async def register_patient(request: PatientRegisterRequest):
    """Register a new patient account and issue the registration OTP.

    Args:
        request: Patient registration payload.

    Returns:
        PatientProfileResponse: Newly created patient profile summary.

    Raises:
        HTTPException 409: Patient email already exists.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/patients/register endpoint")
        response = await UserController().register_patient(patient_data=request.model_dump())
        return build_response(PatientProfileResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/patients/register endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/patients/register endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@user_router.post(
    "/v1/patients/verify-otp",
    response_model=PatientProfileResponse,
    tags=["Patients"],
)
async def verify_patient_otp(request: PatientVerifyOtpRequest):
    """Verify the OTP issued during patient registration.

    Args:
        request: Patient OTP verification payload.

    Returns:
        PatientProfileResponse: Verified patient profile summary.

    Raises:
        HTTPException 400: OTP is invalid or expired.
        HTTPException 404: Patient account does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/patients/verify-otp endpoint")
        response = await UserController().verify_patient_otp(
            email=request.email,
            otp=request.otp,
        )
        return build_response(PatientProfileResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/patients/verify-otp endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/patients/verify-otp endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@user_router.post(
    "/v1/doctors/set-credentials",
    status_code=status.HTTP_201_CREATED,
    response_model=DoctorProfileResponse,
    tags=["Doctors"],
)
async def set_doctor_credentials(request: DoctorSetCredentialsRequest):
    """Create the doctor account after invitation validation.

    Args:
        request: Doctor credential setup payload.

    Returns:
        DoctorProfileResponse: Created doctor account summary.

    Raises:
        HTTPException 400: Invitation token is unusable.
        HTTPException 409: Doctor account already exists.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/doctors/set-credentials endpoint")
        response = await UserController().set_doctor_credentials(
            doctor_data=request.model_dump()
        )
        return build_response(DoctorProfileResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/doctors/set-credentials endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/doctors/set-credentials endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@user_router.post(
    "/v1/doctors/verify-otp",
    response_model=DoctorProfileResponse,
    tags=["Doctors"],
)
async def verify_doctor_otp(request: DoctorVerifyOtpRequest):
    """Verify the OTP issued during doctor onboarding.

    Args:
        request: Doctor OTP verification payload.

    Returns:
        DoctorProfileResponse: Verified doctor account summary.

    Raises:
        HTTPException 400: OTP is invalid or expired.
        HTTPException 404: Doctor account does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/doctors/verify-otp endpoint")
        response = await UserController().verify_doctor_otp(
            email=request.email,
            otp=request.otp,
        )
        return build_response(DoctorProfileResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/doctors/verify-otp endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/doctors/verify-otp endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@user_router.post(
    "/v1/doctors/complete-profile",
    response_model=DoctorProfileResponse,
    tags=["Doctors"],
)
async def complete_doctor_profile(request: DoctorCompleteProfileRequest):
    """Complete the doctor's one-time professional profile setup.

    Args:
        request: Doctor professional profile payload.

    Returns:
        DoctorProfileResponse: Activated doctor profile summary.

    Raises:
        HTTPException 400: Doctor onboarding state is invalid.
        HTTPException 404: Doctor account does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/doctors/complete-profile endpoint")
        response = await UserController().complete_doctor_profile(
            profile_data=request.model_dump()
        )
        return build_response(DoctorProfileResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/doctors/complete-profile endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/doctors/complete-profile endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@user_router.get(
    "/v1/users/me",
    response_model=PatientProfileResponse | DoctorProfileResponse | AdminProfileResponse,
    tags=["Users"],
)
async def get_my_profile(
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Fetch the authenticated user's own profile.

    Args:
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        PatientProfileResponse | DoctorProfileResponse | AdminProfileResponse: Profile for the authenticated user.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 404: User record does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling GET /v1/users/me endpoint")
        response = await UserController().get_user_profile(
            user_id=authenticated_user_details["id"]
        )
        role = UserRole(response["role"])
        if role == UserRole.PATIENT:
            return build_response(PatientProfileResponse, response)
        if role == UserRole.DOCTOR:
            return build_response(DoctorProfileResponse, response)
        return build_response(AdminProfileResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in GET /v1/users/me endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in GET /v1/users/me endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@user_router.get(
    "/v1/users/{user_id}",
    response_model=PatientProfileResponse | DoctorProfileResponse | AdminProfileResponse,
    tags=["Users"],
)
async def get_user_profile(
    user_id: str,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Fetch a user profile for the owner or an admin.

    Args:
        user_id: User identifier requested by the route.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        PatientProfileResponse | DoctorProfileResponse | AdminProfileResponse: Profile matching the requested user.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Caller is neither the owner nor an admin.
        HTTPException 404: User record does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling GET /v1/users/{user_id} endpoint")
        require_self_or_roles(
            authenticated_user_details,
            target_user_id=user_id,
            allowed_roles={UserRole.ADMIN},
        )
        response = await UserController().get_user_profile(user_id=user_id)
        role = UserRole(response["role"])
        if role == UserRole.PATIENT:
            return build_response(PatientProfileResponse, response)
        if role == UserRole.DOCTOR:
            return build_response(DoctorProfileResponse, response)
        return build_response(AdminProfileResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in GET /v1/users/{user_id} endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in GET /v1/users/{user_id} endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@user_router.get(
    "/v1/doctors",
    response_model=DoctorListResponse,
    tags=["Doctors"],
)
async def list_doctors(
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """List doctor accounts for authenticated users.

    Args:
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        DoctorListResponse: Collection of doctor profile records.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling GET /v1/doctors endpoint")
        require_roles(
            authenticated_user_details,
            allowed_roles={UserRole.ADMIN, UserRole.DOCTOR, UserRole.PATIENT},
        )
        response = await UserController().list_doctors()
        return build_response(DoctorListResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in GET /v1/doctors endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in GET /v1/doctors endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@user_router.get(
    "/v1/patients",
    response_model=PatientListResponse,
    tags=["Patients"],
)
async def list_patients(
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """List patient accounts for admin operational views.

    Args:
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        PatientListResponse: Collection of patient profile records.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not an admin.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling GET /v1/patients endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.ADMIN})
        response = await UserController().list_patients()
        return build_response(PatientListResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in GET /v1/patients endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in GET /v1/patients endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
