# src/task_management/integrations/slack.py
import requests
import json
import logging
import os
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


logger = logging.getLogger(__name__)

class SlackNotifier:
    def __init__(self, webhook_url=SLACK_WEBHOOK_URL):
        self.webhook_url = webhook_url
        
    def send_notification(self, message, channel="#task-notifications"):
        """Send a notification to Slack"""
        payload = {
            "channel": channel,
            "text": message,
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def notify_task_created(self, task, assigned_to=None):
        """Notify when a task is created"""
        message = f" New task created: *{task.title}*"
        
        if assigned_to:
            message += f"\nAssigned to: {assigned_to.username}"
            
        message += f"\nPriority: {task.priority}"
        
        if task.due_date:
            message += f"\nDue: {task.due_date.strftime('%Y-%m-%d')}"
            
        return self.send_notification(message)
    
    def notify_task_completed(self, task, completed_by):
        """Notify when a task is marked complete"""
        message = f" Task completed: *{task.title}*"
        message += f"\nCompleted by: {completed_by.username}"
        
        return self.send_notification(message)