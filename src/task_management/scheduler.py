# src/task_management/scheduler.py
"""
Background task scheduler using Celery for Taskflow Manager.
Handles due date reminders, daily summaries, and other background tasks.
"""
import os
import logging
from datetime import datetime, time
from celery import Celery
from celery.schedules import crontab

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery instance
celery = Celery('taskflow')

# Celery configuration
celery.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Celery beat schedule
celery.conf.beat_schedule = {
    'check-due-dates-hourly': {
        'task': 'src.task_management.scheduler.check_due_dates',
        'schedule': crontab(minute=0),  # Every hour at minute 0
    },
    'send-daily-summaries': {
        'task': 'src.task_management.scheduler.send_daily_summaries',
        'schedule': crontab(hour=18, minute=0),  # Daily at 6 PM
    },
    'cleanup-completed-tasks': {
        'task': 'src.task_management.scheduler.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}

def create_celery_app(app):
    """
    Create Celery app with Flask app context.
    Call this from your Flask app factory.
    """
    # Update Celery config with Flask app config
    celery.conf.update(
        broker_url=app.config.get('CELERY_BROKER_URL'),
        result_backend=app.config.get('CELERY_RESULT_BACKEND'),
    )
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    # ADD THIS LINE:
    setup_celery_signals(celery)
    
    return celery

# Background tasks
@celery.task(bind=True, name='src.task_management.scheduler.check_due_dates')
def check_due_dates(self):
    """
    Check for due dates and send reminders.
    Runs every hour to check for overdue, due today, and due tomorrow tasks.
    """
    try:
        logger.info("Starting due date check...")
        
        # Import here to avoid circular imports
        from src.task_management.integration.slack import send_due_date_reminders
        
        # Send due date reminders
        result = send_due_date_reminders()
        
        logger.info(f"Due date check completed: {result}")
        return {"status": "success", "result": result}
        
    except Exception as exc:
        logger.error(f"Due date check failed: {exc}")
        # Retry the task with exponential backoff
        raise self.retry(exc=exc, countdown=60, max_retries=3)

@celery.task(bind=True, name='src.task_management.scheduler.send_daily_summaries')
def send_daily_summaries(self):
    """
    Send daily task summaries to users.
    Runs daily at 6 PM to send productivity summaries.
    """
    try:
        logger.info("Starting daily summary task...")
        
        # Import here to avoid circular imports
        from src.task_management.integration.slack import send_daily_summaries as send_summaries
        
        # Send daily summaries
        result = send_summaries()
        
        logger.info(f"Daily summaries sent: {result}")
        return {"status": "success", "result": result}
        
    except Exception as exc:
        logger.error(f"Daily summary task failed: {exc}")
        # Retry the task with exponential backoff
        raise self.retry(exc=exc, countdown=300, max_retries=2)

@celery.task(bind=True, name='src.task_management.scheduler.send_task_notification')
def send_task_notification(self, notification_type, task_data, user_data, **kwargs):
    """
    Send individual task notifications asynchronously.
    This allows the main application to continue without waiting for Slack API calls.
    """
    try:
        logger.info(f"Sending {notification_type} notification for task {task_data.get('id')}")
        
        # Import here to avoid circular imports
        from src.task_management.integration.slack import SlackService
        
        slack = SlackService()
        
        # Create mock objects for the notification
        class MockTask:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
            
            def to_slack_dict(self):
                return task_data
        
        class MockUser:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
        
        task = MockTask(task_data)
        user = MockUser(user_data)
        
        # Send appropriate notification
        result = False
        if notification_type == 'task_created':
            result = slack.notify_task_created(task, user)
        elif notification_type == 'task_assigned':
            assigned_user = MockUser(kwargs.get('assigned_user_data', {}))
            result = slack.notify_task_assigned(task, assigned_user, user)
        elif notification_type == 'task_completed':
            result = slack.notify_task_completed(task, user)
        elif notification_type == 'task_updated':
            changes = kwargs.get('changes', {})
            result = slack.notify_task_updated(task, user, changes)
        
        logger.info(f"Notification sent successfully: {result}")
        return {"status": "success", "notification_sent": result}
        
    except Exception as exc:
        logger.error(f"Failed to send {notification_type} notification: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=30, max_retries=3)

@celery.task(bind=True, name='src.task_management.scheduler.cleanup_old_data')
def cleanup_old_data(self):
    """
    Clean up old data and optimize database.
    Runs daily at 2 AM to clean up completed tasks older than 90 days.
    """
    try:
        logger.info("Starting data cleanup task...")
        
        # Import here to avoid circular imports
        from src.task_management.tasks.models import Task, TaskHistory
        from src.task_management.db import db
        from datetime import datetime, timedelta
        
        # Archive old completed tasks (older than 90 days)
        cutoff_date = datetime.now() - timedelta(days=90)
        
        old_tasks = Task.query.filter(
            Task.status == 'completed',
            Task.completed_at < cutoff_date
        ).all()
        
        archived_count = 0
        for task in old_tasks:
            task.status = 'archived'
            archived_count += 1
        
        # Clean up old history entries (older than 1 year)
        history_cutoff = datetime.now() - timedelta(days=365)
        old_history = TaskHistory.query.filter(
            TaskHistory.created_at < history_cutoff
        ).delete()
        
        db.session.commit()
        
        result = {
            "archived_tasks": archived_count,
            "deleted_history_entries": old_history,
            "cleanup_date": datetime.now().isoformat()
        }
        
        logger.info(f"Data cleanup completed: {result}")
        return {"status": "success", "result": result}
        
    except Exception as exc:
        logger.error(f"Data cleanup failed: {exc}")
        db.session.rollback()
        raise self.retry(exc=exc, countdown=3600, max_retries=1)  # Retry in 1 hour

@celery.task(bind=True, name='src.task_management.scheduler.send_bulk_notifications')
def send_bulk_notifications(self, notifications):
    """
    Send multiple notifications in batch to improve performance.
    """
    try:
        logger.info(f"Sending {len(notifications)} bulk notifications...")
        
        from src.task_management.integration.slack import SlackService
        
        slack = SlackService()
        results = []
        
        for notification in notifications:
            try:
                # Process each notification
                notification_type = notification.get('type')
                message = notification.get('message')
                channel = notification.get('channel')
                
                result = slack.send_notification(message, channel)
                results.append({"notification": notification, "success": result})
                
            except Exception as e:
                logger.error(f"Failed to send individual notification: {e}")
                results.append({"notification": notification, "success": False, "error": str(e)})
        
        successful = len([r for r in results if r['success']])
        logger.info(f"Bulk notifications completed: {successful}/{len(notifications)} successful")
        
        return {
            "status": "success",
            "total": len(notifications),
            "successful": successful,
            "results": results
        }
        
    except Exception as exc:
        logger.error(f"Bulk notifications failed: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=2)

# Utility functions for easier task scheduling
def schedule_task_notification(notification_type, task, user, **kwargs):
    """
    Schedule a task notification to be sent asynchronously.
    Use this in your route handlers instead of sending notifications directly.
    """
    try:
        # Convert objects to dictionaries for serialization
        task_data = task.to_slack_dict() if hasattr(task, 'to_slack_dict') else task.to_dict()
        user_data = {
            'id': user.id,
            'username': user.username,
            'slack_user_id': getattr(user, 'slack_user_id', None),
            'slack_notifications_enabled': getattr(user, 'slack_notifications_enabled', False),
        }
        
        # Add any additional data
        extra_data = {}
        if 'assigned_user' in kwargs:
            assigned_user = kwargs['assigned_user']
            extra_data['assigned_user_data'] = {
                'id': assigned_user.id,
                'username': assigned_user.username,
                'slack_user_id': getattr(assigned_user, 'slack_user_id', None),
                'slack_notifications_enabled': getattr(assigned_user, 'slack_notifications_enabled', False),
            }
        
        if 'changes' in kwargs:
            extra_data['changes'] = kwargs['changes']
        
        # Schedule the task
        send_task_notification.delay(notification_type, task_data, user_data, **extra_data)
        logger.info(f"Scheduled {notification_type} notification for task {task.id}")
        
    except Exception as e:
        logger.error(f"Failed to schedule {notification_type} notification: {e}")

def schedule_due_date_check():
    """Manually trigger due date check (useful for testing)"""
    return check_due_dates.delay()

def schedule_daily_summary():
    """Manually trigger daily summary (useful for testing)"""
    return send_daily_summaries.delay()

def setup_celery_signals(celery_app):
    """Setup Celery signal handlers"""
    
    @celery_app.task_failure.connect
    def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None):
        """Handle task failures and send alerts if needed"""
        logger.error(f"Task {task_id} failed: {exception}")
        
        # You could send an alert to Slack or email here for critical failures
        if sender and 'critical' in str(sender):
            # Send alert for critical task failures
            pass
    
    @celery_app.task_success.connect
    def task_success_handler(sender=None, result=None, **kwargs):
        """Handle successful task completion"""
        logger.info(f"Task {sender} completed successfully")
# Export the celery instance for the worker
__all__ = ['celery', 'create_celery_app', 'schedule_task_notification']