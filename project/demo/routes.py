from datetime import datetime

from apifairy import body, other_responses, response
from flask import abort

from project.schemas import EntrySchema, NewEntrySchema

from . import demo_api_blueprint


# -------
# Schemas
# -------

new_entry_schema = NewEntrySchema()
entry_schema = EntrySchema()
entries_schema = EntrySchema(many=True)


# ----------------------
# Demonstration Database
# ----------------------

demo_entries = [
    {'id': 1,
     'entry': 'I went for a great walk at the park today.',
     'user_id': 0,
     'created_on': datetime.fromisoformat('2022-07-01T04:29:50.307527'),
     'last_edited_on': datetime.fromisoformat('2022-07-01T04:29:50.307527')},
    {'id': 2,
     'entry': 'I tried a new pasta recipe for dinner tonight.',
     'user_id': 0,
     'created_on': datetime.fromisoformat('2022-07-02T06:29:50.307527'),
     'last_edited_on': datetime.fromisoformat('2022-07-02T06:29:50.307527')},
    {'id': 3,
     'entry': 'There was a great new movie on Netflix that I watched tonight.',
     'user_id': 0,
     'created_on': datetime.fromisoformat('2022-07-02T07:29:50.307527'),
     'last_edited_on': datetime.fromisoformat('2022-07-02T07:29:50.307527')},
    {'id': 4,
     'entry': 'There was so much fresh fruit at the grocery store, so I made a great fruit salad with dinner.',
     'user_id': 0,
     'created_on': datetime.fromisoformat('2022-07-02T14:29:50.307527'),
     'last_edited_on': datetime.fromisoformat('2022-07-02T14:29:50.307527')},
    {'id': 5,
     'entry': 'I got an email from an old friend today that was a really nice surprise.',
     'user_id': 0,
     'created_on': datetime.fromisoformat('2022-07-03T17:29:50.307527'),
     'last_edited_on': datetime.fromisoformat('2022-07-03T17:29:50.307527')},
]


# ------
# Routes
# ------

@demo_api_blueprint.route('/journal/', methods=['GET'])
@response(entries_schema)
def demo_journal():
    """Return journal entries (demo)"""
    return demo_entries


@demo_api_blueprint.route('/journal/', methods=['POST'])
@body(new_entry_schema)
@response(entry_schema, 201)
def demo_add_journal_entry(kwargs):
    """Add a new journal entry (demo)"""
    new_message = {
        'id': len(demo_entries) + 1,
        'entry': kwargs['entry'],
        'user_id': 0,
        'created_on': datetime.utcnow(),
        'last_edited_on': datetime.utcnow()
    }
    return new_message


@demo_api_blueprint.route('/journal/<int:index>', methods=['GET'])
@response(entry_schema)
@other_responses({404: 'Entry not found'})
def demo_get_journal_entry(index):
    """Retrieve a journal entry (demo)"""

    # Range of valid indices (argument): 1...5
    # Range of `demo_entries` entries: 0...4
    if index == 0 or index > len(demo_entries):
        abort(404)
    return demo_entries[index - 1]


@demo_api_blueprint.route('/journal/<int:index>', methods=['PUT'])
@body(new_entry_schema)
@response(entry_schema)
@other_responses({404: 'Entry not found'})
def demo_update_journal_entry(kwargs, index):
    """Update a journal entry (demo)"""

    # Range of valid indices (argument): 1...5
    # Range of `demo_entries` entries: 0...4
    if index == 0 or index > len(demo_entries):
        abort(404)
    entry = demo_entries[index - 1]
    entry['entry'] = kwargs['entry']
    return entry


@demo_api_blueprint.route('/journal/<int:index>', methods=['DELETE'])
@other_responses({404: 'Entry not found'})
def demo_delete_journal_entry(index):
    """Delete a journal entry (demo)"""
    if index == 0 or index > len(demo_entries):
        abort(404)
    return '', 204
