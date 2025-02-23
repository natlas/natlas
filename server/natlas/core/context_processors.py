"""
There are certain things we want to load into settings and have available in templates.
But we're not insane, so we're not just going to expose all of settings to the templates.
"""

from django.conf import settings


def natlas_settings(request):
    return {
        "NATLAS": settings.NATLAS,
    }
