"""Authentication routes for the MedCare API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.commons.logger import logger
from backend.core.apis.routers.router_dependencies import build_response
from backend.core.apis.schemas.request_schemas.auth_request_schema import (
    ForgotPasswordRequest,
    LoginRequest,
    ResendOtpRequest,
    ResetPasswordRequest,
    VerifyPasswordResetOtpRequest,
)
from backend.core.apis.schemas.responses_schemas.auth_response_schema import (
    LoginResponse,
    OtpSentResponse,
    PasswordResetResponse,
)
from backend.core.controllers.auth_controller import AuthController

auth_router = APIRouter()
logging = logger(__name__)


@auth_router.post(
    "/v1/auth/login",
    response_model=LoginResponse,
    tags=["Auth"],
)
async def login(request: LoginRequest):
    """Authenticate a user with the shared login flow.

    Args:
        request: Shared login payload.

    Returns:
        LoginResponse: Signed JWT token with basic user summary.
    """

    try:
        logging.info("Calling POST /v1/auth/login endpoint")
        response = await AuthController().login(
            email=request.email,
            password=request.password,
        )
        return build_response(LoginResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/auth/login endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/auth/login endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@auth_router.post(
    "/v1/auth/resend-otp",
    response_model=OtpSentResponse,
    tags=["Auth"],
)
async def resend_otp(request: ResendOtpRequest):
    """Resend an OTP for onboarding or password reset workflows.

    Args:
        request: OTP resend payload.

    Returns:
        OtpSentResponse: OTP dispatch metadata.
    """

    try:
        logging.info("Calling POST /v1/auth/resend-otp endpoint")
        response = await AuthController().resend_otp(
            email=request.email,
            purpose=request.purpose,
        )
        return build_response(OtpSentResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/auth/resend-otp endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/auth/resend-otp endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@auth_router.post(
    "/v1/auth/forgot-password",
    response_model=OtpSentResponse,
    tags=["Auth"],
)
async def forgot_password(request: ForgotPasswordRequest):
    """Start the password reset flow without disclosing account existence.

    Args:
        request: Forgot-password request payload.

    Returns:
        OtpSentResponse: Generic password reset dispatch metadata.
    """

    try:
        logging.info("Calling POST /v1/auth/forgot-password endpoint")
        response = await AuthController().forgot_password(email=request.email)
        return build_response(OtpSentResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/auth/forgot-password endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/auth/forgot-password endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@auth_router.post(
    "/v1/auth/verify-password-reset-otp",
    response_model=PasswordResetResponse,
    tags=["Auth"],
)
async def verify_password_reset_otp(request: VerifyPasswordResetOtpRequest):
    """Verify a password reset OTP before accepting a new password.

    Args:
        request: Password reset OTP verification payload.

    Returns:
        PasswordResetResponse: Human-readable verification result.
    """

    try:
        logging.info("Calling POST /v1/auth/verify-password-reset-otp endpoint")
        response = await AuthController().verify_password_reset_otp(
            email=request.email,
            otp=request.otp,
        )
        return build_response(PasswordResetResponse, response)
    except HTTPException as http_error:
        logging.error(
            f"Error in POST /v1/auth/verify-password-reset-otp endpoint: {http_error}"
        )
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/auth/verify-password-reset-otp endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@auth_router.post(
    "/v1/auth/reset-password",
    response_model=PasswordResetResponse,
    tags=["Auth"],
)
async def reset_password(request: ResetPasswordRequest):
    """Persist a new password after password reset OTP validation.

    Args:
        request: Final password reset payload.

    Returns:
        PasswordResetResponse: Human-readable password reset completion message.
    """

    try:
        logging.info("Calling POST /v1/auth/reset-password endpoint")
        response = await AuthController().reset_password(
            email=request.email,
            otp=request.otp,
            new_password=request.new_password,
        )
        return build_response(PasswordResetResponse, response)
    except HTTPException as http_error:
        logging.error(f"Error in POST /v1/auth/reset-password endpoint: {http_error}")
        raise http_error
    except Exception as error:
        logging.error(f"Error in POST /v1/auth/reset-password endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
