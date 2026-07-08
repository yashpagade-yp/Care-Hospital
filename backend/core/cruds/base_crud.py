"""Reusable ODMantic CRUD helpers for MedCare persistence modules.

This module centralizes common create, read, update, delete, and list behavior
so domain CRUD classes can stay focused on resource-specific queries.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from bson import ObjectId
from odmantic import Model
from odmantic.query import QueryExpression

from backend.commons.logger import logger
from backend.core.database.database import get_engine

logging = logger(__name__)

ModelType = TypeVar("ModelType", bound=Model)


class BaseCRUD(Generic[ModelType]):
    """Generic ODMantic CRUD helper for model-specific repository classes."""

    def __init__(self, model: type[ModelType]):
        """Store the ODMantic model used by the CRUD helper.

        Args:
            model: ODMantic model class handled by this CRUD helper.
        """

        self.model = model

    async def create(self, *, obj_in: dict[str, Any]) -> ModelType:
        """Create and persist a new model instance.

        Args:
            obj_in: Dictionary payload used to instantiate the model.

        Returns:
            ModelType: Persisted ODMantic model instance.

        Raises:
            Exception: If the database write fails.
        """

        try:
            logging.info(f"Executing {self.__class__.__name__}.create")
            db_object = self.model(**obj_in)
            engine = get_engine()
            await engine.save(db_object)
            return db_object
        except Exception as error:
            logging.error(f"Error in {self.__class__.__name__}.create: {error}")
            raise

    async def get_by_id(self, *, id: str) -> ModelType | None:
        """Read a model instance by its MongoDB ObjectId string.

        Args:
            id: String representation of the ODMantic model identifier.

        Returns:
            ModelType | None: Matching model instance when found.
        """

        try:
            logging.info(f"Executing {self.__class__.__name__}.get_by_id")
            object_id = self._parse_object_id(id=id)
            if object_id is None:
                logging.warning(f"Invalid ObjectId supplied to get_by_id: {id}")
                return None

            engine = get_engine()
            return await engine.find_one(self.model, self.model.id == object_id)
        except Exception as error:
            logging.error(f"Error in {self.__class__.__name__}.get_by_id: {error}")
            raise

    async def get_one(self, *filters: QueryExpression) -> ModelType | None:
        """Read a single model instance matching the given ODMantic filters.

        Args:
            *filters: ODMantic query filters applied to the lookup.

        Returns:
            ModelType | None: First matching model instance, if any.
        """

        try:
            logging.info(f"Executing {self.__class__.__name__}.get_one")
            engine = get_engine()
            return await engine.find_one(self.model, *filters)
        except Exception as error:
            logging.error(f"Error in {self.__class__.__name__}.get_one: {error}")
            raise

    async def get_many(
        self,
        *filters: QueryExpression,
        sort: Any = None,
        skip: int = 0,
        limit: int | None = None,
    ) -> list[ModelType]:
        """Read multiple model instances matching the given filters.

        Args:
            *filters: ODMantic query filters applied to the lookup.
            sort: Optional ODMantic sort expression.
            skip: Number of records to skip for pagination.
            limit: Optional maximum number of records to return.

        Returns:
            list[ModelType]: Matching model instances.
        """

        try:
            logging.info(f"Executing {self.__class__.__name__}.get_many")
            engine = get_engine()
            return await engine.find(
                self.model,
                *filters,
                sort=sort,
                skip=skip,
                limit=limit,
            )
        except Exception as error:
            logging.error(f"Error in {self.__class__.__name__}.get_many: {error}")
            raise

    async def update(self, *, id: str, obj_in: dict[str, Any]) -> ModelType | None:
        """Update a persisted model instance by identifier.

        Args:
            id: String representation of the ODMantic model identifier.
            obj_in: Partial update payload.

        Returns:
            ModelType | None: Updated model instance when found.
        """

        try:
            logging.info(f"Executing {self.__class__.__name__}.update")
            db_object = await self.get_by_id(id=id)
            if db_object is None:
                logging.warning(f"No {self.model.__name__} found with id: {id}")
                return None

            for field, value in obj_in.items():
                setattr(db_object, field, value)

            if hasattr(db_object, "updated_at"):
                setattr(db_object, "updated_at", datetime.now(timezone.utc))

            engine = get_engine()
            await engine.save(db_object)
            return db_object
        except Exception as error:
            logging.error(f"Error in {self.__class__.__name__}.update: {error}")
            raise

    async def delete(self, *, id: str) -> bool:
        """Delete a persisted model instance by identifier.

        Args:
            id: String representation of the ODMantic model identifier.

        Returns:
            bool: True when a matching record was deleted, otherwise False.
        """

        try:
            logging.info(f"Executing {self.__class__.__name__}.delete")
            db_object = await self.get_by_id(id=id)
            if db_object is None:
                logging.warning(f"No {self.model.__name__} found with id: {id}")
                return False

            engine = get_engine()
            await engine.delete(db_object)
            return True
        except Exception as error:
            logging.error(f"Error in {self.__class__.__name__}.delete: {error}")
            raise

    async def count(self, *filters: QueryExpression) -> int:
        """Count model instances matching the given filters.

        Args:
            *filters: ODMantic query filters applied to the count operation.

        Returns:
            int: Number of matching records.
        """

        try:
            logging.info(f"Executing {self.__class__.__name__}.count")
            engine = get_engine()
            return await engine.count(self.model, *filters)
        except Exception as error:
            logging.error(f"Error in {self.__class__.__name__}.count: {error}")
            raise

    @staticmethod
    def _parse_object_id(*, id: str) -> ObjectId | None:
        """Convert a string identifier into a MongoDB ObjectId.

        Args:
            id: Potential MongoDB ObjectId string.

        Returns:
            ObjectId | None: Parsed ObjectId when valid, otherwise None.
        """

        return ObjectId(id) if ObjectId.is_valid(id) else None
