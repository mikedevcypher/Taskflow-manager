# src/main.py
"""
Main application module for TaskFlow.
This module initializes the Flask application with all necessary extensions
and registers blueprints for the different modules.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import Flask, flash, redirect, url_for, send_from_directory, request, jsonify, render_template, current_app
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
from flask_talisman import Talisman
from src.task_management.db import db, init_app as init_db, check_redis

#from src.task_management.auth.models import User
from src.task_management.auth.routes import auth_bp
from src.task_management.tasks.routes import task_bp

from src.task_management.categories.views import categories_bp
from src.task_management.integration.slack import SlackNotifier
from src.task_management.cache.redis_client import cache_data, invalidate_cache, init_redis
from config.config import config_by_name, get_config
from flask_login import current_user
#from src.task_management.categories.models import Category


# Setup logging
log_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
    
log_file_path = os.path.join(log_directory, 'app.log')


def setup_bullet_navigation_fix(app):
    
    @app.after_request
    def remove_bullet_navigation(response):
        if response.content_type and response.content_type.startswith('text/html'):
            html = response.get_data(as_text=True)
            
            # Add a simple CSS solution in the head
            if '</head>' in html:
                css = """
                <style id="hide-bullets">
                /* Hide all top-level ULs that are direct children of the body */
                body > ul {
                    display: none !important;
                }
                </style>
                """
                html = html.replace('</head>', css + '</head>')
            
            response.set_data(html)
        
        return response
    
    return remove_bullet_navigation
def register_context_processors(app):
    """
    Register context processors for templates.
    """
    @app.context_processor
    def inject_categories():
        from src.task_management.categories.models import Category
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            try:
                return {'all_categories': Category.query.filter_by(user_id=current_user.id).all()}
            except Exception as e:
                app.logger.error(f"Error loading categories for context: {str(e)}")
                return {'all_categories': []}
        return {'all_categories': []}

def init_database(app):
    """
    Initialize the database with required tables if they don't exist.
    
    """
    
    with app.app_context():
        app.logger.info("Checking database tables...")
    
        
        # Check if we need to create tables
        try:
            inspector = db.inspect(db.engine)
            tables_exist = inspector.get_table_names()
            
            if not tables_exist:
                app.logger.info("No tables found. Creating all tables...")
                db.create_all()
                app.logger.info("Database tables created successfully.")
                create_default_data(app)
            else:
                app.logger.info("Database tables already exist.")
                
                # Check for specific tables and their columns
                if 'users' in tables_exist:
                    columns = inspector.get_columns('users')
                    for column in columns:
                        if column['name'] == 'password':
                            # If password column is too small, we need to migrate data
                            if hasattr(column['type'], 'length') and column['type'].length < 512:
                                app.logger.warning("Password column is too small. Consider running a migration.")
                                # Note: Actual column alteration would require Alembic migrations
                
        except Exception as e:
            app.logger.error(f"Error checking database: {str(e)}")
            # Try to create all tables as a fallback
            try:
                db.create_all()
                app.logger.info("Database tables created successfully after error.")
                create_default_data(app)
            except Exception as inner_e:
                app.logger.error(f"Failed to create database tables: {str(inner_e)}")

def create_default_data(app):
    """
    Create default admin user and categories.
    """
    try:
        app.logger.info("Creating default admin user...")
        from src.task_management.auth.models import User
        from src.task_management.categories.models import Category
        
        # Create admin user
        admin = User(username="admin", email_id="admin@taskflow.com", role="admin")
        admin.create_password("admin123")  # Use a secure password in production
        db.session.add(admin)
        db.session.commit()
        
        # Create default categories for admin
        categories = [
            Category(name="Work", description="Work-related tasks", color="#e74c3c", user_id=admin.id),
            Category(name="Personal", description="Personal tasks", color="#3498db", user_id=admin.id),
            Category(name="Urgent", description="Urgent tasks", color="#e67e22", user_id=admin.id),
            Category(name="Uncategorized", description="Default category", color="#95a5a6", user_id=admin.id)
        ]
        db.session.bulk_save_objects(categories)
        db.session.commit()
        app.logger.info("Default admin user and categories created.")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating default data: {str(e)}")


def create_web_app(config_name=None):
    """
    Application factory method to support different configurations.
    """
    # Get configuration
    config_class = get_config(config_name)
    
    # Initialize Flask app
    app = Flask('TaskFlow', template_folder='src/templates', static_folder='src/static')
    app.config.from_object(config_class)
    
    # Configure logging
    configure_logging(app)
    
    # Initialize extensions
    init_extensions(app)

    # Initialize database tables
    init_database(app)
    
    # Register context processors
    register_context_processors(app)

    # Setup bullet navigation fix
    setup_bullet_navigation_fix(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register middlewares
    register_middlewares(app)
    
    # Configure Swagger UI
    configure_swagger(app)
    
    # Register CLI commands
    register_commands(app)
    
    return app

def configure_logging(app):
    """
    Configure logging for the application.
    """
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    handler = RotatingFileHandler(log_file_path, maxBytes=10000000, backupCount=5)
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
    app.logger.info('TaskFlow startup')

def init_extensions(app):
    """
    Initialize Flask extensions.
    """
    # Initialize CORS
    CORS(app)
    
    # Initialize database and migrations
    init_db(app)

    with app.app_context():
        # Import models here to ensure they're registered
        from src.task_management.auth.models import User
        from src.task_management.tasks.models import Task
        from src.task_management.categories.models import Category
        
        # Ensure all tables exist
        db.create_all()
    
    # Initialize Redis cache
    init_redis(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Reload user object from the user ID stored in the session"""
        from src.task_management.auth.models import User
        return User.query.get(int(user_id))
        
    @login_manager.unauthorized_handler
    def unauthorized_user():
        """Handle unauthorized user requests"""
        # Check if request is an API call or a web page request
        if request.path.startswith('/api/'):
            return jsonify({"error": "Authentication required"}), 401
        else:
            flash("You must be logged in to access this page.", "error")
            return redirect(url_for('auth.login'))
    
    # Initialize Slack notifier if enabled
    if app.config.get('SLACK_ENABLED', False):
        app.slack_notifier = SlackNotifier(app.config.get('SLACK_WEBHOOK_URL', ''))
        app.logger.info("Slack notifications enabled")
    
    # Initialize Flask-Compress for response compression
    Compress(app)
    
    # Initialize Flask-Limiter for rate limiting
    Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["1000 per day", "200 per hour"],
        storage_uri=app.config.get('REDIS_URL')
    )
    
    # Initialize Talisman for security headers (if not in development)
    if not app.debug:
        talisman = Talisman(
            app,
            content_security_policy=app.config.get('SECURITY_HEADERS', {}).get('Content-Security-Policy'),
            force_https=app.config.get('ENV') == 'production',
            strict_transport_security=app.config.get('SECURITY_HEADERS', {}).get('Strict-Transport-Security'),
            session_cookie_secure=app.config.get('SESSION_COOKIE_SECURE', False)
        )

def register_error_handlers(app):
    """
    Register error handlers for the application.
    """
    @app.errorhandler(400)
    def bad_request_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Bad request", "details": str(error)}), 400
        return render_template('errors/400.html'), 400
        
    @app.errorhandler(401)
    def unauthorized_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Unauthorized", "details": str(error)}), 401
        return render_template('errors/401.html'), 401
        
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Forbidden", "details": str(error)}), 403
        return render_template('errors/403.html'), 403
        
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Resource not found", "details": str(error)}), 404
        return render_template('errors/404.html'), 404
        
    @app.errorhandler(429)
    def ratelimit_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Too many requests", "details": str(error)}), 429
        return render_template('errors/429.html'), 429
        
    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        app.logger.error(f"Server Error: {error}")
        if request.path.startswith('/api/'):
            return jsonify({"error": "Internal server error"}), 500
        return render_template('errors/500.html'), 500

def register_blueprints(app):
    """
    Register blueprints for different modules.
    
    """
    # Register web UI blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(task_bp, url_prefix='/tasks')
    app.register_blueprint(categories_bp, url_prefix='/categories')
    
    # Register API blueprints with unique names
    app.register_blueprint(auth_bp, url_prefix='/api/auth', name='auth_api')
    app.register_blueprint(task_bp, url_prefix='/api/tasks', name='tasks_api')
    app.register_blueprint(categories_bp, url_prefix='/api/categories', name='categories_api')
def register_middlewares(app):
    """
    Register middleware functions.
    
    """
    @app.before_request
    def before_request():
        """Execute before each request"""
        # Log API requests
        if request.path.startswith('/api/'):
            app.logger.debug(f"API Request: {request.method} {request.path}")

    @app.after_request
    def after_request(response):
        """Execute after each request"""
        # Add security headers
        for header, value in app.config.get('SECURITY_HEADERS', {}).items():
            response.headers.setdefault(header, value)
        
        # Set cache control headers for API responses
        if request.path.startswith('/api/'):
            response.headers.setdefault('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            response.headers.setdefault('Pragma', 'no-cache')
            response.headers.setdefault('Expires', '0')
        
        return response

def configure_swagger(app):
    """
    Configure Swagger UI for API documentation.
    """
    # Swagger UI setup
    SWAGGER_URL = '/api/docs'  # URL to access Swagger UI
    API_URL = '/static/swagger.json'  # URL to access OpenAPI specification
    swagger_ui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL, 
        API_URL, 
        config={
            "app_name": "TaskFlow API",
            "dom_id": "#swagger-ui",
            "deepLinking": True,
            "layout": "BaseLayout",
            "showExtensions": True,
            "showCommonExtensions": True
        }
    )
    app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)
    
    # Serving OpenAPI spec file from the static directory
    @app.route('/static/swagger.json')
    def serve_swagger_json():
        return send_from_directory(app.static_folder, 'swagger.json')

def register_commands(app):
    """
    Register custom CLI commands.
    """
    @app.cli.command("routes")
    def routes():
        """List all registered routes"""
        output = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            output.append(f"{rule.endpoint:30s} {methods:20s} {rule}")
        
        for line in sorted(output):
            print(line)

# Create the application instance
app = create_web_app()

# Root route
@app.route('/')
def index():
    """Root route that redirects to the task dashboard"""
    return redirect(url_for('tasks.dashboard'))

# Health check endpoint
@app.route('/health')
def health_check():
    """
    Health check endpoint for monitoring.
    """
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "healthy" if db.engine.execute("SELECT 1").scalar() == 1 else "unhealthy",
            "redis": "healthy" if check_redis() else "not configured or unhealthy"
        }
    }
    return jsonify(health_status)

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))