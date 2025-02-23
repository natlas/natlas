from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base class that provides self-updating 'created' and 'modified' fields.
    """

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    last_modified_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
