"""Shared router dependencies for authentication and authorization."""

from __future__ import annotations

import types
from typing import Any, get_args, get_origin

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from backend.commons.auth import decodeJWT
from backend.commons.logger import logger
from backend.core.models.user_model import UserRole

logging = logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


def get_authenticated_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Decode the bearer token and return the authenticated user context.

    Args:
        token: OAuth2 bearer token supplied by the request.

    Returns:
        dict: Decoded JWT payload containing user identity fields.

    Raises:
        HTTPException 401: Token is missing, invalid, or expired.
    """

    authenticated_user_details = decodeJWT(token=token)
    if not authenticated_user_details:
        logging.warning("Route authentication failed because token is invalid or expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return authenticated_user_details


def get_authenticated_role(authenticated_user_details: dict) -> UserRole:
    """Read and validate the authenticated user's role from the token payload.

    Args:
        authenticated_user_details: Decoded JWT payload from the auth dependency.

    Returns:
        UserRole: Normalized authenticated user role enum.

    Raises:
        HTTPException 401: Token payload does not contain a supported role.
    """

    try:
        return UserRole(authenticated_user_details["user_role"])
    except (KeyError, ValueError) as error:
        logging.warning(f"Route authentication failed because role payload is invalid: {error}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from error


def require_roles(
    authenticated_user_details: dict,
    *,
    allowed_roles: set[UserRole],
) -> UserRole:
    """Ensure the authenticated user belongs to one of the allowed roles.

    Args:
        authenticated_user_details: Decoded JWT payload from the auth dependency.
        allowed_roles: Roles allowed to call the route.

    Returns:
        UserRole: Authenticated user's normalized role.

    Raises:
        HTTPException 403: Authenticated user's role is not permitted.
    """

    authenticated_role = get_authenticated_role(authenticated_user_details)
    if authenticated_role not in allowed_roles:
        logging.warning(
            f"Route authorization failed for user {authenticated_user_details.get('id')} with role {authenticated_role}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource",
        )
    return authenticated_role


def require_self_or_roles(
    authenticated_user_details: dict,
    *,
    target_user_id: str,
    allowed_roles: set[UserRole],
) -> UserRole:
    """Allow access when the target user matches the token or role is whitelisted.

    Args:
        authenticated_user_details: Decoded JWT payload from the auth dependency.
        target_user_id: User identifier referenced by the route path or query.
        allowed_roles: Additional roles that may access the route for other users.

    Returns:
        UserRole: Authenticated user's normalized role.

    Raises:
        HTTPException 403: Authenticated user is neither the target user nor an allowed role.
    """

    authenticated_role = get_authenticated_role(authenticated_user_details)
    authenticated_user_id = authenticated_user_details.get("id")
    if authenticated_user_id == target_user_id or authenticated_role in allowed_roles:
        return authenticated_role

    logging.warning(
        f"Route ownership check failed for user {authenticated_user_id} targeting {target_user_id}"
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this resource",
    )


def build_response(model_class: type[BaseModel], payload: Any) -> BaseModel:
    """Trim controller payloads to the declared response model before validation.

    Args:
        model_class: Pydantic response model class expected by the route.
        payload: Raw controller payload that may include internal-only fields.

    Returns:
        BaseModel: Validated response model instance.
    """

    trimmed_payload = _trim_payload_for_annotation(model_class, payload)
    return model_class(**trimmed_payload)


def _trim_payload_for_annotation(annotation: Any, value: Any) -> Any:
    """Recursively project a payload to the declared annotation shape.

    Args:
        annotation: Target annotation or Pydantic model type.
        value: Raw payload value being projected.

    Returns:
        Any: Payload trimmed to the declared response contract.
    """

    if value is None:
        return None

    origin = get_origin(annotation)
    if origin is None:
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            trimmed: dict[str, Any] = {}
            for field_name, field_info in annotation.model_fields.items():
                if isinstance(value, dict) and field_name in value:
                    trimmed[field_name] = _trim_payload_for_annotation(
                        field_info.annotation,
                        value[field_name],
                    )
            return trimmed
        return value

    if origin is list:
        item_annotation = get_args(annotation)[0] if get_args(annotation) else Any
        return [
            _trim_payload_for_annotation(item_annotation, item)
            for item in value
        ]

    if origin is dict:
        return value

    if origin in {types.UnionType}:
        candidate_annotations = [
            candidate for candidate in get_args(annotation) if candidate is not type(None)
        ]
        nested_model = next(
            (
                candidate
                for candidate in candidate_annotations
                if isinstance(candidate, type) and issubclass(candidate, BaseModel)
            ),
            None,
        )
        if nested_model is not None and isinstance(value, dict):
            return _trim_payload_for_annotation(nested_model, value)
        return value

    if str(origin) == "typing.Union":
        candidate_annotations = [
            candidate for candidate in get_args(annotation) if candidate is not type(None)
        ]
        nested_model = next(
            (
                candidate
                for candidate in candidate_annotations
                if isinstance(candidate, type) and issubclass(candidate, BaseModel)
            ),
            None,
        )
        if nested_model is not None and isinstance(value, dict):
            return _trim_payload_for_annotation(nested_model, value)
        return value

    return value
