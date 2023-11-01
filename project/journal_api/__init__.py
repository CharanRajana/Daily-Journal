"""
The 'journal_api' blueprint handles the API for managing journal entries.
Specifically, this blueprint allows for journal entries to be added, edited,
and deleted.
"""
from flask import Blueprint


journal_api_blueprint = Blueprint('journal_api', __name__)

from . import routes
