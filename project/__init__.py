"""
Welcome to the documentation for the Flask Journal API!

## Introduction

The Flask Journal API is an API (Application Programming Interface) for creating a **daily journal** that documents events that happen each day.

## Key Functionality

The Flask Journal API has the following functionality:

1. Work with journal entries:
  * Create a new journal entry
  * Update a journal entry
  * Delete a journal entry
  * View all journal entries
2. User management:
  * Register new users
  * Retrieve authentication token

## Key Modules

This project is written using Python 3.10.1.

The project utilizes the following modules:

* **Flask**: micro-framework for web application development which includes the following dependencies:
  * **click**: package for creating command-line interfaces (CLI)
  * **itsdangerous**: cryptographically sign data
  * **Jinja2**: templating engine
  * **MarkupSafe**: escapes characters so text is safe to use in HTML and XML
  * **Werkzeug**: set of utilities for creating a Python application that can talk to a WSGI server
* **APIFairy**: API framework for Flask which includes the following dependencies:
  * **Flask-Marshmallow** - Flask extension for using Marshmallow (object serialization/deserialization library)
  * **Flask-HTTPAuth** - Flask extension for HTTP authentication
  * **apispec** - API specification generator that supports the OpenAPI specification
* **pytest**: framework for testing Python projects
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from apifairy import APIFairy
from click import echo
from flask import Flask, json
from flask.logging import default_handler
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from flask_login import LoginManager
from flask_mail import Mail
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from werkzeug.exceptions import HTTPException


# -------------
# Configuration
# -------------

# Create a naming convention for the database tables
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=convention)

# Create the instances of the Flask extensions in the global scope,
# but without any arguments passed in. These instances are not
# attached to the Flask application at this point.
apifairy = APIFairy()
ma = Marshmallow()
database = SQLAlchemy(metadata=metadata)
db_migration = Migrate()
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()
mail = Mail()
login = LoginManager()
login.login_view = "admin.admin_login"


# ----------------------------
# Application Factory Function
# ----------------------------

def create_app():
    # Create the Flask application
    app = Flask(__name__)

    # Configure the Flask application
    config_type = os.getenv('CONFIG_TYPE', default='config.DevelopmentConfig')
    app.config.from_object(config_type)

    initialize_extensions(app)
    register_blueprints(app)
    configure_logging(app)
    register_error_handlers(app)
    register_cli_commands(app)
    return app


# ----------------
# Helper Functions
# ----------------

def initialize_extensions(app):
    # Since the application instance is now created, pass it to each Flask
    # extension instance to bind it to the Flask application instance (app)
    apifairy.init_app(app)
    ma.init_app(app)
    database.init_app(app)
    db_migration.init_app(app, database, render_as_batch=True)
    mail.init_app(app)
    login.init_app(app)

    # Flask-Login configuration
    from project.models import User

    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


def register_blueprints(app):
    # Import the blueprints
    from project.admin import admin_blueprint
    from project.demo import demo_api_blueprint
    from project.journal_api import journal_api_blueprint
    from project.users_api import users_api_blueprint

    # Since the application instance is now created, register each Blueprint
    # with the Flask application instance (app)
    app.register_blueprint(journal_api_blueprint, url_prefix='/journal')
    app.register_blueprint(users_api_blueprint, url_prefix='/users')
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    app.register_blueprint(demo_api_blueprint, url_prefix='/demo')


def configure_logging(app):
    if app.config['LOG_TO_STDOUT']:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
    else:
        file_handler = RotatingFileHandler('instance/flask-journal-api.log',
                                           maxBytes=16384,
                                           backupCount=20)
        file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(threadName)s-%(thread)d: %(message)s [in %(filename)s:%(lineno)d]')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    # Remove the default logger configured by Flask
    app.logger.removeHandler(default_handler)


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Return JSON instead of HTML for HTTP errors."""
        # Start with the correct headers and status code from the error
        response = e.get_response()
        # Replace the body with JSON
        response.data = json.dumps({
            'code': e.code,
            'name': e.name,
            'description': e.description,
        })
        response.content_type = 'application/json'
        return response


def register_cli_commands(app):
    @app.cli.command('init_db')
    def initialize_database():
        """Initialize the SQLite database."""
        database.drop_all()
        database.create_all()
        echo('Initializing the SQLite database!')

    @app.cli.command('fill_db')
    def fill_database():
        """Fill the SQLite database with initial data."""
        from project.models import Entry, User

        # Add a default set of users to the database
        new_users = [
            User(email='pkennedy@hey.com', password_plaintext='FlaskIsAwesome123'),
            User(email='patkennedy79@gmail.com', password_plaintext='FlaskIsTheBest456')
        ]
        for user in new_users:
            database.session.add(user)

        # Add a default set of journal entries to the database
        new_entries = [
            Entry(entry='The sun was shining when I woke up this morning.', user_id=1),
            Entry(entry='I tried a new fruit mixture in my oatmeal for breakfast.', user_id=1),
            Entry(entry='Today I ate a great sandwich for lunch.', user_id=2)
        ]
        for entry in new_entries:
            database.session.add(entry)

        database.session.commit()
        echo(f'Filled the SQLite database with {len(new_users)} users and {len(new_entries)} entries!')
