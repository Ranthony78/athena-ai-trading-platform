from django.contrib.auth.models import AbstractUser
from django.db import models

from shared.models import BaseModel


class User(AbstractUser, BaseModel):
    """
    Custom User Model
    """

    email = models.EmailField(unique=True)

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    timezone = models.CharField(
        max_length=100,
        default="Asia/Kolkata",
    )

    is_email_verified = models.BooleanField(
        default=False,
    )

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username