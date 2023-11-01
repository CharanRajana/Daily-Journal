import functools

import click
from flask import (abort, current_app, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required, login_user, logout_user

from project import database
from project.models import Entry, User

from . import admin_blueprint
from .forms import LoginForm, PasswordForm


# ----------
# Decorators
# ----------

def admin_required(func):
    @functools.wraps(func)
    def wrapper_admin_required(*args, **kwargs):
        if current_user.user_type != 'Admin':
            abort(403)
        return func(*args, **kwargs)
    return wrapper_admin_required


# ------------
# CLI Commands
# ------------

@admin_blueprint.cli.command('create_admin_user')
@click.argument('email')
@click.argument('password')
def create(email, password):
    """Create a new admin user and add it to the database."""
    admin_user = User(email, password, user_type='Admin')
    database.session.add(admin_user)
    database.session.commit()
    click.echo(f'Created new admin user ({email})!')


# ------
# Routes
# ------

@admin_blueprint.route('/login', methods=['GET', 'POST'])
def admin_login():
    form = LoginForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.is_password_correct(form.password.data) and user.user_type == 'Admin':
                # Admin user's credentials have been validated, so log them in
                login_user(user, remember=form.remember_me.data)
                current_app.logger.info(f'Logged in user: {current_user.email}')
                return redirect(url_for('admin.admin_list_users'))

        flash('ERROR! Incorrect login credentials.', 'error')
    return render_template('admin/login.html', form=form)


@admin_blueprint.route('/logout')
@login_required
@admin_required
def admin_logout():
    current_app.logger.info(f'Logged out user: {current_user.email}')
    logout_user()
    flash('Goodbye!')
    return redirect(url_for('admin.admin_login'))


@admin_blueprint.route('/users/')
@login_required
@admin_required
def admin_list_users():
    """Display all users."""
    users = User.query.order_by(User.id).all()
    for user in users:
        user.number_of_journal_entries = len(Entry.query.filter_by(user_id=user.id).all())
    return render_template('admin/users.html', users=users)


@admin_blueprint.route('/users/<int:index>/confirm_email')
@login_required
@admin_required
def admin_confirm_email(index):
    """Confirm email address for the user."""
    user = User.query.filter_by(id=index).first_or_404()
    user.confirm_email_address()
    database.session.add(user)
    database.session.commit()
    flash(f'Email address confirmed for {user.email}', 'success')
    return redirect(url_for('admin.admin_list_users'))


@admin_blueprint.route('/users/<int:index>/unconfirm_email')
@login_required
@admin_required
def admin_unconfirm_email(index):
    """Un-confirm email address for the user."""
    user = User.query.filter_by(id=index).first_or_404()
    user.revoke_email_address_confirmation()
    database.session.add(user)
    database.session.commit()
    flash(f'Email address confirmation revoked for {user.email}', 'success')
    return redirect(url_for('admin.admin_list_users'))


@admin_blueprint.route('/users/<int:index>/change_password', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_change_password(index):
    """Change the password for the user."""
    form = PasswordForm()
    user = User.query.filter_by(id=index).first_or_404()

    if request.method == 'POST' and form.validate_on_submit():
        user.set_password(form.password.data)
        database.session.add(user)
        database.session.commit()
        flash(f'Password changed for {user.email}', 'success')
        return redirect(url_for('admin.admin_list_users'))
    return render_template('admin/change_password.html', form=form)


@admin_blueprint.route('/users/<int:index>/revoke_token')
@login_required
@admin_required
def admin_revoke_token(index):
    """Revoke the authentication token for the user."""
    user = User.query.filter_by(id=index).first_or_404()
    user.revoke_auth_token()
    database.session.add(user)
    database.session.commit()
    flash(f'Authentication token revoked for {user.email}', 'success')
    return redirect(url_for('admin.admin_list_users'))


@admin_blueprint.route('/users/<int:index>/delete_user')
@login_required
@admin_required
def admin_delete_user(index):
    """Delete the user and their journal entries."""
    user = User.query.filter_by(id=index).first_or_404()

    if user.user_type == 'Admin':
        flash(f'Cannot delete Administrator ({user.email})!', 'error')
        return redirect(url_for('admin.admin_list_users'))

    # First, delete all the journal entries associated with the user
    entries = Entry.query.filter_by(user_id=user.id).all()
    for entry in entries:
        database.session.delete(entry)

    # Second, delete the user
    database.session.delete(user)
    database.session.commit()
    flash(f'User ({user.email}) and their associated journal entries were deleted!', 'success')
    return redirect(url_for('admin.admin_list_users'))
