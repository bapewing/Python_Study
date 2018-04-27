import flask
from flask import Blueprint

admin_blu = Blueprint('admin', __name__, url_prefix='/admin')

from . import views


@admin_blu.before_request
def check_admin():
    is_admin = flask.session.get('is_admin', False)
    if not is_admin and not flask.request.url.endswith(flask.url_for('admin.admin_login')):
        return flask.redirect('/')
