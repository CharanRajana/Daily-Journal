from apifairy import authenticate, body, other_responses, response
from flask import abort

from project import database, token_auth
from project.models import Entry
from project.schemas import EntrySchema, NewEntrySchema

from . import journal_api_blueprint


# -------
# Schemas
# -------

new_entry_schema = NewEntrySchema()
entry_schema = EntrySchema()
entries_schema = EntrySchema(many=True)


# ------
# Routes
# ------

@journal_api_blueprint.route('/', methods=['GET'])
@authenticate(token_auth)
@response(entries_schema)
def journal():
    """Return journal entries"""
    user = token_auth.current_user()
    return Entry.query.filter_by(user_id=user.id).all()


@journal_api_blueprint.route('/', methods=['POST'])
@authenticate(token_auth)
@body(new_entry_schema)
@response(entry_schema, 201)
def add_journal_entry(kwargs):
    """Add a new journal entry"""
    user = token_auth.current_user()
    new_message = Entry(user_id=user.id, **kwargs)
    database.session.add(new_message)
    database.session.commit()
    return new_message


@journal_api_blueprint.route('/<int:index>', methods=['GET'])
@authenticate(token_auth)
@response(entry_schema)
@other_responses({403: 'Forbidden', 404: 'Entry not found'})
def get_journal_entry(index):
    """Return a journal entry"""
    user = token_auth.current_user()
    entry = Entry.query.filter_by(id=index).first_or_404()

    if entry.user_id != user.id:
        abort(403)
    return entry


@journal_api_blueprint.route('/<int:index>', methods=['PUT'])
@authenticate(token_auth)
@body(new_entry_schema)
@response(entry_schema)
@other_responses({403: 'Forbidden', 404: 'Entry not found'})
def update_journal_entry(data, index):
    """Update a journal entry"""
    user = token_auth.current_user()
    entry = Entry.query.filter_by(id=index).first_or_404()

    if entry.user_id != user.id:
        abort(403)

    entry.update(data['entry'])
    database.session.add(entry)
    database.session.commit()
    return entry


@journal_api_blueprint.route('/<int:index>', methods=['DELETE'])
@authenticate(token_auth)
@other_responses({403: 'Forbidden', 404: 'Entry not found'})
def delete_journal_entry(index):
    """Delete a journal entry"""
    user = token_auth.current_user()
    entry = Entry.query.filter_by(id=index).first_or_404()

    if entry.user_id != user.id:
        abort(403)

    database.session.delete(entry)
    database.session.commit()
    return '', 204
