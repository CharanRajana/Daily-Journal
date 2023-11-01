import secrets
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash, generate_password_hash

from project import database


class Entry(database.Model):
    """
    Class that represents a journal entry.

    The following attributes of a journal entry are stored in this table:
        * entry - text of the journal entry
        * user_id - ID of the user that owns this journal entry
        * created_on - date and time (in UTC) when the journal entry was created
        * last_edited_on - date and time (in UTC) when the journal entry was last edited
    """
    __tablename__ = 'entries'

    id = database.Column(database.Integer, primary_key=True)
    entry = database.Column(database.String, nullable=False)
    user_id = database.Column(database.Integer, database.ForeignKey('users.id'))
    created_on = database.Column(database.DateTime)
    last_edited_on = database.Column(database.DateTime)

    def __init__(self, entry: str, user_id: int):
        """Create a new journal entry."""
        self.entry = entry
        self.user_id = user_id
        self.created_on = datetime.utcnow()
        self.last_edited_on = datetime.utcnow()

    def update(self, entry: str):
        """Update the journal entry."""
        self.entry = entry
        self.last_edited_on = datetime.utcnow()

    def __repr__(self):
        return f"<Entry: {self.entry}>"


class User(database.Model):
    """
    Class that represents a user of the application.

    The following attributes of a user are stored in this table:
        * email - email address of the user
        * hashed password - hashed password (using werkzeug.security)
        * authentication token - authentication token unique to the user
        * authentication token expiration - expiration date and time of
                                            the authentication token
        * registered_on - date and time (in UTC) when the user registered
        * email_confirmation_sent_on - date and time (in UTC) that the confirmation email was sent
        * email_confirmed - flag indicating if the user's email address has been confirmed
        * email_confirmed_on - date and time (in UTC) that the user's email address was confirmed

    REMEMBER: Never store the plaintext password in a database!
    """
    __tablename__ = 'users'

    id = database.Column(database.Integer, primary_key=True)
    email = database.Column(database.String, unique=True, nullable=False)
    password_hashed = database.Column(database.String(128), nullable=False)
    entries = database.relationship('Entry', backref='user', lazy='dynamic')
    auth_token = database.Column(database.String(64), index=True)
    auth_token_expiration = database.Column(database.DateTime)
    registered_on = database.Column(database.DateTime)
    email_confirmation_sent_on = database.Column(database.DateTime)
    email_confirmed = database.Column(database.Boolean, default=False)
    email_confirmed_on = database.Column(database.DateTime)
    user_type = database.Column(database.String(10), default='User')

    def __init__(self, email: str, password_plaintext: str, user_type: str = 'User'):
        """Create a new User object.

        This constructor assumes that an email is sent to the new user to confirm
        their email address at the same time that the user is registered.
        """
        self.email = email
        self.password_hashed = self._generate_password_hash(password_plaintext)
        self.auth_token = None
        self.auth_token_expiration = None
        self.registered_on = datetime.utcnow()
        self.email_confirmation_sent_on = datetime.utcnow()
        self.email_confirmed = False
        self.email_confirmed_on = None
        self.user_type = user_type

    def is_password_correct(self, password_plaintext: str):
        return check_password_hash(self.password_hashed, password_plaintext)

    def set_password(self, password_plaintext: str):
        self.password_hashed = self._generate_password_hash(password_plaintext)

    @staticmethod
    def _generate_password_hash(password_plaintext):
        return generate_password_hash(password_plaintext)

    def generate_auth_token(self):
        self.auth_token = secrets.token_urlsafe()
        self.auth_token_expiration = datetime.utcnow() + timedelta(minutes=60)
        return self.auth_token

    @staticmethod
    def verify_auth_token(auth_token):
        user = User.query.filter_by(auth_token=auth_token).first()
        if user and user.auth_token_expiration > datetime.utcnow():
            return user

    def revoke_auth_token(self):
        self.auth_token_expiration = datetime.utcnow()

    def confirm_email_address(self):
        self.email_confirmed = True
        self.email_confirmed_on = datetime.utcnow()

    def revoke_email_address_confirmation(self):
        self.email_confirmed = False
        self.email_confirmed_on = None

    def confirmation_email_link_sent(self):
        self.email_confirmation_sent_on = datetime.utcnow()

    def is_admin(self):
        return self.user_type == 'Admin'

    def get_roles(self):
        if self.user_type == 'Admin':
            return ['User', 'Admin']
        return ['User']

    def __repr__(self):
        return f'<User: {self.email}>'

    @property
    def is_authenticated(self):
        """Return True if the user has been successfully registered."""
        return True

    @property
    def is_active(self):
        """Always True, as all users are active."""
        return True

    @property
    def is_anonymous(self):
        """Always False, as anonymous users aren't supported."""
        return False

    def get_id(self):
        """Return the user ID as a unicode string (`str`)."""
        return str(self.id)
