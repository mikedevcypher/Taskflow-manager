# src/task_management/tasks/models.py
"""
This model is used to represent fields for task management,
including title, description, due date, priority, status, category, and assignee.
The model includes database indexing for performance optimization and Slack integration support.
"""
from sqlalchemy import Index
from sqlalchemy.orm import relationship
from ..db import db
from datetime import datetime

class Task(db.Model):
    """
    Task model to represent a task in the task management system.
    Enhanced with Slack integration fields and assignment tracking.
    """
    __tablename__ = "tasks"
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic task information (existing fields preserved)
    title = db.Column(db.String(200), nullable=False)  # Increased from 140 to 200
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="medium")  # low, medium, high, critical
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending, in-progress, completed, archived
    
    # User relationships (existing preserved + enhanced)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # NEW: Who created the task
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # NEW: Who is assigned to the task
    
    # Category relationship (existing preserved)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True, index=True)
    
    # Timestamps (existing preserved)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # NEW: Task completion tracking
    completed_at = db.Column(db.DateTime, nullable=True)
    completed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # NEW: Slack integration fields
    slack_thread_ts = db.Column(db.String(50), nullable=True)  # Slack thread timestamp for updates
    slack_channel_id = db.Column(db.String(50), nullable=True)  # Channel where task was discussed
    slack_message_ts = db.Column(db.String(50), nullable=True)  # Original message timestamp
    
    # NEW: Task metadata
    estimated_hours = db.Column(db.Float, nullable=True)  # Estimated time to complete
    actual_hours = db.Column(db.Float, nullable=True)     # Actual time spent
    tags = db.Column(db.String(500), nullable=True)       # Comma-separated tags
    
    # Relationships (existing preserved + enhanced)
    # Main user relationship (task owner)
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('user_tasks', lazy='dynamic'))
    
    # Category relationship (existing preserved)
    category = db.relationship('Category', foreign_keys=[category_id], backref=db.backref('category_tasks', lazy='dynamic'))
    
    # NEW: Enhanced user relationships
    creator = relationship('User', foreign_keys=[created_by_id], backref='created_tasks')
    assignee = relationship('User', foreign_keys=[assigned_to_id], backref='assigned_tasks')
    completed_by = relationship('User', foreign_keys=[completed_by_id], backref='completed_tasks')
    
    # Enhanced indexes for performance optimization (existing + new)
    __table_args__ = (
        # Existing indexes preserved
        Index('idx_task_status', status),
        Index('idx_task_due_date', due_date),
        Index('idx_task_priority', priority),
        Index('idx_task_user_status', user_id, status),
        Index('idx_task_category_status', category_id, status),
        
        # NEW: Enhanced indexes for Slack integration and assignment tracking
        Index('idx_task_assigned_to_id', assigned_to_id),
        Index('idx_task_created_by_id', created_by_id),
        Index('idx_task_completed_by_id', completed_by_id),
        Index('idx_task_status_priority', status, priority),
        Index('idx_task_due_date_status', due_date, status),
        Index('idx_task_slack_thread', slack_thread_ts),
        Index('idx_task_assignee_status', assigned_to_id, status),
    )
    
    def __repr__(self):
        """
        String representation of the Task object.
        """
        return f"<Task {self.id}: {self.title}>"
    
    def to_dict(self):
        """
        Convert the Task object to a dictionary for API responses.
        Enhanced with new Slack and assignment fields.
        """
        return {
            # Existing fields preserved
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "priority": self.priority,
            "status": self.status,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            
            # Enhanced category information (existing preserved)
            "category": {
                "id": self.category.id,
                "name": self.category.name,
                "color": self.category.color
            } if self.category else None,
            
            # NEW: Enhanced fields
            "created_by_id": self.created_by_id,
            "assigned_to_id": self.assigned_to_id,
            "completed_by_id": self.completed_by_id,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "tags": self.tags.split(',') if self.tags else [],
            
            # NEW: Slack integration fields
            "slack_thread_ts": self.slack_thread_ts,
            "slack_channel_id": self.slack_channel_id,
            "slack_message_ts": self.slack_message_ts,
            
            # NEW: Include related object names for easier frontend display
            "creator_name": self.creator.username if self.creator else None,
            "assignee_name": self.assignee.username if self.assignee else None,
            "completed_by_name": self.completed_by.username if self.completed_by else None,
        }
    
    def to_slack_dict(self):
        """
        NEW: Convert task to dictionary optimized for Slack notifications.
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description[:200] + '...' if self.description and len(self.description) > 200 else self.description,
            'due_date': self.due_date.strftime('%B %d, %Y') if self.due_date else None,
            'priority': self.priority.upper(),
            'status': self.status.replace('_', ' ').title(),
            'assignee_name': self.assignee.username if self.assignee else 'Unassigned',
            'creator_name': self.creator.username if self.creator else 'Unknown',
            'category_name': self.category.name if self.category else 'Uncategorized',
            'is_overdue': self.due_date < datetime.now() if self.due_date else False,
            'is_high_priority': self.priority.lower() in ['high', 'critical'],
        }
    
    # Existing static methods preserved
    @staticmethod
    def get_tasks_by_status(user_id, status=None):
        """
        Get tasks filtered by status.
        """
        query = Task.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Task.due_date.asc())
    
    @staticmethod
    def get_tasks_by_category(user_id, category_id):
        """
        Get tasks filtered by category.
        """
        return Task.query.filter_by(user_id=user_id, category_id=category_id).order_by(Task.due_date.asc())
    
    @staticmethod
    def get_tasks_by_priority(user_id, priority):
        """
        Get tasks filtered by priority.
        """
        return Task.query.filter_by(user_id=user_id, priority=priority).order_by(Task.due_date.asc())
    
    @staticmethod
    def get_overdue_tasks(user_id):
        """
        Get overdue tasks for a user.
        """
        return Task.query.filter_by(user_id=user_id).filter(
            Task.due_date < datetime.utcnow(),
            Task.status != 'completed'
        ).order_by(Task.due_date.asc())
    
    # Existing method preserved + enhanced
    def complete(self):
        """
        Mark a task as completed.
        Enhanced with completion tracking.
        """
        self.status = 'completed'
        self.completed_at = datetime.utcnow()  # NEW: Track completion time
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    # NEW: Property methods for enhanced functionality
    @property
    def is_overdue(self):
        """Check if task is overdue."""
        if not self.due_date or self.status == 'completed':
            return False
        return self.due_date < datetime.now()
    
    @property
    def is_due_today(self):
        """Check if task is due today."""
        if not self.due_date:
            return False
        return self.due_date.date() == datetime.now().date()
    
    @property
    def is_due_tomorrow(self):
        """Check if task is due tomorrow."""
        if not self.due_date:
            return False
        from datetime import timedelta
        tomorrow = datetime.now().date() + timedelta(days=1)
        return self.due_date.date() == tomorrow
    
    @property
    def priority_weight(self):
        """Get numeric weight for priority (for sorting)."""
        weights = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        return weights.get(self.priority.lower(), 2)
    
    @property
    def status_weight(self):
        """Get numeric weight for status (for sorting)."""
        weights = {
            'pending': 1,
            'in-progress': 2,
            'completed': 3,
            'archived': 4
        }
        return weights.get(self.status.lower(), 1)
    
    # NEW: Tag management methods
    def add_tag(self, tag):
        """Add a tag to the task."""
        if not self.tags:
            self.tags = tag
        else:
            current_tags = self.tags.split(',')
            if tag not in current_tags:
                current_tags.append(tag)
                self.tags = ','.join(current_tags)
    
    def remove_tag(self, tag):
        """Remove a tag from the task."""
        if self.tags:
            current_tags = self.tags.split(',')
            if tag in current_tags:
                current_tags.remove(tag)
                self.tags = ','.join(current_tags) if current_tags else None
    
    def get_tags(self):
        """Get list of tags."""
        return self.tags.split(',') if self.tags else []
    
    # NEW: Slack integration methods
    def update_slack_thread(self, thread_ts, channel_id=None, message_ts=None):
        """Update Slack thread information for this task."""
        self.slack_thread_ts = thread_ts
        if channel_id:
            self.slack_channel_id = channel_id
        if message_ts:
            self.slack_message_ts = message_ts
    
    # NEW: Time tracking methods
    def get_time_stats(self):
        """Get time-related statistics for the task."""
        stats = {
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'is_over_estimate': False,
            'efficiency_ratio': None
        }
        
        if self.estimated_hours and self.actual_hours:
            stats['is_over_estimate'] = self.actual_hours > self.estimated_hours
            stats['efficiency_ratio'] = self.estimated_hours / self.actual_hours
        
        return stats
    
    # NEW: Enhanced class methods for analytics
    @classmethod
    def get_user_stats(cls, user_id, date_range=None):
        """Get task statistics for a user."""
        query = cls.query.filter_by(user_id=user_id)
        
        if date_range:
            start_date, end_date = date_range
            query = query.filter(cls.created_at.between(start_date, end_date))
        
        tasks = query.all()
        
        stats = {
            'total': len(tasks),
            'completed': len([t for t in tasks if t.status == 'completed']),
            'pending': len([t for t in tasks if t.status == 'pending']),
            'in_progress': len([t for t in tasks if t.status == 'in-progress']),
            'overdue': len([t for t in tasks if t.is_overdue]),
            'due_today': len([t for t in tasks if t.is_due_today]),
            'due_tomorrow': len([t for t in tasks if t.is_due_tomorrow]),
            'high_priority': len([t for t in tasks if t.priority.lower() in ['high', 'critical']]),
        }
        
        # Calculate completion rate
        if stats['total'] > 0:
            stats['completion_rate'] = (stats['completed'] / stats['total']) * 100
        else:
            stats['completion_rate'] = 0
        
        return stats
    
    @classmethod
    def get_due_date_reminders(cls, user_id=None, reminder_type='today'):
        """Get tasks that need due date reminders."""
        query = cls.query.filter(cls.status != 'completed')
        
        if user_id:
            query = query.filter_by(assigned_to_id=user_id)
        
        today = datetime.now().date()
        
        if reminder_type == 'overdue':
            query = query.filter(cls.due_date < today)
        elif reminder_type == 'today':
            query = query.filter(db.func.date(cls.due_date) == today)
        elif reminder_type == 'tomorrow':
            from datetime import timedelta
            tomorrow = today + timedelta(days=1)
            query = query.filter(db.func.date(cls.due_date) == tomorrow)
        elif reminder_type == 'this_week':
            from datetime import timedelta
            week_end = today + timedelta(days=7)
            query = query.filter(cls.due_date.between(today, week_end))
        
        return query.all()
    
    # NEW: Enhanced assignment methods
    @classmethod
    def get_assigned_tasks(cls, user_id, status=None):
        """Get tasks assigned to a specific user."""
        query = cls.query.filter_by(assigned_to_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.due_date.asc())
    
    @classmethod
    def get_created_tasks(cls, user_id, status=None):
        """Get tasks created by a specific user."""
        query = cls.query.filter_by(created_by_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.created_at.desc())
    
    def __init__(self, **kwargs):
        """Initialize task with default values."""
        super(Task, self).__init__(**kwargs)
        
        # Set default assigned_to_id to user_id if not provided
        if not self.assigned_to_id and self.user_id:
            self.assigned_to_id = self.user_id
        
        # Set default created_by_id to user_id if not provided
        if not self.created_by_id and self.user_id:
            self.created_by_id = self.user_id

# NEW: Task History model for tracking changes
class TaskHistory(db.Model):
    """
    Model for tracking task changes and audit trail.
    """
    __tablename__ = 'task_history'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Change tracking
    action = db.Column(db.String(50), nullable=False)  # created, updated, completed, deleted
    field_name = db.Column(db.String(50), nullable=True)  # Which field was changed
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    
    # Slack integration
    slack_notified = db.Column(db.Boolean, default=False)
    slack_thread_ts = db.Column(db.String(50), nullable=True)
    
    # Relationships
    task = relationship('Task', backref='history')
    user = relationship('User', backref='task_actions')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_task_history_task_id', task_id),
        Index('idx_task_history_user_id', user_id),
        Index('idx_task_history_created_at', created_at),
    )
    
    def __repr__(self):
        return f'<TaskHistory {self.id}: {self.action} on Task {self.task_id}>'
    
    def to_dict(self):
        """Convert history entry to dictionary."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'action': self.action,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_name': self.user.username if self.user else None,
            'slack_notified': self.slack_notified
        }
    
    @classmethod
    def log_change(cls, task_id, user_id, action, field_name=None, old_value=None, new_value=None, **kwargs):
        """Log a task change."""
        history = cls(
            task_id=task_id,
            user_id=user_id,
            action=action,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent')
        )
        
        db.session.add(history)
        return history

# NEW: Task Comment model for discussion tracking
class TaskComment(db.Model):
    """
    Model for task comments and discussions.
    """
    __tablename__ = 'task_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Comment content
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Slack integration
    slack_thread_ts = db.Column(db.String(50), nullable=True)
    slack_message_ts = db.Column(db.String(50), nullable=True)
    
    # Relationships
    task = relationship('Task', backref='comments')
    user = relationship('User', backref='task_comments')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_task_comments_task_id', task_id),
        Index('idx_task_comments_user_id', user_id),
    )
    
    def __repr__(self):
        return f'<TaskComment {self.id} on Task {self.task_id}>'
    
    def to_dict(self):
        """Convert comment to dictionary."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_name': self.user.username if self.user else None,
            'slack_thread_ts': self.slack_thread_ts,
            'slack_message_ts': self.slack_message_ts
        }