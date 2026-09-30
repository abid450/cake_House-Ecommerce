# cooking/celery.py

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cooking.settings')

app = Celery('cooking')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery"""
    print(f'✅ Debug task executed! ID: {self.request.id}')
    return {'status': 'success', 'message': 'Celery is working with RabbitMQ!'}


# ============================================================
# ✅ TASK ROUTES (Simplified)
# ============================================================
app.conf.task_routes = {
    'Task.tasks.send_verification_email': {'queue': 'email'},
    'Task.tasks.send_welcome_email': {'queue': 'email'},
    'Task.tasks.send_bulk_email': {'queue': 'email'},
    'Task.tasks.send_weekly_newsletter': {'queue': 'email'},
    'Task.tasks.send_test_email': {'queue': 'email'},
    'Task.tasks.send_low_stock_alerts': {'queue': 'priority'},
    'Task.tasks.generate_daily_sales_report': {'queue': 'background'},
    'Task.tasks.backup_database': {'queue': 'background'},
    'Task.tasks.cleanup_expired_verification_tokens': {'queue': 'background'},
    'Task.tasks.cleanup_expired_carts': {'queue': 'background'},
    'customers.tasks.send_login_alert_email': {'queue': 'email'},
    'orders.tasks.send_order_confirmation_email': {'queue': 'email'},
    'orders.tasks.send_order_status_update_email': {'queue': 'email'},
    'orders.tasks.process_order_payment': {'queue': 'email'},



}


# ============================================================
# ✅ TASK QUEUES (Simplified)
# ============================================================
app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'email': {
        'exchange': 'email',
        'routing_key': 'email',
        'exchange_type': 'direct',
    },
    'priority': {
        'exchange': 'priority',
        'routing_key': 'priority',
        'exchange_type': 'direct',
    },
    'background': {
        'exchange': 'background',
        'routing_key': 'background',
        'exchange_type': 'direct',
    },
}


# ============================================================
# ✅ BEAT SCHEDULE
# ============================================================
app.conf.beat_schedule = {
    'cleanup-expired-verification-tokens': {
        'task': 'Task.tasks.cleanup_expired_verification_tokens',
        'schedule': crontab(hour=0, minute=0),
    },
    'send-low-stock-alerts': {
        'task': 'Task.tasks.send_low_stock_alerts',
        'schedule': crontab(hour=8, minute=0),
    },
    'generate-daily-sales-report': {
        'task': 'Task.tasks.generate_daily_sales_report',
        'schedule': crontab(hour=23, minute=59),
    },
    'cleanup-expired-carts': {
        'task': 'cart.tasks.cleanup_expired_carts',
        'schedule': crontab(hour=2, minute=0),
    },
}


# ============================================================
# ✅ TASK SETTINGS
# ============================================================
app.conf.task_time_limit = 30 * 60
app.conf.task_soft_time_limit = 25 * 60
app.conf.task_max_retries = 3
app.conf.task_default_retry_delay = 60
app.conf.task_acks_late = True
app.conf.task_track_started = True
app.conf.task_send_sent_event = False