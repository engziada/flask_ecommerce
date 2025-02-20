"""Authentication blueprint."""
from flask import Blueprint

bp = Blueprint('auth', __name__)

# Import routes here to avoid circular imports
from app.auth import routes
