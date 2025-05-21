# src/task_management/categories/models.py
"""
This module defines the Category model for organizing tasks.
Categories allow users to group related tasks together.
"""
from src.task_management.db import db
from datetime import datetime

class Category(db.Model):
    """
    Category model for classifying and organizing tasks.
    """
    __tablename__ = "categories"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    color = db.Column(db.String(7), default="#3498db")  # Hex color code
    icon = db.Column(db.String(50), default="folder")    # Icon identifier
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Foreign key to the User model
    user = db.relationship('User', backref=db.backref('user_categories', lazy='dynamic'))
    # Relationships defined using string references to avoid circular imports
    
    def __repr__(self):
        """
        String representation of the Category object.
        """
        return f"<Category {self.name} (ID: {self.id})>"
    
    def to_dict(self):
        """
        Convert the Category object to a dictionary for API responses.
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id,
            'task_count': self.tasks.count() if hasattr(self, 'tasks') else 0
        }
    
    @classmethod
    def get_default_category(cls, user_id):
        """
        Get or create a default category for a user.
        """
        default_category = cls.query.filter_by(
            user_id=user_id, 
            name='Uncategorized'
        ).first()
        
        if not default_category:
            default_category = cls(
                name='Uncategorized',
                description='Default category for uncategorized tasks',
                color='#95a5a6',
                user_id=user_id
            )
            db.session.add(default_category)
            db.session.commit()
            
        return default_category