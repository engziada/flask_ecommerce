from flask import Blueprint

bp = Blueprint('admin', __name__, url_prefix='/admin')

from . import routes  # Import routes at the end to avoid circular imports
