from flask import Blueprint

bp = Blueprint('wishlist', __name__)

from app.wishlist import routes
