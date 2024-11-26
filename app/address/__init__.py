from flask import Blueprint

bp = Blueprint('address', __name__)

from app.address import routes
