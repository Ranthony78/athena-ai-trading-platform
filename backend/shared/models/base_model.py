from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """
    Abstract base model inherited by all application models.
    """

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        abstract = True