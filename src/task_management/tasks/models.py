# src/task_management/tasks/models.py
"""
This model is used to represent fields for task management,
including title, description, due date, priority, status, category, and assignee.
The model includes database indexing for performance optimization.
"""
from sqlalchemy import Index
from ..db import db
from datetime import datetime

class Task(db.Model):
    """
    Task model to represent a task in the task management system.
    """
    __tablename__ = "tasks"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="medium")  # low, medium, high
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending, in-progress, completed
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships defined using string references to avoid circular imports
    user = db.relationship('User', backref=db.backref('user_tasks', lazy='dynamic'))
    category = db.relationship('Category', backref=db.backref('category_tasks', lazy='dynamic'))
    
    # Indexes for performance optimization
    __table_args__ = (
        Index('idx_task_status', status),
        Index('idx_task_due_date', due_date),
        Index('idx_task_priority', priority),
        Index('idx_task_user_status', user_id, status),
        Index('idx_task_category_status', category_id, status),
    )
    
    def __repr__(self):
        """
        String representation of the Task object.
        """
        return f"<Task {self.id}: {self.title}>"
    
    def to_dict(self):
        """
        Convert the Task object to a dictionary for API responses.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "priority": self.priority,
            "status": self.status,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "category": {
                "id": self.category.id,
                "name": self.category.name,
                "color": self.category.color
            } if self.category else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
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
    
    def complete(self):
        """
        Mark a task as completed.
        """
        self.status = 'completed'
        self.updated_at = datetime.utcnow()
        db.session.commit()