# src/task_management/integrations/slack.py
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config.config import Config

logger = logging.getLogger(__name__)

class SlackService:
    """
    Slack integration service for Taskflow Manager
    
    """
    
    def __init__(self, 
                 bot_token: str = None, 
                 webhook_url: str = None,
                 signing_secret: str = None):
        self.bot_token = bot_token or Config.SLACK_BOT_TOKEN
        self.webhook_url = webhook_url or Config.SLACK_WEBHOOK_URL
        self.signing_secret = signing_secret or Config.SLACK_SIGNING_SECRET
        
        # Initialize Slack client if bot token is provided
        if self.bot_token:
            self.client = WebClient(token=self.bot_token)
        else:
            self.client = None
            
        self.default_channel = Config.SLACK_DEFAULT_CHANNEL or "#task-notifications"
    
    def _send_webhook_message(self, message: str, channel: str = None) -> bool:
        """Send message using incoming webhook"""
        if not self.webhook_url:
            logger.error("Slack webhook URL not configured")
            return False
            
        payload = {
            "channel": channel or self.default_channel,
            "text": message,
            "username": "Taskflow Bot",
            "icon_emoji": ":clipboard:"
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Webhook message sent successfully to {channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to send webhook message: {e}")
            return False
    
    def _send_bot_message(self, 
                         message: str = None, 
                         blocks: List[Dict] = None,
                         channel: str = None,
                         attachments: List[Dict] = None) -> bool:
        """Send message using Bot API with rich formatting"""
        if not self.client:
            logger.error("Slack bot client not initialized")
            return False
            
        try:
            response = self.client.chat_postMessage(
                channel=channel or self.default_channel,
                text=message,
                blocks=blocks,
                attachments=attachments
            )
            logger.info(f"Bot message sent successfully to {channel}")
            return True
        except SlackApiError as e:
            logger.error(f"Failed to send bot message: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending bot message: {e}")
            return False
    
    def send_notification(self, 
                         message: str, 
                         channel: str = None,
                         blocks: List[Dict] = None,
                         use_bot: bool = True) -> bool:
        """
        Send notification with fallback between bot and webhook
        """
        channel = channel or self.default_channel
        
        if use_bot and self.client:
            return self._send_bot_message(message, blocks, channel)
        else:
            return self._send_webhook_message(message, channel)
    
    # Task Assignment Notifications
    def notify_task_assigned(self, task, assigned_to, assigned_by, channel: str = None) -> bool:
        """Notify when a task is assigned to someone"""
        
        # Rich blocks for bot API
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📋 Task Assigned"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Task:* {task.title}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Assigned to:* <@{assigned_to.slack_user_id or assigned_to.username}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Assigned by:* {assigned_by.username}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:* {task.priority.upper()}"
                    }
                ]
            }
        ]
        
        if task.due_date:
            blocks[1]["fields"].append({
                "type": "mrkdwn",
                "text": f"*Due Date:* {task.due_date.strftime('%B %d, %Y')}"
            })
        
        if task.description:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:* {task.description[:500]}{'...' if len(task.description) > 500 else ''}"
                }
            })
        
        # Add action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Task"
                    },
                    "url": f"{Config.FRONTEND_URL}/tasks/{task.id}",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Mark Complete"
                    },
                    "value": f"complete_task_{task.id}",
                    "action_id": "complete_task"
                }
            ]
        })
        
        # Fallback message for webhook
        fallback_message = (
            f"📋 *Task Assigned*\n"
            f"Task: {task.title}\n"
            f"Assigned to: {assigned_to.username}\n"
            f"Assigned by: {assigned_by.username}\n"
            f"Priority: {task.priority.upper()}"
        )
        
        if task.due_date:
            fallback_message += f"\nDue: {task.due_date.strftime('%Y-%m-%d')}"
        
        return self.send_notification(fallback_message, channel, blocks)
    
    # Due Date Reminders
    def notify_due_date_reminder(self, tasks: List, user, reminder_type: str = "today") -> bool:
        """Send due date reminders"""
        
        if not tasks:
            return True
        
        emoji_map = {
            "overdue": "🚨",
            "today": "⏰", 
            "tomorrow": "📅",
            "this_week": "📆"
        }
        
        title_map = {
            "overdue": "Overdue Tasks",
            "today": "Tasks Due Today",
            "tomorrow": "Tasks Due Tomorrow", 
            "this_week": "Tasks Due This Week"
        }
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji_map.get(reminder_type, '📋')} {title_map.get(reminder_type, 'Task Reminder')}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hey <@{user.slack_user_id or user.username}>! You have {len(tasks)} task(s) that need attention:"
                }
            }
        ]
        
        # Add task list
        task_list = []
        for task in tasks[:10]:  # Limit to 10 tasks to avoid message size limits
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority.lower(), "⚪")
            due_str = task.due_date.strftime('%m/%d') if task.due_date else "No due date"
            task_list.append(f"{priority_emoji} *{task.title}* (Due: {due_str})")
        
        if len(tasks) > 10:
            task_list.append(f"...and {len(tasks) - 10} more tasks")
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(task_list)
            }
        })
        
        # Add action button
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View All Tasks"
                    },
                    "url": f"{Config.FRONTEND_URL}/tasks?filter={reminder_type}",
                    "style": "primary"
                }
            ]
        })
        
        # Fallback message
        fallback_message = (
            f"{emoji_map.get(reminder_type, '📋')} *{title_map.get(reminder_type, 'Task Reminder')}*\n"
            f"You have {len(tasks)} task(s) that need attention.\n"
            f"View them at: {Config.FRONTEND_URL}/tasks"
        )
        
        # Send to user's DM if possible, otherwise default channel
        channel = f"@{user.slack_user_id or user.username}" if user.slack_user_id else None
        
        return self.send_notification(fallback_message, channel, blocks)
    
    # Task Completion Alerts
    def notify_task_completed(self, task, completed_by, channel: str = None) -> bool:
        """Notify when a task is completed"""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✅ Task Completed"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Task:* {task.title}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Completed by:* <@{completed_by.slack_user_id or completed_by.username}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:* {task.priority.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Completed:* {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
                    }
                ]
            }
        ]
        
        # Add celebration for high priority tasks
        if task.priority.lower() == "high":
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🎉 Great job completing this high-priority task!"
                }
            })
        
        fallback_message = (
            f"✅ *Task Completed*\n"
            f"Task: {task.title}\n"
            f"Completed by: {completed_by.username}\n"
            f"Priority: {task.priority.upper()}"
        )
        
        return self.send_notification(fallback_message, channel, blocks)
    
    # Additional Notification Types
    def notify_task_created(self, task, created_by, channel: str = None) -> bool:
        """Notify when a new task is created"""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🆕 New Task Created"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Task:* {task.title}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Created by:* {created_by.username}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:* {task.priority.upper()}"
                    }
                ]
            }
        ]
        
        if task.due_date:
            blocks[1]["fields"].append({
                "type": "mrkdwn",
                "text": f"*Due Date:* {task.due_date.strftime('%B %d, %Y')}"
            })
        
        fallback_message = (
            f"🆕 *New Task Created*\n"
            f"Task: {task.title}\n"
            f"Created by: {created_by.username}\n"
            f"Priority: {task.priority.upper()}"
        )
        
        return self.send_notification(fallback_message, channel, blocks)
    
    def notify_task_updated(self, task, updated_by, changes: Dict, channel: str = None) -> bool:
        """Notify when a task is updated"""
        
        if not changes:
            return True
        
        change_list = []
        for field, (old_val, new_val) in changes.items():
            change_list.append(f"*{field.title()}:* {old_val} → {new_val}")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📝 Task Updated"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Task:* {task.title}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Updated by:* {updated_by.username}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Changes:*\n" + "\n".join(change_list)
                }
            }
        ]
        
        fallback_message = (
            f"📝 *Task Updated*\n"
            f"Task: {task.title}\n"
            f"Updated by: {updated_by.username}\n"
            f"Changes: {', '.join([f'{k}: {v[0]} → {v[1]}' for k, v in changes.items()])}"
        )
        
        return self.send_notification(fallback_message, channel, blocks)
    
    def notify_daily_summary(self, user, stats: Dict, channel: str = None) -> bool:
        """Send daily task summary"""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Daily Task Summary"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Here's your task summary for {datetime.now().strftime('%B %d, %Y')}:"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Completed:* {stats.get('completed', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Pending:* {stats.get('pending', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Overdue:* {stats.get('overdue', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Created Today:* {stats.get('created_today', 0)}"
                    }
                ]
            }
        ]
        
        # Add motivational message based on performance
        if stats.get('completed', 0) > 0:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🎉 Great job completing {stats['completed']} task(s) today!"
                }
            })
        
        fallback_message = (
            f"📊 *Daily Task Summary for {datetime.now().strftime('%B %d, %Y')}*\n"
            f"Completed: {stats.get('completed', 0)}\n"
            f"Pending: {stats.get('pending', 0)}\n"
            f"Overdue: {stats.get('overdue', 0)}\n"
            f"Created Today: {stats.get('created_today', 0)}"
        )
        
        # Send to user's DM
        channel = f"@{user.slack_user_id or user.username}" if user.slack_user_id else channel
        
        return self.send_notification(fallback_message, channel, blocks)
    
    # Slack Command Handlers
    def handle_slack_command(self, command: str, text: str, user_id: str, channel_id: str) -> Dict:
        """Handle incoming slash commands"""
        
        try:
            if command == "/task":
                return self._handle_task_command(text, user_id, channel_id)
            elif command == "/taskstatus":
                return self._handle_status_command(user_id, channel_id)
            else:
                return {
                    "response_type": "ephemeral",
                    "text": f"Unknown command: {command}"
                }
        except Exception as e:
            logger.error(f"Error handling Slack command {command}: {e}")
            return {
                "response_type": "ephemeral",
                "text": "Sorry, there was an error processing your command."
            }
    
    def _handle_task_command(self, text: str, user_id: str, channel_id: str) -> Dict:
        """Handle /task command"""
        
        if not text.strip():
            return {
                "response_type": "ephemeral",
                "text": "Usage: `/task create \"Task title\" priority:high due:tomorrow`"
            }
        
        parts = text.split()
        action = parts[0].lower() if parts else ""
        
        if action == "create":
            # Parse task creation from Slack
            # This would integrate with your task creation API
            return {
                "response_type": "in_channel",
                "text": f"📋 Task creation requested by <@{user_id}>",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Task creation form would be displayed here..."
                        }
                    }
                ]
            }
        elif action == "list":
            return {
                "response_type": "ephemeral",
                "text": f"Your task list would be displayed here...\nView all tasks: {Config.FRONTEND_URL}/tasks"
            }
        else:
            return {
                "response_type": "ephemeral",
                "text": "Available actions: create, list\nExample: `/task create \"Review code\" priority:high`"
            }
    
    def _handle_status_command(self, user_id: str, channel_id: str) -> Dict:
        """Handle /taskstatus command"""
        
        # This would fetch actual user stats from your database
        return {
            "response_type": "ephemeral",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Your Task Status"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Pending:* 5"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*In Progress:* 3"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Completed Today:* 2"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Overdue:* 1"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View All Tasks"
                            },
                            "url": f"{Config.FRONTEND_URL}/tasks",
                            "style": "primary"
                        }
                    ]
                }
            ]
        }
    
    # Interactive Component Handlers
    def handle_interactive_component(self, payload: Dict) -> Dict:
        """Handle button clicks and other interactive components"""
        
        action_id = payload.get("actions", [{}])[0].get("action_id")
        
        if action_id == "complete_task":
            task_id = payload.get("actions", [{}])[0].get("value", "").replace("complete_task_", "")
            # Here you would call your task completion API
            return {
                "response_type": "ephemeral",
                "text": f"Task {task_id} marked as complete! ✅"
            }
        
        return {
            "response_type": "ephemeral",
            "text": "Action processed."
        }

# Utility functions for background tasks
def send_due_date_reminders():
    """Background task to send due date reminders"""
    from src.task_management.tasks.models import Task
    from src.task_management.auth.models import User
    from datetime import datetime, timedelta
    
    slack = SlackService()
    
    # Get tasks due today, tomorrow, and overdue
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Overdue tasks
    overdue_tasks = Task.query.filter(
        Task.due_date < today,
        Task.status != 'completed'
    ).all()
    
    # Tasks due today
    today_tasks = Task.query.filter(
        Task.due_date == today,
        Task.status != 'completed'
    ).all()
    
    # Tasks due tomorrow
    tomorrow_tasks = Task.query.filter(
        Task.due_date == tomorrow,
        Task.status != 'completed'
    ).all()
    
    # Group by user and send reminders
    user_tasks = {}
    
    for task in overdue_tasks:
        if task.assigned_to_id not in user_tasks:
            user_tasks[task.assigned_to_id] = {"overdue": [], "today": [], "tomorrow": []}
        user_tasks[task.assigned_to_id]["overdue"].append(task)
    
    for task in today_tasks:
        if task.assigned_to_id not in user_tasks:
            user_tasks[task.assigned_to_id] = {"overdue": [], "today": [], "tomorrow": []}
        user_tasks[task.assigned_to_id]["today"].append(task)
    
    for task in tomorrow_tasks:
        if task.assigned_to_id not in user_tasks:
            user_tasks[task.assigned_to_id] = {"overdue": [], "today": [], "tomorrow": []}
        user_tasks[task.assigned_to_id]["tomorrow"].append(task)
    
    # Send reminders
    for user_id, tasks in user_tasks.items():
        user = User.query.get(user_id)
        if user and user.slack_notifications_enabled:
            
            if tasks["overdue"]:
                slack.notify_due_date_reminder(tasks["overdue"], user, "overdue")
            
            if tasks["today"]:
                slack.notify_due_date_reminder(tasks["today"], user, "today")
            
            if tasks["tomorrow"]:
                slack.notify_due_date_reminder(tasks["tomorrow"], user, "tomorrow")

def send_daily_summaries():
    """Background task to send daily task summaries"""
    from src.task_management.tasks.models import Task
    from src.task_management.auth.models import User
    from datetime import datetime, timedelta
    
    slack = SlackService()
    today = datetime.now().date()
    
    users = User.query.filter_by(slack_notifications_enabled=True).all()
    
    for user in users:
        # Calculate user stats
        stats = {
            "completed": Task.query.filter(
                Task.assigned_to_id == user.id,
                Task.status == 'completed',
                Task.updated_at >= today
            ).count(),
            "pending": Task.query.filter(
                Task.assigned_to_id == user.id,
                Task.status.in_(['pending', 'in_progress'])
            ).count(),
            "overdue": Task.query.filter(
                Task.assigned_to_id == user.id,
                Task.due_date < today,
                Task.status != 'completed'
            ).count(),
            "created_today": Task.query.filter(
                Task.created_by_id == user.id,
                Task.created_at >= today
            ).count()
        }
        
        slack.notify_daily_summary(user, stats)