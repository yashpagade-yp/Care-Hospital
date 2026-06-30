"""Prescription routes for the MedCare API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.commons.logger import logger
from backend.core.apis.routers.router_dependencies import (
    build_response,
    get_authenticated_user,
    require_roles,
    require_self_or_roles,
)
from backend.core.apis.schemas.request_schemas.prescription_request_schema import (
    CreatePrescriptionRequest,
    UpdatePrescriptionRequest,
)
from backend.core.apis.schemas.responses_schemas.prescription_response_schema import (
    PrescriptionListResponse,
    PrescriptionResponse,
)
from backend.core.controllers.prescription_controller import PrescriptionController
from backend.core.models.user_model import UserRole

prescription_router = APIRouter()
logging = logger(__name__)


@prescription_router.post(
    "/v1/doctors/prescriptions",
    status_code=status.HTTP_201_CREATED,
    response_model=PrescriptionResponse,
    tags=["Prescriptions"],
)
async def create_prescription(
    request: CreatePrescriptionRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Create a prescription as the authenticated doctor.

    Args:
        request: Prescription creation payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        PrescriptionResponse: Created prescription details.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not a doctor.
        HTTPException 404: Appointment does not exist.
        HTTPException 409: Prescription already exists for the appointment.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/doctors/prescriptions endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.DOCTOR})
        response = await PrescriptionController().create_prescription(
            doctor_id=authenticated_user_details["id"],
            prescription_data=request.model_dump(),
        )
        return build_response(PrescriptionResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/doctors/prescriptions endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/doctors/prescriptions endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@prescription_router.patch(
    "/v1/doctors/prescriptions/{prescription_id}",
    response_model=PrescriptionResponse,
    tags=["Prescriptions"],
)
async def update_prescription(
    prescription_id: str,
    request: UpdatePrescriptionRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Update a prescription as the authenticated doctor owner.

    Args:
        prescription_id: Prescription record identifier.
        request: Prescription update payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        PrescriptionResponse: Updated prescription details.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not a doctor.
        HTTPException 404: Prescription does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling PATCH /v1/doctors/prescriptions/{prescription_id} endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.DOCTOR})
        response = await PrescriptionController().update_prescription(
            prescription_id=prescription_id,
            doctor_id=authenticated_user_details["id"],
            update_data=request.model_dump(),
        )
        return build_response(PrescriptionResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in PATCH /v1/doctors/prescriptions/{prescription_id} endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in PATCH /v1/doctors/prescriptions/{prescription_id} endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@prescription_router.get(
    "/v1/appointments/{appointment_id}/prescription",
    response_model=PrescriptionResponse,
    tags=["Prescriptions"],
)
async def get_prescription_by_appointment(
    appointment_id: str,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Fetch a prescription for the related doctor-patient pair only.

    Args:
        appointment_id: Appointment identifier linked to the prescription.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        PrescriptionResponse: Prescription linked to the appointment.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not allowed to access prescriptions.
        HTTPException 404: Appointment or prescription does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling GET /v1/appointments/{appointment_id}/prescription endpoint")
        authenticated_role = require_roles(
            authenticated_user_details,
            allowed_roles={UserRole.PATIENT, UserRole.DOCTOR},
        )
        response = await PrescriptionController().get_prescription_by_appointment(
            appointment_id=appointment_id,
            actor_id=authenticated_user_details["id"],
            actor_role=authenticated_role,
        )
        return build_response(PrescriptionResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in GET /v1/appointments/{appointment_id}/prescription endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in GET /v1/appointments/{appointment_id}/prescription endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@prescription_router.get(
    "/v1/patients/{patient_id}/prescriptions",
    response_model=PrescriptionListResponse,
    tags=["Prescriptions"],
)
async def list_prescriptions_for_patient(
    patient_id: str,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """List prescriptions visible to the owning patient.

    Args:
        patient_id: Patient identifier referenced by the route.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        PrescriptionListResponse: Collection of patient-visible prescriptions.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Caller is not the patient owner.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling GET /v1/patients/{patient_id}/prescriptions endpoint")
        require_self_or_roles(
            authenticated_user_details,
            target_user_id=patient_id,
            allowed_roles=set(),
        )
        require_roles(authenticated_user_details, allowed_roles={UserRole.PATIENT})
        response = await PrescriptionController().list_prescriptions_for_patient(
            patient_id=patient_id
        )
        return build_response(PrescriptionListResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in GET /v1/patients/{patient_id}/prescriptions endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in GET /v1/patients/{patient_id}/prescriptions endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@prescription_router.get(
    "/v1/doctors/{doctor_id}/prescriptions",
    response_model=PrescriptionListResponse,
    tags=["Prescriptions"],
)
async def list_prescriptions_for_doctor(
    doctor_id: str,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """List prescriptions created by the owning doctor.

    Args:
        doctor_id: Doctor identifier referenced by the route.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        PrescriptionListResponse: Collection of doctor-created prescriptions.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Caller is not the doctor owner.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling GET /v1/doctors/{doctor_id}/prescriptions endpoint")
        require_self_or_roles(
            authenticated_user_details,
            target_user_id=doctor_id,
            allowed_roles=set(),
        )
        require_roles(authenticated_user_details, allowed_roles={UserRole.DOCTOR})
        response = await PrescriptionController().list_prescriptions_for_doctor(
            doctor_id=doctor_id
        )
        return build_response(PrescriptionListResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in GET /v1/doctors/{doctor_id}/prescriptions endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in GET /v1/doctors/{doctor_id}/prescriptions endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
