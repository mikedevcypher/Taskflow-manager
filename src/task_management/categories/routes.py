# src/task_management/categories/routes.py
"""
This module handles routes for category management in the TaskFlow application.
It supports creating, reading, updating, and deleting categories,
as well as assigning tasks to categories.
"""
from flask import request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from src.task_management.db import db
from src.task_management.auth.routes import token_required
from .models import Category
from src.task_management.cache.redis_client import cache_data, invalidate_cache
from . import categories_bp

# Web UI Routes
@categories_bp.route('/', methods=['GET'])
@login_required
def list_categories():
    """
    Display all categories for the current user.
    """
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('categories/list_categories.html', categories=categories)

@categories_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_category():
    """
    Create a new category via web form.
    """
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        color = request.form.get('color', '#3498db')
        icon = request.form.get('icon', 'folder')
        
        if not name:
            flash('Category name is required.', 'error')
            return redirect(url_for('categories.create_category'))
        
        category = Category(
            name=name,
            description=description,
            color=color,
            icon=icon,
            user_id=current_user.id
        )
        
        try:
            db.session.add(category)
            db.session.commit()
            invalidate_cache(f'user_categories_{current_user.id}')
            flash('Category created successfully.', 'success')
            return redirect(url_for('categories.list_categories'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Error creating category: {str(e)}', 'error')
            return redirect(url_for('categories.create_category'))
    
    return render_template('categories/create_category.html')

@categories_bp.route('/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """
    Edit an existing category via web form.
    """
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        color = request.form.get('color')
        icon = request.form.get('icon')
        
        if not name:
            flash('Category name is required.', 'error')
            return redirect(url_for('categories.edit_category', category_id=category_id))
        
        category.name = name
        category.description = description
        if color:
            category.color = color
        if icon:
            category.icon = icon
        
        try:
            db.session.commit()
            invalidate_cache(f'user_categories_{current_user.id}')
            invalidate_cache(f'category_{category_id}')
            flash('Category updated successfully.', 'success')
            return redirect(url_for('categories.list_categories'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Error updating category: {str(e)}', 'error')
            return redirect(url_for('categories.edit_category', category_id=category_id))
    
    return render_template('categories/edit_category.html', category=category)

@categories_bp.route('/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """
    Delete a category and reassign its tasks to the default category.
    """
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    
    # Don't allow deletion of the default category
    if category.name == 'Uncategorized':
        flash('Cannot delete the default category.', 'error')
        return redirect(url_for('categories.list_categories'))
    
    # Get default category for reassigning tasks
    default_category = Category.get_default_category(current_user.id)
    
    try:
        # Reassign tasks to default category
        for task in category.category_tasks:
            task.category_id = default_category.id
        
        # Delete the category
        db.session.delete(category)
        db.session.commit()
        
        # Invalidate caches
        invalidate_cache(f'user_categories_{current_user.id}')
        invalidate_cache(f'category_{category_id}')
        
        flash('Category deleted successfully.', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'error')
    
    return redirect(url_for('categories.list_categories'))

# API Routes
@categories_bp.route('/api/categories', methods=['GET'])
@token_required
def api_get_categories(current_user):
    """
    Get all categories for the authenticated user.
    """
    # Try to get from cache first
    @cache_data(f'user_categories_{current_user.id}', expire=300)
    def get_user_categories():
        categories = Category.query.filter_by(user_id=current_user.id).all()
        return {"categories": [category.to_dict() for category in categories]}
    
    return jsonify(get_user_categories()), 200

@categories_bp.route('/api/categories', methods=['POST'])
@token_required
def api_create_category(current_user):
    """
    Create a new category for the authenticated user.
    """
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({"error": "Category name is required"}), 400
    
    # Create new category
    category = Category(
        name=data.get('name'),
        description=data.get('description', ''),
        color=data.get('color', '#3498db'),
        icon=data.get('icon', 'folder'),
        user_id=current_user.id
    )
    
    try:
        db.session.add(category)
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache(f'user_categories_{current_user.id}')
        
        return jsonify({
            "message": "Category created successfully",
            "category": category.to_dict()
        }), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create category: {str(e)}"}), 500

@categories_bp.route('/api/categories/<int:category_id>', methods=['GET'])
@token_required
def api_get_category(current_user, category_id):
    """
    Get a specific category by ID.
    """
    # Try to get from cache first
    @cache_data(f'category_{category_id}', expire=300)
    def get_category():
        category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
        if not category:
            return None
        return {"category": category.to_dict()}
    
    result = get_category()
    if not result:
        return jsonify({"error": "Category not found"}), 404
    
    return jsonify(result), 200

@categories_bp.route('/api/categories/<int:category_id>', methods=['PUT'])
@token_required
def api_update_category(current_user, category_id):
    """
    Update a specific category.

    """
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
    if not category:
        return jsonify({"error": "Category not found"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No update data provided"}), 400
    
    # Update fields if provided
    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = data['color']
    if 'icon' in data:
        category.icon = data['icon']
    
    try:
        db.session.commit()
        
        # Invalidate caches
        invalidate_cache(f'user_categories_{current_user.id}')
        invalidate_cache(f'category_{category_id}')
        
        return jsonify({
            "message": "Category updated successfully",
            "category": category.to_dict()
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update category: {str(e)}"}), 500

@categories_bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
@token_required
def api_delete_category(current_user, category_id):
    """
    Delete a specific category and reassign its tasks to the default category.
    """
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
    if not category:
        return jsonify({"error": "Category not found"}), 404
    
    # Don't allow deletion of the default category
    if category.name == 'Uncategorized':
        return jsonify({"error": "Cannot delete the default category"}), 400
    
    # Get default category for reassigning tasks
    default_category = Category.get_default_category(current_user.id)
    
    try:
        # Reassign tasks to default category
        for task in category.category_tasks:
            task.category_id = default_category.id
        
        # Delete the category
        db.session.delete(category)
        db.session.commit()
        
        # Invalidate caches
        invalidate_cache(f'user_categories_{current_user.id}')
        invalidate_cache(f'category_{category_id}')
        
        return jsonify({"message": "Category deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete category: {str(e)}"}), 500