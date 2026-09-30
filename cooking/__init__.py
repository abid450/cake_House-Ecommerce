# Payment/__init__.py
from cooking.celery import app as celery_app

__all__ = ('celery_app',)