from typing import Generic, Optional, Type, TypeVar

from django.db.models import Model, QuerySet


T = TypeVar("T", bound=Model)


class BaseRepository(Generic[T]):
    """
    Generic base repository providing common CRUD and query operations.
    All app-level repositories inherit from this class.

    Usage:
        class InstrumentRepository(BaseRepository[Instrument]):
            model = Instrument
    """

    model: Type[T]

    def __init_subclass__(cls, **kwargs) -> None:
        """
        Enforce that every subclass declares a model attribute.
        Raises TypeError at class definition time if missing.
        """
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "model"):
            raise TypeError(
                f"Repository '{cls.__name__}' must define a 'model' class attribute."
            )

    # ------------------------------------------------------------------
    # Read Operations
    # ------------------------------------------------------------------

    @classmethod
    def all(cls) -> QuerySet[T]:
        """Return all records."""
        return cls.model.objects.all()

    @classmethod
    def active(cls) -> QuerySet[T]:
        """Return only active records (is_active=True)."""
        return cls.model.objects.filter(is_active=True)

    @classmethod
    def get_by_id(cls, id: int) -> Optional[T]:
        """Return a single record by primary key, or None."""
        return cls.model.objects.filter(pk=id).first()

    @classmethod
    def filter(cls, **kwargs) -> QuerySet[T]:
        """Return filtered queryset by arbitrary kwargs."""
        return cls.model.objects.filter(**kwargs)

    @classmethod
    def first(cls, **kwargs) -> Optional[T]:
        """Return the first matching record or None."""
        return cls.model.objects.filter(**kwargs).first()

    @classmethod
    def count(cls) -> int:
        """Return total record count."""
        return cls.model.objects.count()

    @classmethod
    def exists(cls, **kwargs) -> bool:
        """Return True if any record matches kwargs."""
        return cls.model.objects.filter(**kwargs).exists()

    # ------------------------------------------------------------------
    # Write Operations
    # ------------------------------------------------------------------

    @classmethod
    def create(cls, **kwargs) -> T:
        """Create and return a new record."""
        return cls.model.objects.create(**kwargs)

    @classmethod
    def update(cls, instance: T, **kwargs) -> T:
        """Update fields on an existing instance and save."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    @classmethod
    def delete(cls, instance: T) -> None:
        """Hard delete a record."""
        instance.delete()

    @classmethod
    def soft_delete(cls, instance: T) -> T:
        """Soft delete by setting is_active=False."""
        instance.is_active = False
        instance.save()
        return instance

    # ------------------------------------------------------------------
    # Upsert Operations
    # ------------------------------------------------------------------

    @classmethod
    def get_or_create(
        cls,
        defaults: Optional[dict] = None,
        **kwargs,
    ) -> tuple[T, bool]:
        """Get or create a record. Returns (instance, created)."""
        return cls.model.objects.get_or_create(
            defaults=defaults or {},
            **kwargs,
        )

    @classmethod
    def update_or_create(
        cls,
        defaults: Optional[dict] = None,
        **kwargs,
    ) -> tuple[T, bool]:
        """Update or create a record. Returns (instance, created)."""
        return cls.model.objects.update_or_create(
            defaults=defaults or {},
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Bulk Operations
    # ------------------------------------------------------------------

    @classmethod
    def bulk_create(
        cls,
        objects: list[T],
        batch_size: int = 500,
        ignore_conflicts: bool = False,
    ) -> list[T]:
        """Bulk insert a list of model instances."""
        return cls.model.objects.bulk_create(
            objects,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts,
        )

    @classmethod
    def bulk_update(
        cls,
        objects: list[T],
        fields: list[str],
        batch_size: int = 500,
    ) -> None:
        """Bulk update specific fields on a list of model instances."""
        cls.model.objects.bulk_update(
            objects,
            fields,
            batch_size=batch_size,
        )

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    @classmethod
    def paginate(
        cls,
        queryset: QuerySet[T],
        page: int = 1,
        page_size: int = 20,
    ) -> QuerySet[T]:
        """Return a sliced queryset for the given page and page_size."""
        start = (page - 1) * page_size
        end = start + page_size
        return queryset[start:end]