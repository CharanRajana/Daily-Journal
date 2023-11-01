from datetime import datetime
from threading import Thread

from apifairy import authenticate, body, other_responses, response
from flask import (abort, copy_current_request_context, current_app,
                   render_template, request, url_for)
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from itsdangerous.exc import BadSignature
from sqlalchemy.exc import IntegrityError

from project import basic_auth, database, mail, token_auth
from project.models import User
from project.schemas import (ChangePasswordSchema, EmailSchema, NewUserSchema,
                             TokenSchema, UserSchema)

from . import users_api_blueprint
from .forms import PasswordForm


# ----------------
# Helper Functions
# ----------------

def generate_confirmation_email(user_email):
    confirm_serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    confirm_url = url_for('users_api.confirm_email',
                          token=confirm_serializer.dumps(user_email, salt='email-confirmation-salt'),
                          _external=True)

    return Message(subject='Flask Journal API - Confirm Your Email Address',
                   html=render_template('users_api/email_confirmation.html', confirm_url=confirm_url),
                   recipients=[user_email])


def generate_password_reset_email(user_email):
    password_reset_serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    password_reset_url = url_for('users_api.process_password_reset_token',
                                 token=password_reset_serializer.dumps(user_email, salt='password-reset-salt'),
                                 _external=True)

    return Message(subject='Flask Journal API - Password Reset Requested',
                   html=render_template('users_api/email_password_reset.html', password_reset_url=password_reset_url),
                   recipients=[user_email])


# -------
# Schemas
# -------

new_user_schema = NewUserSchema()
user_schema = UserSchema()
token_schema = TokenSchema()
change_password_schema = ChangePasswordSchema()
email_schema = EmailSchema()


# ------
# Routes
# ------

@users_api_blueprint.route('/', methods=['POST'])
@body(new_user_schema)
@response(user_schema, 201)
@other_responses({400: 'Bad Request'})
def register(kwargs):
    """Create a new user"""
    try:
        new_user = User(**kwargs)
        database.session.add(new_user)
        database.session.commit()
    except IntegrityError:
        database.session.rollback()
        abort(400)

    @copy_current_request_context
    def send_email(message):
        with current_app.app_context():
            mail.send(message)

    # Email to confirm the new user's email address
    msg = generate_confirmation_email(new_user.email)
    email_thread = Thread(target=send_email, args=[msg])
    email_thread.start()

    return new_user


@users_api_blueprint.route('/get-auth-token', methods=['POST'])
@authenticate(basic_auth)
@response(token_schema)
@other_responses({401: 'Invalid username or password'})
def get_auth_token():
    """Get authentication token"""
    user = basic_auth.current_user()
    token = user.generate_auth_token()
    database.session.add(user)
    database.session.commit()
    return dict(token=token)


@users_api_blueprint.route('/account', methods=['GET'])
@authenticate(token_auth)
@response(user_schema)
def user_profile():
    """Retrieve the user profile"""
    return token_auth.current_user()


@users_api_blueprint.route('/account', methods=['PUT'])
@authenticate(token_auth)
@body(change_password_schema)
@response(user_schema)
@other_responses({400: 'Bad Request'})
def change_password(data):
    """Change the password"""
    user = token_auth.current_user()
    if not user.is_password_correct(data['old_password_plaintext']):
        abort(400)

    # Update the password and revoke the authentication token to require
    # the user to get a new authorization token using the new password
    user.set_password(data['new_password_plaintext'])
    user.revoke_auth_token()
    database.session.add(user)
    database.session.commit()
    return user


@users_api_blueprint.route('/confirm/<token>')
def confirm_email(token):
    try:
        confirm_serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        email = confirm_serializer.loads(token, salt='email-confirmation-salt', max_age=3600)
    except BadSignature:
        current_app.logger.info(f'Invalid or expired confirmation link received from IP address: {request.remote_addr}')
        return render_template("users_api/email_confirmation_invalid.html")

    user = User.query.filter_by(email=email).first()

    if user.email_confirmed:
        current_app.logger.info(f'Confirmation link received for a confirmed user: {user.email}')
        return render_template("users_api/email_confirmation_duplicate.html")

    user.email_confirmed = True
    user.email_confirmed_on = datetime.now()
    database.session.add(user)
    database.session.commit()
    current_app.logger.info(f'Email address confirmed for: {user.email}')
    return render_template("users_api/email_confirmed.html")


@users_api_blueprint.route('/resend_email_confirmation', methods=['GET'])
@authenticate(token_auth)
@response(user_schema)
@other_responses({400: 'Email already confirmed'})
def resend_email_confirmation():
    """Resend email confirmation link"""
    user = token_auth.current_user()

    # Check if the user's email has already been confirmed
    if user.email_confirmed:
        abort(400)

    @copy_current_request_context
    def send_email(message):
        with current_app.app_context():
            mail.send(message)

    # Email to confirm the new user's email address
    msg = generate_confirmation_email(user.email)
    email_thread = Thread(target=send_email, args=[msg])
    email_thread.start()

    # Record that the email confirmation was sent again
    user.confirmation_email_link_sent()
    database.session.add(user)
    database.session.commit()
    return user


@users_api_blueprint.route('/forgot-password', methods=['PUT'])
@body(email_schema)
@other_responses({400: 'Bad Request'})
def forgot_password(data):
    """Send email link to change password"""
    user = User.query.filter_by(email=data['email']).first()

    if user is None:
        current_app.logger.info(f"Forgot password requested for invalid email address: {data['email']}")
        abort(400)

    if not user.email_confirmed:
        current_app.logger.info(f"Forgot password requested for user {data['email']} without a confirmed email address.")
        abort(400, 'Password reset link cannot be sent to an unconfirmed email address.')

    @copy_current_request_context
    def send_email(email_message):
        with current_app.app_context():
            mail.send(email_message)

    # Send an email with a unique link for the user to reset their password
    message = generate_password_reset_email(user.email)
    email_thread = Thread(target=send_email, args=[message])
    email_thread.start()
    return {'message': 'Please check your email for a password reset link!'}, 200


@users_api_blueprint.route('/password_reset_via_token/<token>', methods=['GET', 'POST'])
def process_password_reset_token(token):
    """Process a password reset token that was emailed to a user."""
    try:
        password_reset_serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        email = password_reset_serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except BadSignature:
        current_app.logger.info('Processed password reset link that is invalid or has expired.')
        return render_template("users_api/password_reset_invalid.html")

    form = PasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()

        if user is None:
            return render_template("users_api/password_reset_invalid.html")

        user.set_password(form.password.data)
        database.session.add(user)
        database.session.commit()
        return render_template("users_api/password_updated.html")

    return render_template('users_api/reset_password_with_token.html', form=form)
