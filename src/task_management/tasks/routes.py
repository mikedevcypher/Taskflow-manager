# src/task_management/tasks/routes.py
"""
This module handles task management routes for the TaskFlow application.
It supports adding, viewing, editing, deleting, and categorizing tasks,
with both web UI and API endpoints.
"""
from datetime import datetime
from flask import Flask,Blueprint, request, jsonify, flash, redirect, render_template, url_for, make_response, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from .models import Task
from src.task_management.categories.models import Category
from src.task_management.auth.routes import token_required
from src.task_management.db import db, optimize_query
from src.task_management.cache.redis_client import cache_data, invalidate_cache
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import current_user


task_bp = Blueprint('tasks', __name__)
 
def limit_route(limit_string):
    """Helper function to apply rate limits without circular imports"""
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if the current app has a rate limiter
           
            
            # Look for the limiter instance in extensions
            limiter = None
            for extension in current_app.extensions.values():
                if isinstance(extension, Limiter):
                    limiter = extension
                    break
            
            if limiter is None:
                # If no rate limiter is found, log a warning and proceed without limiting
                current_app.logger.warning("Rate limiter not found in extensions")
                return f(*args, **kwargs)
                
            # Apply the limit
            limited = limiter.limit(limit_string)(f)
            return limited(*args, **kwargs)
        
        return decorated_function
    return decorator


# Web UI Routes
@task_bp.route('/dashboard', methods=['GET'])
@login_required
@limit_route("1000 per day")
def dashboard():
    """
    Display the task dashboard with filtered tasks based on query parameters.
    
    """
    # Get filter parameters
    status = request.args.get('status')
    priority = request.args.get('priority')
    category_id = request.args.get('category_id')
    sort = request.args.get('sort', 'due_date')
    order = request.args.get('order', 'asc')
    
    # Base query
    query = Task.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Apply sorting
    if sort == 'due_date':
        sort_column = Task.due_date
    elif sort == 'priority':
        sort_column = Task.priority
    elif sort == 'created_at':
        sort_column = Task.created_at
    else:
        sort_column = Task.due_date
    
    if order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Execute query
    tasks = query.all()
    
    # Get all categories for filter dropdown
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    # Get current date for template
    current_date = datetime.now().date()
    
    # Calculate task stats for progress bars
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.status == 'completed')
    in_progress_tasks = sum(1 for task in tasks if task.status == 'in-progress')
    pending_tasks = sum(1 for task in tasks if task.status == 'pending')
    
    # Calculate percentages for progress bars
    if total_tasks > 0:
        completed_percent = int((completed_tasks / total_tasks) * 100)
        in_progress_percent = int((in_progress_tasks / total_tasks) * 100)
        pending_percent = int((pending_tasks / total_tasks) * 100)
    else:
        completed_percent = 0
        in_progress_percent = 0
        pending_percent = 0
    
    # Enhance tasks with additional data
    for task in tasks:
        # Convert datetime to date for comparison 
        task_due_date = task.due_date.date() if hasattr(task.due_date, 'date') else task.due_date
        task.is_overdue = task_due_date < current_date
        task.is_due_today = task_due_date == current_date
    
    # Set cache control headers
    response = make_response(render_template(
        'dashboard.html',
        tasks=tasks,
        categories=categories,
        current_date=current_date,
        all_categories=categories,  # For backward compatibility
        completed_percent=completed_percent,
        in_progress_percent=in_progress_percent,
        pending_percent=pending_percent
    ))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@task_bp.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_new_task():
    """Handle adding/creating new tasks with category support."""
    # Get all categories for the dropdown
    categories = Category.query.filter_by(user_id=current_user.id).all()
    # Create Uncategorized category if it doesn't exist
    uncategorized = Category.query.filter_by(name="Uncategorized", user_id=current_user.id).first()
    if not uncategorized:
        uncategorized = Category(
            name="Uncategorized",
            description="Default category for tasks",
            color="#95a5a6",  # Grey color
            user_id=current_user.id
        )
        db.session.add(uncategorized)
        db.session.commit()
        categories.append(uncategorized)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority', 'medium')
        status = request.form.get('status', 'pending')
        category_id = request.form.get('category_id')
        
        # Validate required fields
        if not title or not due_date_str:
            flash("Title and Due Date are required fields", "error")
            return render_template('add_task.html', categories=categories)
        
        try:
            # Parse date
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            
            # Create new task
            new_task = Task(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                status=status,
                user_id=current_user.id,
                category_id=category_id if category_id else None
            )
            
            db.session.add(new_task)
            db.session.commit()
            
            # Invalidate cache
            invalidate_cache(f'user_tasks_{current_user.id}')
            
            # Send Slack notification if enabled
            if current_app.config.get('SLACK_ENABLED', False) and hasattr(current_app, 'slack_notifier'):
                current_app.slack_notifier.notify_task_created(new_task, current_user)
            
            flash("Task added successfully", "success")
            return redirect(url_for('tasks.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding task: {str(e)}", "error")
            return render_template('add_task.html', categories=categories)
    
    return render_template('add_task.html', categories=categories)

@task_bp.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Edit an existing task."""
    # Get the task
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    # Get all categories for the dropdown
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority')
        status = request.form.get('status')
        category_id = request.form.get('category_id')
        
        # Validate required fields
        if not title or not due_date_str:
            flash("Title and Due Date are required fields", "error")
            return render_template('edit_task.html', task=task, categories=categories)
        
        try:
            # Update task fields
            task.title = title
            task.description = description
            task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            task.priority = priority
            task.status = status
            task.category_id = category_id if category_id else None
            
            db.session.commit()
            
            # Invalidate cache
            invalidate_cache(f'user_tasks_{current_user.id}')
            invalidate_cache(f'task_{task_id}')
            
            flash("Task updated successfully", "success")
            return redirect(url_for('tasks.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating task: {str(e)}", "error")
            return render_template('edit_task.html', task=task, categories=categories)
    
    return render_template('edit_task.html', task=task, categories=categories)

@task_bp.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    """Delete a task."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(task)
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache(f'user_tasks_{current_user.id}')
        invalidate_cache(f'task_{task_id}')
        
        flash("Task deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting task: {str(e)}", "error")
    
    return redirect(url_for('tasks.dashboard'))

@task_bp.route('/complete_task/<int:task_id>', methods=['GET','POST'])
@login_required
def complete_task(task_id):
    """Mark a task as completed."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    try:
        task.status = 'completed'
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache(f'user_tasks_{current_user.id}')
        invalidate_cache(f'task_{task_id}')
        
        # Send Slack notification if enabled
        if current_app.config.get('SLACK_ENABLED', False) and hasattr(current_app, 'slack_notifier'):
            current_app.slack_notifier.notify_task_completed(task, current_user)
        
        flash("Task marked as completed", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error completing task: {str(e)}", "error")
    
    return redirect(url_for('tasks.dashboard'))

# API Routes
@task_bp.route('/api/tasks', methods=['GET'])
@token_required
def api_get_tasks(current_user):
    """
    Get all tasks for the authenticated user with filtering, sorting, and pagination.
    
    """
    # Get request parameters
    status = request.args.get('status')
    priority = request.args.get('priority')
    category_id = request.args.get('category_id')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)  # Cap at 100 items per page
    sort = request.args.get('sort', 'due_date')
    order = request.args.get('order', 'asc')
    
    # Try to get from cache first
    @cache_data(f'user_tasks_{current_user.id}_{status}_{priority}_{category_id}_{page}_{per_page}_{sort}_{order}', expire=300)
    def get_tasks():
        # Base query
        query = Task.query.filter_by(user_id=current_user.id)
        
        # Apply filters
        if status:
            query = query.filter_by(status=status)
        if priority:
            query = query.filter_by(priority=priority)
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        # Apply sorting
        if sort == 'due_date':
            sort_column = Task.due_date
        elif sort == 'priority':
            sort_column = Task.priority
        elif sort == 'created_at':
            sort_column = Task.created_at
        else:
            sort_column = Task.due_date
        
        if order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Apply pagination
        tasks_page = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Prepare response
        return {
            "tasks": [task.to_dict() for task in tasks_page.items],
            "pagination": {
                "total": tasks_page.total,
                "page": tasks_page.page,
                "per_page": tasks_page.per_page,
                "pages": tasks_page.pages,
                "has_next": tasks_page.has_next,
                "has_prev": tasks_page.has_prev
            }
        }
    
    return jsonify(get_tasks()), 200

@task_bp.route('/api/tasks', methods=['POST'])
@token_required
def api_create_task(current_user):
    """
    Create a new task.
    
    """
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('title') or not data.get('due_date'):
        return jsonify({"error": "Title and due date are required"}), 400
    
    try:
        # Create new task
        new_task = Task(
            title=data.get('title'),
            description=data.get('description', ''),
            due_date=datetime.fromisoformat(data.get('due_date').replace('Z', '+00:00')),
            priority=data.get('priority', 'medium'),
            status=data.get('status', 'pending'),
            user_id=current_user.id,
            category_id=data.get('category_id')
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache(f'user_tasks_{current_user.id}')
        
        # Send Slack notification if enabled
        if current_app.config.get('SLACK_ENABLED', False) and hasattr(current_app, 'slack_notifier'):
            current_app.slack_notifier.notify_task_created(new_task, current_user)
        
        return jsonify({
            "message": "Task created successfully",
            "task": new_task.to_dict()
        }), 201
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error creating task: {str(e)}"}), 500

@task_bp.route('/api/tasks/<int:task_id>', methods=['GET'])
@token_required
def api_get_task(current_user, task_id):
    """Get a specific task by ID."""
    # Try to get from cache first
    @cache_data(f'task_{task_id}', expire=300)
    def get_task():
        task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
        if not task:
            return None
        return {"task": task.to_dict()}
    
    result = get_task()
    if not result:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify(result), 200

@task_bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
@token_required
def api_update_task(current_user, task_id):
    """
    Update a specific task.
    """
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No update data provided"}), 400
    
    try:
        # Update fields if provided
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'due_date' in data:
            task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
        if 'priority' in data:
            task.priority = data['priority']
        if 'status' in data:
            task.status = data['status']
        if 'category_id' in data:
            task.category_id = data['category_id']
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache(f'user_tasks_{current_user.id}')
        invalidate_cache(f'task_{task_id}')
        
        return jsonify({
            "message": "Task updated successfully",
            "task": task.to_dict()
        }), 200
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error updating task: {str(e)}"}), 500

@task_bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@token_required
def api_delete_task(current_user, task_id):
    """Delete a specific task."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    try:
        db.session.delete(task)
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache(f'user_tasks_{current_user.id}')
        invalidate_cache(f'task_{task_id}')
        
        return jsonify({"message": "Task deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error deleting task: {str(e)}"}), 500

@task_bp.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
@token_required
def api_complete_task(current_user, task_id):
    """Mark a task as completed."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    try:
        task.status = 'completed'
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache(f'user_tasks_{current_user.id}')
        invalidate_cache(f'task_{task_id}')
        
        # Send Slack notification if enabled
        if current_app.config.get('SLACK_ENABLED', False) and hasattr(current_app, 'slack_notifier'):
            current_app.slack_notifier.notify_task_completed(task, current_user)
        
        return jsonify({
            "message": "Task marked as completed",
            "task": task.to_dict()
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error completing task: {str(e)}"}), 500