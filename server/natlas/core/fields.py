import secrets

from django.db import models


class PrefixedUniqueIDField(models.CharField):
    """
    A Django model field that generates a unique ID with a globally unique prefix.
    """

    description = "A globally unique prefixed ID field"

    def __init__(self, prefix, *args, **kwargs):
        self.prefix = prefix
        kwargs.setdefault("max_length", len(prefix) + 36)
        kwargs.setdefault("unique", True)
        kwargs.setdefault("editable", False)
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        """
        Generates a unique value if not already set.
        """
        value = f"{self.prefix}_{secrets.token_urlsafe(16)}"
        setattr(model_instance, self.attname, value)
        return value

    def deconstruct(self):
        """
        Ensures the prefix is stored correctly for migrations.
        """
        name, path, args, kwargs = super().deconstruct()
        kwargs["prefix"] = self.prefix
        return name, path, args, kwargs
