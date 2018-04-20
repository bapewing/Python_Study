from flask import Blueprint

# ValueError: urls must start with a leading slash 原因:url_prefix没加/
passport_blu = Blueprint('passport', __name__, url_prefix='/passport')

from . import views
