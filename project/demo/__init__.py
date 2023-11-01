"""
The 'demo_api' blueprint handles the API for demonstrating how to manage
journal entries with a fake set of data (not stored in a database).
Specifically, this blueprint allows for journal entries to be added, edited,
and deleted.
"""
from flask import Blueprint


demo_api_blueprint = Blueprint('demo_api', __name__)

from . import routes
