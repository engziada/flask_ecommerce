from flask import Blueprint

bp = Blueprint('shipping', __name__)

from . import routes  # noqa
