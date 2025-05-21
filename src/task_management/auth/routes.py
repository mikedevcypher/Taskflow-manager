# src/task_management/auth/routes.py
"""
This module handles authentication routes for the TaskFlow application.
It supports both form-based authentication (for web UI) and JWT token-based
authentication (for API clients).
"""
from flask import Blueprint, request, jsonify, redirect, url_for, render_template, flash, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from .models import User
from src.task_management.db import db
from datetime import datetime, timedelta,timezone
from functools import wraps
import jwt
import os
import random
from flask_mail import Message
from .email import send_email, send_password_reset_email
import string


auth_bp = Blueprint('auth', __name__)

# JWT Authentication Helper Functions
def token_required(f):
    """
    Decorator to check if the request has a valid JWT token.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in the header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            # Decode token
            secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
            data = jwt.decode(token, secret_key, algorithms=["HS256"])
            current_user = User.query.filter_by(email_id=data['sub']).first()
            
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

# Form-based Authentication Routes (Web UI)
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user via web form"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email_id')
        
        if not username or not password or not email:
            flash("Required fields missing from the form", "error")
            return render_template('register.html'), 400
    
        existing_user = User.query.filter((User.username == username) | (User.email_id == email)).first()
    
        if existing_user:
            flash("User already registered. Please try to sign in", "error")
            return render_template('register.html'), 400
        
        hash_password = generate_password_hash(password)
        new_user = User(username=username, email_id=email, password=hash_password)
        db.session.add(new_user)
        try:
            db.session.commit()
            flash("User registered successfully.")
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash("Registration failed", "error")
            return render_template('register.html'), 500
    return render_template('register.html')
    
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticate a user via web form"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            user.update_last_login()
            flash("Login successful.", "success")
            return redirect(url_for('tasks.dashboard'))
        else:
            flash("Invalid user credentials. Please try again", "error")
            return render_template('login.html'), 401
    return render_template('login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Logout a user from web session"""
    logout_user()
    flash("You have been logged out.", 'info')
    return redirect(url_for('auth.login'))

# API Authentication Routes (JWT-based)
@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    """
    Register a new user via API
    """
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing required fields"}), 400
        
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    existing_user = User.query.filter((User.username == username) | (User.email_id == email)).first()
    
    if existing_user:
        return jsonify({"error": "User already exists"}), 409
    
    new_user = User(username=username, email_id=email)
    new_user.create_password(password)
    
    db.session.add(new_user)
    try:
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """
    Authenticate and get JWT token

    """
    auth = request.get_json()
    
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({"error": "Missing credentials"}), 400
        
    user = User.query.filter_by(username=auth.get('username')).first()
    
    if not user or not user.check_password(auth.get('password')):
        return jsonify({"error": "Invalid credentials"}), 401
        
    # Update last login time
    user.update_last_login()
    
    # Generate JWT token with 24 hour expiration
    token_expiry = timedelta(hours=24)
    token = user.generate_jwt_token(token_expiry)
    expires_at = datetime.utcnow() + token_expiry

    
    return jsonify({
        "token": token,
        "expires_at": expires_at.isoformat(),
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email_id,
            "role": user.role
        }
    }), 200

@auth_bp.route('/api/refresh-token', methods=['POST'])
@token_required
def refresh_token(current_user):
    """
    Refresh the JWT token for the authenticated user

    """
    # Generate a new token
    token_expiry = timedelta(hours=24)
    new_token = current_user.generate_jwt_token(token_expiry)
    expires_at = datetime.utcnow() + token_expiry
    
    return jsonify({
        "token": new_token,
        "expires_at": expires_at.isoformat()
    }), 200

@auth_bp.route('/api/user', methods=['GET'])
@token_required
def get_user_info(current_user):
    """
    Get information about the currently authenticated user
    """
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email_id,
        "role": current_user.role,
        "created_on": current_user.created_on.isoformat() if current_user.created_on else None,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }), 200

@auth_bp.route('/api/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """
    Change the password for the authenticated user

    """
    data = request.get_json()
    
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({"error": "Missing required fields"}), 400
        
    # Verify current password
    if not current_user.check_password(data.get('current_password')):
        return jsonify({"error": "Current password is incorrect"}), 401
        
    # Update password
    current_user.create_password(data.get('new_password'))
    
    try:
        db.session.commit()
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Password update failed: {str(e)}"}), 500
    


# In production, store these in a database with expiration
password_reset_tokens = {}

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle password reset request"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash("Email is required", "error")
            return render_template('forgot_password.html'), 400
        
        # Find user by email
        user = User.query.filter_by(email_id=email).first()
        
        if not user:
            # Don't reveal if email exists for security reasons
            flash("If an account with that email exists, we have sent a password reset link.", "info")
            return redirect(url_for('auth.login'))
        
        # Generate a secure random token
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        
        # Store token with expiration (24 hours)
        expiration = datetime.now(timezone.utc) + timedelta(hours=24)
        password_reset_tokens[token] = {
            'user_id': user.id,
            'expires': expiration
        }
        
        # Create reset link
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        # Send email with reset link
        try:
            # Check if we're using a mail service
            if hasattr(current_app, 'mail'):
                msg = Message(
                    subject="TaskFlow Password Reset",
                    recipients=[email],
                    body=f"Click the following link to reset your password: {reset_url}\n\nThis link will expire in 24 hours.",
                    html=render_template('reset_password.html', reset_url=reset_url, username=user.username)
                )
                current_app.mail.send(msg)
            else:
                # Fallback for when email service isn't configured
                send_email(
                    recipient=email,
                    subject="TaskFlow Password Reset",
                    body=f"Click the following link to reset your password: {reset_url}\n\nThis link will expire in 24 hours."
                )
                
            flash("If an account with that email exists, we have sent a password reset link.", "info")
            return redirect(url_for('auth.login'))
        except Exception as e:
            current_app.logger.error(f"Failed to send password reset email: {str(e)}")
            flash("There was an error sending the password reset email. Please try again later.", "error")
            return render_template('forgot_password.html'), 500
    
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password using token"""
    # Check if token exists and is valid
    if token not in password_reset_tokens:
        flash("Invalid or expired password reset token", "error")
        return redirect(url_for('auth.forgot_password'))
    
    # Check if token is expired
    token_data = password_reset_tokens[token]
    if datetime.now(timezone.utc) > token_data['expires']:
        # Remove expired token
        password_reset_tokens.pop(token)
        flash("Password reset token has expired", "error")
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash("Password fields are required", "error")
            return render_template('reset_password.html', token=token), 400
        
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template('reset_password.html', token=token), 400
        
        # Get user from token data
        user = User.query.get(token_data['user_id'])
        
        if not user:
            flash("User not found", "error")
            return redirect(url_for('auth.forgot_password'))
        
        # Update password
        user.create_password(password)
        
        try:
            db.session.commit()
            # Remove used token
            password_reset_tokens.pop(token)
            flash("Password has been reset successfully. You can now log in with your new password.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash("Password reset failed", "error")
            return render_template('reset_password.html', token=token), 500
    
    return render_template('reset_password.html', token=token)

# API route for password reset request
@auth_bp.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    """API endpoint to request password reset"""
    data = request.get_json()
    
    if not data or not data.get('email'):
        return jsonify({"error": "Email is required"}), 400
        
    email = data.get('email')
    user = User.query.filter_by(email_id=email).first()
    
    if not user:
        # Don't reveal if email exists for security
        return jsonify({"message": "If an account with that email exists, a password reset link will be sent."}), 200
    
    # Generate token 
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    expiration = datetime.now(timezone.utc) + timedelta(hours=24)
    password_reset_tokens[token] = {
        'user_id': user.id,
        'expires': expiration
    }
    
    # URL for password reset page
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    # Send email 
    try:
        if hasattr(current_app, 'mail'):
            msg = Message(
                subject="TaskFlow Password Reset",
                recipients=[email],
                body=f"Click the following link to reset your password: {reset_url}\n\nThis link will expire in 24 hours.",
                html=render_template('reset_password.html', reset_url=reset_url, username=user.username)
            )
            current_app.mail.send(msg)
        else:
            send_email(
                recipient=email,
                subject="TaskFlow Password Reset",
                body=f"Click the following link to reset your password: {reset_url}\n\nThis link will expire in 24 hours."
            )
            
        return jsonify({"message": "If an account with that email exists, a password reset link will be sent."}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {str(e)}")
        return jsonify({"error": "Failed to send password reset email"}), 500
    
# API route for resetting password with token
@auth_bp.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    """API endpoint to reset password using token"""
    data = request.get_json()
    
    if not data or not data.get('token') or not data.get('password'):
        return jsonify({"error": "Token and password are required"}), 400
        
    token = data.get('token')
    password = data.get('password')
    
    # Check token validity (same logic as web route)
    if token not in password_reset_tokens:
        return jsonify({"error": "Invalid or expired password reset token"}), 400
    
    token_data = password_reset_tokens[token]
    if datetime.now(timezone.utc) > token_data['expires']:
        password_reset_tokens.pop(token)
        return jsonify({"error": "Password reset token has expired"}), 400
    
    # Get user and update password
    user = User.query.get(token_data['user_id'])
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    user.create_password(password)
    
    try:
        db.session.commit()
        password_reset_tokens.pop(token)
        return jsonify({"message": "Password has been reset successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Password reset failed: {str(e)}"}), 500