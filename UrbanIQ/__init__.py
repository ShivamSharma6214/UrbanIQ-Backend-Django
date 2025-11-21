# package init
from .celery import app as celery_app

# Expose celery app as a module-level variable so `celery -A UrbanIQ worker` can find it
__all__ = ('celery_app',)
