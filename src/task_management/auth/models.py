# src/task_management/auth/models.py
"""
This model represents users in the TaskFlow application and provides 
fields for authentication, user roles, and security features.
"""
from flask_login import UserMixin
from ..db import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import os
from typing import Optional

class User(UserMixin, db.Model):
    """
    User model for storing user information and handling authentication
    """
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), index=True, unique=True, nullable=False)
    email_id = db.Column(db.String(128), index=True, unique=True, nullable=False)
    # Increase password field length to accommodate modern hash algorithms
    password = db.Column(db.String(512), nullable=False)  # Increased from 128 to 512
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    role = db.Column(db.String(20), default="user")  # Options: admin, manager, user
    is_active = db.Column(db.Boolean, default=True)
    

    def __repr__(self):
        """
        Standard python Method to return a string representation of the user object.
        """
        return f"<User {self.username}:{self.email_id}>"
    
    def create_password(self, password):
        """
        Method to generate and set the password hash from the provided password.
        """
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        """
        Method to check if the provided password matches the stored password hash.

        """
        return check_password_hash(self.password, password)
    
    def generate_jwt_token(self, expires_delta: Optional[timedelta] = None) -> str:
        """
        Generate a JWT token for the user with configurable expiration.

        """
        if expires_delta is None:
            expires_delta = timedelta(hours=24)
            
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": self.email_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "user_id": self.id,
            "username": self.username,
            "role": self.role
        }
        
        # Use environment variable for secret key in production
        secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
        
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    @staticmethod
    def verify_jwt_token(token: str) -> dict:
        """
        Verify and decode a JWT token.
        """
        secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    
    def update_last_login(self):
        """
        Update the last_login timestamp for the user.
        """
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def is_admin(self):
        """
        Check if the user has admin role.
        """
        return self.role == "admin"
    
    def is_manager(self):
        """
        Check if the user has manager role.
        """
        return self.role == "manager"