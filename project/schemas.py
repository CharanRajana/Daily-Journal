from project import ma


# -------
# Schemas
# -------

class NewEntrySchema(ma.Schema):
    """Schema defining the attributes when creating a new journal entry."""
    entry = ma.String(required=True)


class EntrySchema(ma.Schema):
    """Schema defining the attributes in a journal entry."""
    id = ma.Integer()
    entry = ma.String()
    user_id = ma.Integer()
    created_on = ma.DateTime()
    last_edited_on = ma.DateTime()


class NewUserSchema(ma.Schema):
    """Schema defining the attributes when creating a new user."""
    email = ma.String(required=True)
    password_plaintext = ma.String(required=True)


class UserSchema(ma.Schema):
    """Schema defining the attributes of a user."""
    id = ma.Integer()
    email = ma.String()
    registered_on = ma.DateTime()
    email_confirmation_sent_on = ma.DateTime()
    email_confirmed = ma.Boolean()
    email_confirmed_on = ma.DateTime()


class TokenSchema(ma.Schema):
    """Schema defining the attributes of a token."""
    token = ma.String()


class ChangePasswordSchema(ma.Schema):
    """Schema defining the attributes for changing a user's password."""
    old_password_plaintext = ma.String(required=True)
    new_password_plaintext = ma.String(required=True)


class EmailSchema(ma.Schema):
    """Schema defining the attributes for specifying an email address."""
    email = ma.String(required=True)
