# src/task_management/integrations/routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import hmac
import hashlib
import json
import logging
from .slack import SlackService
from ..auth.models import User

logger = logging.getLogger(__name__)

integrations_bp = Blueprint('integrations', __name__, url_prefix='/api/integrations')

@integrations_bp.route('/slack/events', methods=['POST'])
def slack_events():
    """Handle Slack events and interactive components"""
    
    # Verify Slack signature
    if not verify_slack_signature(request):
        return jsonify({"error": "Invalid signature"}), 401
    
    try:
        data = request.get_json()
        
        # Handle URL verification challenge
        if data.get('type') == 'url_verification':
            return jsonify({"challenge": data.get('challenge')})
        
        # Handle interactive components (button clicks)
        if data.get('type') == 'interactive_message' or 'payload' in request.form:
            payload = json.loads(request.form.get('payload', '{}'))
            slack = SlackService()
            response = slack.handle_interactive_component(payload)
            return jsonify(response)
        
        # Handle other events
        event = data.get('event', {})
        if event.get('type') == 'app_mention':
            # Handle app mentions
            pass
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        return jsonify({"error": "Internal server error"}), 500

@integrations_bp.route('/slack/commands', methods=['POST'])
def slack_commands():
    """Handle Slack slash commands"""
    
    # Verify Slack signature
    if not verify_slack_signature(request):
        return jsonify({"error": "Invalid signature"}), 401
    
    try:
        command = request.form.get('command')
        text = request.form.get('text', '')
        user_id = request.form.get('user_id')
        channel_id = request.form.get('channel_id')
        
        slack = SlackService()
        response = slack.handle_slack_command(command, text, user_id, channel_id)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error handling Slack command: {e}")
        return jsonify({
            "response_type": "ephemeral",
            "text": "Sorry, there was an error processing your command."
        })

@integrations_bp.route('/slack/test', methods=['POST'])
@jwt_required()
def test_slack_notification():
    """Test endpoint to send a Slack notification"""
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    message = data.get('message', 'Test notification from Taskflow Manager!')
    channel = data.get('channel')
    
    slack = SlackService()
    success = slack.send_notification(message, channel)
    
    if success:
        return jsonify({"message": "Notification sent successfully"})
    else:
        return jsonify({"error": "Failed to send notification"}), 500

@integrations_bp.route('/slack/user/settings', methods=['GET', 'PUT'])
@jwt_required()
def slack_user_settings():
    """Get or update user's Slack notification settings"""
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if request.method == 'GET':
        return jsonify({
            "slack_notifications_enabled": getattr(user, 'slack_notifications_enabled', False),
            "slack_user_id": getattr(user, 'slack_user_id', None),
            "notification_preferences": {
                "task_assignments": getattr(user, 'notify_task_assignments', True),
                "due_date_reminders": getattr(user, 'notify_due_dates', True),
                "task_completions": getattr(user, 'notify_completions', True),
                "daily_summaries": getattr(user, 'notify_daily_summary', False)
            }
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        # Update user settings
        if 'slack_notifications_enabled' in data:
            user.slack_notifications_enabled = data['slack_notifications_enabled']
        
        if 'slack_user_id' in data:
            user.slack_user_id = data['slack_user_id']
        
        # Update notification preferences
        prefs = data.get('notification_preferences', {})
        if 'task_assignments' in prefs:
            user.notify_task_assignments = prefs['task_assignments']
        if 'due_date_reminders' in prefs:
            user.notify_due_dates = prefs['due_date_reminders']
        if 'task_completions' in prefs:
            user.notify_completions = prefs['task_completions']
        if 'daily_summaries' in prefs:
            user.notify_daily_summary = prefs['daily_summaries']
        
        try:
            from .. import db
            db.session.commit()
            return jsonify({"message": "Settings updated successfully"})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user settings: {e}")
            return jsonify({"error": "Failed to update settings"}), 500

def verify_slack_signature(request):
    """Verify that the request came from Slack"""
    
    slack_signing_secret = current_app.config.get('SLACK_SIGNING_SECRET')
    if not slack_signing_secret:
        logger.warning("Slack signing secret not configured")
        return True  # Skip verification if not configured
    
    timestamp = request.headers.get('X-Slack-Request-Timestamp')
    signature = request.headers.get('X-Slack-Signature')
    
    if not timestamp or not signature:
        return False
    
    # Create signature
    req_body = request.get_data()
    basestring = f"v0:{timestamp}:{req_body.decode('utf-8')}"
    
    computed_signature = 'v0=' + hmac.new(
        slack_signing_secret.encode('utf-8'),
        basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature)