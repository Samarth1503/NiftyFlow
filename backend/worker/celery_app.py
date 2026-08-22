from celery import Celery
from celery.schedules import crontab
from backend.core.config import settings

celery_app = Celery(
    "niftyflow_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["backend.worker.tasks", "backend.worker.schedule_tasks", "backend.worker.ml_tasks"]
)

celery_app.conf.timezone = getattr(settings, 'STOCK_FULL_UPDATE_TIMEZONE', 'UTC')
celery_app.conf.enable_utc = True

# Parse the scheduled time from settings (e.g. "21:00")
try:
    update_time = getattr(settings, 'STOCK_FULL_UPDATE_TIME', '21:00')
    hour, minute = map(int, update_time.split(':'))
except Exception:
    hour, minute = 21, 0

active_interval_minutes = getattr(settings, 'STOCK_ACTIVE_UPDATE_INTERVAL_MINUTES', 15)

celery_app.conf.beat_schedule = {
    'nightly-full-stock-update': {
        'task': 'stock.update_all_prices',
        'schedule': crontab(hour=hour, minute=minute),
    },
    'frequent-active-stock-update': {
        'task': 'stock.update_active_prices',
        'schedule': crontab(minute=f'*/{active_interval_minutes}'),
    },
    'nightly-ml-predictions': {
        'task': 'backend.worker.ml_tasks.generate_predictions',
        'schedule': crontab(hour=(hour + 1) % 24, minute=minute), # Run 1 hour after full update
    }
}

# Custom queues removed so it defaults to the standard 'celery' queue
