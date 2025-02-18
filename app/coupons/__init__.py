from flask import Blueprint

bp = Blueprint('coupons', __name__)

from app.coupons import routes
