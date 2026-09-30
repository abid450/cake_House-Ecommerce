# order/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order, OrderStatusHistory


@receiver(pre_save, sender=Order)
def _stash_previous_status(sender, instance, **kwargs):
    """Remember previous status"""
    if instance.pk:
        try:
            instance._previous_status = Order.objects.get(pk=instance.pk).status
        except Order.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Order)
def _log_status_change(sender, instance, created, **kwargs):
    """Log status change automatically"""
    if created:
        return
    
    previous = getattr(instance, '_previous_status', None)
    if previous and previous != instance.status:
        OrderStatusHistory.objects.create(
            order=instance,
            status=instance.status,
            note=f'Status changed from {previous} to {instance.status}'
        )