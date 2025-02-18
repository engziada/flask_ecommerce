"""Custom decorators for the application"""
from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """Decorator to require admin access for a route
    
    This decorator should be used after @login_required to ensure
    the user is both authenticated and has admin privileges.
    
    Args:
        f: The function to decorate
        
    Returns:
        decorated_function: The decorated function that checks for admin access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function
