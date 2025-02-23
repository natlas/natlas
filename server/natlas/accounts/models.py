from typing import ClassVar

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

from natlas.accounts.validators import validate_deliverable_email
from natlas.core.fields import PrefixedUniqueIDField
from natlas.core.models import TimeStampedModel


class UserManager(BaseUserManager):
    """Manager for custom user model."""

    @classmethod
    def normalize_email(cls, email: str | None) -> str:
        """Normalize the email address by using the validate_email function"""
        return validate_deliverable_email(email).normalized.casefold()

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        """Create and return a regular user with an email."""
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        """Create and return a superuser with given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, TimeStampedModel, PermissionsMixin):
    """Custom user model that uses email instead of username."""

    id = PrefixedUniqueIDField(prefix="usr", primary_key=True, editable=False)
    email = models.EmailField(unique=True, validators=[validate_deliverable_email])
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_confirmed = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"  # Log in using email
    REQUIRED_FIELDS: ClassVar = []  # No extra required fields (besides email and password)

    def __str__(self):
        return self.email

    class Meta:
        db_table = "users"
