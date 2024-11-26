"""Authentication blueprint."""
from flask import Blueprint

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Import routes here to avoid circular imports
from app.auth import routes
