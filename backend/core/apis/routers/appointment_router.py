"""Appointment booking and lifecycle routes for the MedCare API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.commons.logger import logger
from backend.core.apis.routers.router_dependencies import (
    build_response,
    get_authenticated_user,
    require_roles,
    require_self_or_roles,
)
from backend.core.apis.schemas.request_schemas.appointment_request_schema import (
    CancelAppointmentRequest,
    ConfirmAppointmentRequest,
    CreateSlotHoldRequest,
    RescheduleAppointmentRequest,
    TelegramGuestAppointmentRequest,
    UpdateAppointmentStatusRequest,
)
from backend.core.apis.schemas.responses_schemas.appointment_response_schema import (
    AppointmentConfirmationResponse,
    AppointmentDetailResponse,
    AppointmentListResponse,
    AppointmentRescheduleResponse,
    AppointmentResponse,
    BookedSlotListResponse,
    SlotHoldResponse,
)
from backend.core.controllers.appointment_controller import AppointmentController
from backend.core.models.user_model import UserRole

appointment_router = APIRouter()
logging = logger(__name__)


@appointment_router.post(
    "/v1/public/telegram/appointments",
    status_code=status.HTTP_201_CREATED,
    response_model=AppointmentConfirmationResponse,
    tags=["Appointments"],
)
async def create_telegram_guest_appointment(request: TelegramGuestAppointmentRequest):
    """Create a lightweight public Telegram appointment without web-app login."""

    try:
        logging.info("Calling POST /v1/public/telegram/appointments endpoint")
        response = await AppointmentController().create_telegram_guest_appointment(
            booking_data=request.model_dump(),
        )
        return build_response(AppointmentConfirmationResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/public/telegram/appointments endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/public/telegram/appointments endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@appointment_router.post(
    "/v1/appointments/slot-holds",
    status_code=status.HTTP_201_CREATED,
    response_model=SlotHoldResponse,
    tags=["Appointments"],
)
async def create_slot_hold(
    request: CreateSlotHoldRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Create a temporary slot hold for the authenticated patient.

    Args:
        request: Slot-hold creation payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        SlotHoldResponse: Created temporary slot hold details.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not a patient.
        HTTPException 404: Patient or doctor does not exist.
        HTTPException 409: Slot is already held or booked.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/appointments/slot-holds endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.PATIENT})
        response = await AppointmentController().create_slot_hold(
            patient_id=authenticated_user_details["id"],
            slot_hold_data=request.model_dump(),
        )
        return build_response(SlotHoldResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/appointments/slot-holds endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/appointments/slot-holds endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@appointment_router.post(
    "/v1/appointments/confirm",
    status_code=status.HTTP_201_CREATED,
    response_model=AppointmentConfirmationResponse,
    tags=["Appointments"],
)
async def confirm_appointment(
    request: ConfirmAppointmentRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Confirm an appointment from the authenticated patient's active hold.

    Args:
        request: Appointment confirmation payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        AppointmentConfirmationResponse: Confirmed appointment and payment details.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not a patient.
        HTTPException 404: Slot hold does not exist.
        HTTPException 409: Slot is already booked.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling POST /v1/appointments/confirm endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.PATIENT})
        response = await AppointmentController().confirm_appointment(
            patient_id=authenticated_user_details["id"],
            confirmation_data=request.model_dump(),
        )
        return build_response(AppointmentConfirmationResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/appointments/confirm endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/appointments/confirm endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@appointment_router.patch(
    "/v1/appointments/{appointment_id}/cancel",
    response_model=AppointmentResponse,
    tags=["Appointments"],
)
async def cancel_appointment(
    appointment_id: str,
    request: CancelAppointmentRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Cancel an appointment as the owning patient or doctor.

    Args:
        appointment_id: Appointment identifier being cancelled.
        request: Appointment cancellation payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        AppointmentResponse: Updated cancelled appointment details.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not allowed to cancel the appointment.
        HTTPException 404: Appointment does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling PATCH /v1/appointments/{appointment_id}/cancel endpoint")
        authenticated_role = require_roles(
            authenticated_user_details,
            allowed_roles={UserRole.PATIENT, UserRole.DOCTOR},
        )
        response = await AppointmentController().cancel_appointment(
            appointment_id=appointment_id,
            actor_id=authenticated_user_details["id"],
            actor_role=authenticated_role,
            cancel_reason=request.cancel_reason,
        )
        return build_response(AppointmentResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in PATCH /v1/appointments/{appointment_id}/cancel endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in PATCH /v1/appointments/{appointment_id}/cancel endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@appointment_router.patch(
    "/v1/appointments/{appointment_id}/reschedule",
    response_model=AppointmentRescheduleResponse,
    tags=["Appointments"],
)
async def reschedule_appointment(
    appointment_id: str,
    request: RescheduleAppointmentRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Reschedule an appointment as the owning patient or doctor.

    Args:
        appointment_id: Appointment identifier being rescheduled.
        request: Appointment reschedule payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        AppointmentRescheduleResponse: Updated original and replacement appointments.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not allowed to reschedule the appointment.
        HTTPException 404: Appointment does not exist.
        HTTPException 409: Requested slot is already booked.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(
            f"Calling PATCH /v1/appointments/{appointment_id}/reschedule endpoint"
        )
        authenticated_role = require_roles(
            authenticated_user_details,
            allowed_roles={UserRole.PATIENT, UserRole.DOCTOR},
        )
        response = await AppointmentController().reschedule_appointment(
            appointment_id=appointment_id,
            actor_id=authenticated_user_details["id"],
            actor_role=authenticated_role,
            reschedule_data=request.model_dump(),
        )
        return build_response(AppointmentRescheduleResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in PATCH /v1/appointments/{appointment_id}/reschedule endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in PATCH /v1/appointments/{appointment_id}/reschedule endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@appointment_router.patch(
    "/v1/appointments/{appointment_id}/status",
    response_model=AppointmentResponse,
    tags=["Appointments"],
)
async def update_appointment_status(
    appointment_id: str,
    request: UpdateAppointmentStatusRequest,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Update an appointment lifecycle status as the owning doctor.

    Args:
        appointment_id: Appointment identifier being updated.
        request: Appointment status update payload.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        AppointmentResponse: Updated appointment details.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not a doctor.
        HTTPException 404: Appointment does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling PATCH /v1/appointments/{appointment_id}/status endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.DOCTOR})
        response = await AppointmentController().update_appointment_status(
            appointment_id=appointment_id,
            doctor_id=authenticated_user_details["id"],
            new_status=request.status,
        )
        return build_response(AppointmentResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in PATCH /v1/appointments/{appointment_id}/status endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in PATCH /v1/appointments/{appointment_id}/status endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@appointment_router.get(
    "/v1/patients/{patient_id}/appointments",
    response_model=AppointmentListResponse,
    tags=["Appointments"],
)
async def list_patient_appointments(
    patient_id: str,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """List appointments for a patient owner or an admin.

    Args:
        patient_id: Patient identifier referenced by the route.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        AppointmentListResponse: Collection of patient appointments.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Caller is neither the patient nor an admin.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling GET /v1/patients/{patient_id}/appointments endpoint")
        require_self_or_roles(
            authenticated_user_details,
            target_user_id=patient_id,
            allowed_roles={UserRole.ADMIN},
        )
        response = await AppointmentController().list_patient_appointments(
            patient_id=patient_id
        )
        return build_response(AppointmentListResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in GET /v1/patients/{patient_id}/appointments endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in GET /v1/patients/{patient_id}/appointments endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@appointment_router.get(
    "/v1/doctors/{doctor_id}/appointments",
    response_model=AppointmentListResponse,
    tags=["Appointments"],
)
async def list_doctor_appointments(
    doctor_id: str,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """List appointments for a doctor owner or an admin.

    Args:
        doctor_id: Doctor identifier referenced by the route.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        AppointmentListResponse: Collection of doctor appointments.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Caller is neither the doctor nor an admin.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling GET /v1/doctors/{doctor_id}/appointments endpoint")
        require_self_or_roles(
            authenticated_user_details,
            target_user_id=doctor_id,
            allowed_roles={UserRole.ADMIN},
        )
        response = await AppointmentController().list_doctor_appointments(
            doctor_id=doctor_id
        )
        return build_response(AppointmentListResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in GET /v1/doctors/{doctor_id}/appointments endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in GET /v1/doctors/{doctor_id}/appointments endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@appointment_router.get(
    "/v1/admin/appointments",
    response_model=AppointmentListResponse,
    tags=["Appointments"],
)
async def list_admin_appointments(
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """List all appointments for admin operational oversight.

    Args:
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        AppointmentListResponse: Collection of platform appointment records.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not an admin.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info("Calling GET /v1/admin/appointments endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.ADMIN})
        response = await AppointmentController().list_all_appointments()
        return build_response(AppointmentListResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in GET /v1/admin/appointments endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in GET /v1/admin/appointments endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@appointment_router.get(
    "/v1/doctors/{doctor_id}/booked-slots",
    response_model=BookedSlotListResponse,
    tags=["Appointments"],
)
async def list_doctor_booked_slots(
    doctor_id: str,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """List booked slot datetimes for a doctor.

    Returns only occupied slot times so authenticated booking users can avoid
    selecting unavailable slots without receiving other patients' details.

    Args:
        doctor_id: Doctor identifier referenced by the route.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        BookedSlotListResponse: Collection of booked doctor slot datetimes.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated role is not allowed to view booking availability.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling GET /v1/doctors/{doctor_id}/booked-slots endpoint")
        require_roles(
            authenticated_user_details,
            allowed_roles={UserRole.PATIENT, UserRole.DOCTOR, UserRole.ADMIN},
        )
        response = await AppointmentController().list_doctor_booked_slots(
            doctor_id=doctor_id
        )
        return build_response(BookedSlotListResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in GET /v1/doctors/{doctor_id}/booked-slots endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(
            f"Error in GET /v1/doctors/{doctor_id}/booked-slots endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@appointment_router.get(
    "/v1/appointments/{appointment_id}",
    response_model=AppointmentDetailResponse,
    tags=["Appointments"],
)
async def get_appointment_detail(
    appointment_id: str,
    authenticated_user_details: dict = Depends(get_authenticated_user),
):
    """Fetch appointment detail for admin operational views.

    Args:
        appointment_id: Appointment identifier requested by the route.
        authenticated_user_details: Decoded authenticated user context.

    Returns:
        AppointmentDetailResponse: Appointment detail with lightweight names.

    Raises:
        HTTPException 401: Authentication token is invalid or expired.
        HTTPException 403: Authenticated user is not an admin.
        HTTPException 404: Appointment does not exist.
        HTTPException 500: Internal server error.
    """

    try:
        logging.info(f"Calling GET /v1/appointments/{appointment_id} endpoint")
        require_roles(authenticated_user_details, allowed_roles={UserRole.ADMIN})
        response = await AppointmentController().get_appointment_detail(
            appointment_id=appointment_id
        )
        return build_response(AppointmentDetailResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in GET /v1/appointments/{appointment_id} endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in GET /v1/appointments/{appointment_id} endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
