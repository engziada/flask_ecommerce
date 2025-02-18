"""Utility functions for the application"""
from flask import current_app

def allowed_file(filename):
    """Check if a file has an allowed extension
    
    Args:
        filename (str): Name of the file to check
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
