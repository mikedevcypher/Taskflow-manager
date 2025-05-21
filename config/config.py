# config/config.py
"""
Configuration module for TaskManager application.
This module provides configuration for different environments: development, testing, and production.
It includes settings for database, Redis caching, security, and third-party integrations.
"""
import os
from datetime import timedelta

class Config(object):
    """
    Base configuration class with common settings used by all environments.
    """
    # Application settings
    APP_NAME = 'Taskflow'
    APP_VERSION = '1.0.0'
   
    
    # Security settings
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    
    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Default PostgreSQL URI
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI', 
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    
    # Redis settings
    REDIS_URL = os.getenv('REDIS_URL')
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    }
    
    # Session settings
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_USE_SIGNER = True
    SESSION_REDIS = None  # Will be set in init_app
    
    # Password hashing
    BCRYPT_LOG_ROUNDS = 13
    
    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "1000 per day, 100 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # Slack integration
    SLACK_ENABLED = os.getenv('SLACK_ENABLED', 'false').lower() == 'true'
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')
    SLACK_API_TOKEN = os.getenv('SLACK_API_TOKEN', '')
    SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', '#task-notifications')
    

    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload


class Development(Config):
    """
    Development environment configuration.
    """
    DEBUG = True
    TESTING = False
    ENV = 'development'
    
    # Less strict security for development
    WTF_CSRF_ENABLED = False
    BCRYPT_LOG_ROUNDS = 4  # Faster hashing for development
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    
    # Enable debug toolbar if installed
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False


class Testing(Config):
    """
    Testing environment configuration.
    """
    DEBUG = False
    TESTING = True
    ENV = 'testing'
    
    # Use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URI', 'sqlite:///:memory:')
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Use faster hashing for tests
    BCRYPT_LOG_ROUNDS = 4
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False
    
    # Use memory cache for tests
    CACHE_TYPE = 'simple'
    
    # Logging
    LOG_LEVEL = 'DEBUG'


class Production(Config):
    """
    Production environment configuration.
    """
    DEBUG = False
    TESTING = False
    ENV = 'production'
    
    # Use provided PostgreSQL URI for production
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI',
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}"
    )
    
    # Stricter security settings for production
    WTF_CSRF_ENABLED = True
    BCRYPT_LOG_ROUNDS = 13
    
    # Use secure cookies in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # HTTPS settings
    PREFERRED_URL_SCHEME = 'https'
    
    # Logging
    LOG_LEVEL = 'ERROR'
    
    # Add Content-Security-Policy for production
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; media-src 'self'; frame-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
    }


# Dictionary to map environment names to configuration classes
config_by_name = {
    'development': Development,
    'testing': Testing,
    'production': Production,
    'default': Development
}

# Function to get configuration by name
def get_config(config_name=None):
    """
    Get the configuration class based on the environment name.
    """
    if not config_name:
        config_name = os.getenv('FLASK_ENV', 'default')
    return config_by_name.get(config_name, Development)