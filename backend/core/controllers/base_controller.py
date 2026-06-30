"""Shared controller helpers for payload serialization and time handling."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


class BaseController:
    """Base controller with shared serialization and datetime helpers."""

    @staticmethod
    def _utc_now() -> datetime:
        """Return the current UTC timestamp.

        Returns:
            datetime: Timezone-aware UTC datetime for controller decisions.
        """

        return datetime.now(timezone.utc)

    @classmethod
    def _serialize_value(cls, value: Any) -> Any:
        """Convert ODMantic and BSON values into JSON-friendly primitives.

        Args:
            value: Value extracted from a model, list, or dictionary.

        Returns:
            Any: Serialized value safe for response payload construction.
        """

        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, list):
            return [cls._serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {key: cls._serialize_value(item) for key, item in value.items()}
        if hasattr(value, "model_dump"):
            return cls._serialize_value(value.model_dump())
        return value

    @classmethod
    def _serialize_document(cls, document: Any) -> dict[str, Any]:
        """Convert a persisted model into a response-friendly dictionary.

        Args:
            document: ODMantic model instance or model-like object.

        Returns:
            dict[str, Any]: Serialized payload with a string identifier.
        """

        payload = cls._serialize_value(document.model_dump())
        if hasattr(document, "id"):
            payload["id"] = str(document.id)
        return payload

    @classmethod
    def _serialize_documents(cls, documents: list[Any]) -> list[dict[str, Any]]:
        """Convert multiple persisted models into response dictionaries.

        Args:
            documents: Sequence of ODMantic model instances.

        Returns:
            list[dict[str, Any]]: Serialized payloads for each model instance.
        """

        return [cls._serialize_document(document) for document in documents]

    @classmethod
    def _normalize_datetime(cls, value: datetime) -> datetime:
        """Normalize a datetime value to timezone-aware UTC.

        Args:
            value: Input datetime from request or persistence state.

        Returns:
            datetime: UTC-normalized datetime for comparisons.
        """

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
