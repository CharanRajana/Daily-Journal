"""
The 'users_api' blueprint handles the API for managing users entries.
Specifically, this Blueprint allows for new users to register and for
users to request an authentication token to access protected aspects
of the application.
"""
from flask import Blueprint


users_api_blueprint = Blueprint('users_api', __name__, template_folder='templates')

from . import authentication, routes
