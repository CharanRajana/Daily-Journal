import os

import click
import requests


BASE_URL = os.getenv('FLASK_JOURNAL_API_BASEURL', default='http://127.0.0.1:5000/')


# ----------------
# Helper Functions
# ----------------

def get_authentication_token():
    """Returns the authentication token from the `FLASK_JOURNAL_API_TOKEN` environment variable."""
    if 'FLASK_JOURNAL_API_TOKEN' not in os.environ:
        click.echo('Flask Journal API token was not found in the environment variables!')
        click.echo('Request the authentication token from the Flask Journal API via the /users/get-auth-token URL.')
        return

    return os.environ['FLASK_JOURNAL_API_TOKEN']


# ------------
# CLI Commands
# ------------

@click.group()
def cli():
    pass


@click.command()
@click.option('--message', help='New journal entry')
def add_entry(message):
    """Add a new journal entry via the Flask Journal API."""
    auth_token = get_authentication_token()

    if auth_token is None:
        click.echo('Error! Cannot access the Flask Journal API without authentication token.')
        return

    headers = {'Authorization': f'Bearer {auth_token}'}
    post_data = {'entry': message}
    r = requests.post(BASE_URL + 'journal/', json=post_data, headers=headers)
    click.echo(f'Status code: {r.status_code}')
    click.echo(r.text)


@click.command()
def journal():
    """Prints all the journal entries from the Flask Journal API."""
    auth_token = get_authentication_token()

    if auth_token is None:
        click.echo('Error! Cannot access the Flask Journal API without authentication token.')
        return

    headers = {'Authorization': f'Bearer {auth_token}'}
    r = requests.get(BASE_URL + 'journal/', headers=headers)
    click.echo(f'Status code: {r.status_code}')
    if r.status_code == 200:
        click.echo('Journal entries:')
        click.echo(r.text)


@click.command()
@click.option('--entry_id', help='ID of journal entry to update')
@click.option('--message', help='Updated journal entry')
def update_entry(entry_id, message):
    """Update a journal entry via the Flask Journal API."""
    auth_token = get_authentication_token()

    if auth_token is None:
        click.echo('Error! Cannot access the Flask Journal API without authentication token.')
        return

    headers = {'Authorization': f'Bearer {auth_token}'}
    put_data = {'entry': message}
    r = requests.put(BASE_URL + f'journal/{entry_id}', json=put_data, headers=headers)
    click.echo(f'Status code: {r.status_code}')
    if r.status_code == 200:
        click.echo('Journal entry:')
        click.echo(r.text)


@click.command()
@click.option('--entry_id', help='ID of journal entry to delete')
def delete_entry(entry_id):
    """Delete a journal entry via the Flask Journal API."""
    auth_token = get_authentication_token()

    if auth_token is None:
        click.echo('Error! Cannot access the Flask Journal API without authentication token.')
        return

    headers = {'Authorization': f'Bearer {auth_token}'}
    r = requests.delete(BASE_URL + f'journal/{entry_id}', headers=headers)
    click.echo(f'Status code: {r.status_code}')


@click.command()
@click.option('--email', help='Email of the new user')
@click.option('--password', help='Password of the new user')
def register_user(email, password):
    """Register a new user via the Flask Journal API."""
    post_data = {'email': email, 'password_plaintext': password}
    r = requests.post(BASE_URL + 'users/', json=post_data)
    click.echo(f'Status code: {r.status_code}')
    click.echo(r.text)


@click.command()
@click.option('--email', help='Email of the new user')
@click.option('--password', help='Password of the new user')
def get_auth_token(email, password):
    """Get the authentication token for a user via the Flask Journal API."""
    r = requests.post(BASE_URL + 'users/get-auth-token', auth=(email, password))
    click.echo(f'Status code: {r.status_code}')
    if r.status_code == 200:
        auth_token = r.json()['token']
        click.echo(f'Authentication token: {auth_token}')
        click.echo('This token should be saved to the FLASK_JOURNAL_API_TOKEN environment variable:')
        click.echo("    Mac OS/Linux: export FLASK_JOURNAL_API_TOKEN='<token>'")
        click.echo("    Windows: set FLASK_JOURNAL_API_TOKEN='<token>'")


@click.command()
def user_profile():
    """Print the user profile from the Flask Journal API."""
    auth_token = get_authentication_token()

    if auth_token is None:
        click.echo('Error! Cannot access the Flask Journal API without authentication token.')
        return

    headers = {'Authorization': f'Bearer {auth_token}'}
    r = requests.get(BASE_URL + 'users/account', headers=headers)
    click.echo(f'Status code: {r.status_code}')
    if r.status_code == 200:
        click.echo('User Profile:')
        click.echo(r.text)


@click.command()
@click.option('--old_password', help='Current password to be replaced')
@click.option('--new_password', help='New password')
def change_password(old_password, new_password):
    """Change the password via the Flask Journal API."""
    auth_token = get_authentication_token()

    if auth_token is None:
        click.echo('Error! Cannot access the Flask Journal API without authentication token.')
        return

    headers = {'Authorization': f'Bearer {auth_token}'}
    put_data = {'old_password_plaintext': old_password, 'new_password_plaintext': new_password}
    r = requests.put(BASE_URL + 'users/account', json=put_data, headers=headers)
    click.echo(f'Status code: {r.status_code}')
    if r.status_code == 200:
        click.echo('User Data:')
        click.echo(r.text)


@click.command()
def resend_email_confirmation_link():
    """Re-send the email confirmation link from the Flask Journal API."""
    auth_token = get_authentication_token()

    if auth_token is None:
        click.echo('Error! Cannot access the Flask Journal API without authentication token.')
        return

    headers = {'Authorization': f'Bearer {auth_token}'}
    r = requests.get(BASE_URL + 'users/resend_email_confirmation', headers=headers)
    click.echo(f'Status code: {r.status_code}')
    if r.status_code == 200:
        click.echo('User Profile:')
        click.echo(r.text)


@click.command()
@click.option('--email', help='Email of the new user')
def forgot_password(email):
    """Request an email link to reset your password the Flask Journal API."""
    put_data = {'email': email}
    r = requests.put(BASE_URL + 'users/forgot-password', json=put_data)
    click.echo(f'Status code: {r.status_code}')
    if r.status_code == 200:
        click.echo(r.text)


cli.add_command(add_entry)
cli.add_command(journal)
cli.add_command(update_entry)
cli.add_command(delete_entry)
cli.add_command(register_user)
cli.add_command(get_auth_token)
cli.add_command(user_profile)
cli.add_command(change_password)
cli.add_command(resend_email_confirmation_link)
cli.add_command(forgot_password)


if __name__ == '__main__':
    cli()
