# src/task_management/db.py
"""
Database configuration module for TaskFlow.
This module initializes SQLAlchemy, Migrate, and Redis for caching.
It also provides helper functions for database operations and indexing.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import redis
import os
import logging

from src.task_management.auth.models import User
from src.task_management.categories.models import Category
        

# Initialize SQLAlchemy
db = SQLAlchemy()
migrate = None  # Declaring migration

# Initialize Redis client
redis_client = None

logger = logging.getLogger(__name__)

def init_app(app):
    """
    Initialize database and migration with the Flask app.
    """
    global migrate, redis_client
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    # Initialize Redis client for caching if configured
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    try:
        redis_client = redis.from_url(redis_url)
        # Test the connection
        redis_client.ping()
        logger.info("Redis connection established successfully")
    except redis.ConnectionError:
        logger.warning("Redis connection failed - caching will be disabled")
        redis_client = None
    
    # Register database commands with the CLI
    register_commands(app)

def register_commands(app):
    """
    Register database commands with the Flask CLI.
    """
    @app.cli.command("create-db")
    def create_db():
        """Create database tables from SQLAlchemy models."""
        db.create_all()
        print("Database tables created.")
    
    @app.cli.command("drop-db")
    def drop_db():
        """Drop all database tables."""
        if input("Are you sure you want to drop all tables? (y/N): ").lower() == 'y':
            db.drop_all()
            print("Database tables dropped.")
        else:
            print("Operation cancelled.")
    
    @app.cli.command("seed-db")
    def seed_db():
        """Seed the database with initial data."""
       
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(username="admin", email_id="admin@taskflow.com", role="admin")
            admin.create_password("admin123")  # In production, use a secure password
            db.session.add(admin)
            
            # Create default categories
            categories = [
                Category(name="Work", description="Work-related tasks", color="#e74c3c", user_id=1),
                Category(name="Personal", description="Personal tasks", color="#3498db", user_id=1),
                Category(name="Urgent", description="Urgent tasks", color="#e67e22", user_id=1),
                Category(name="Uncategorized", description="Default category", color="#95a5a6", user_id=1)
            ]
            db.session.bulk_save_objects(categories)
            
            db.session.commit()
            print("Database seeded with initial data.")
        else:
            print("Admin user already exists, skipping seeding.")

def optimize_query(query, model, page=1, per_page=20, **filters):
    """
    Optimize a database query with filtering, pagination, and caching.
    """
    # Apply filters
    for key, value in filters.items():
        if value is not None:
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    # Execute query
    results = query.all()
    
    # Calculate if there are more pages
    has_next = (page * per_page) < total_count
    
    return results, total_count, has_next

def check_redis():
    """
    Check if Redis is available.
    """
    if redis_client is None:
        return False
    
    try:
        redis_client.ping()
        return True
    except redis.ConnectionError:
        return False

def clear_cache(pattern='*'):
    """
    Clear cache entries matching the pattern.
    """
    if not check_redis():
        return 0
    
    keys = redis_client.keys(pattern)
    if keys:
        return redis_client.delete(*keys)
    return 0