from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.base import db
from app.models.user import User, Role
from app.forms.auth import LoginForm, ChangePasswordForm
from app.services.auth_service import log_audit

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_student:
            return redirect(url_for('student_portal.dashboard'))
        elif current_user.is_staff:
            return redirect(url_for('staff.my_duties'))
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user_identifier = form.username_or_email.data.strip()
        user = User.query.filter(
            (User.username == user_identifier) | (User.email == user_identifier)
        ).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account is currently disabled. Please contact the administrator.', 'danger')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            log_audit('LOGIN', 'User', user.id, f'Successful login for {user.username}')
            flash(f'Welcome back, {user.full_name}!', 'success')

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            
            if user.is_student:
                return redirect(url_for('student_portal.dashboard'))
            elif user.is_staff:
                return redirect(url_for('staff.my_duties'))
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username/email or password. Please try again.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    log_audit('LOGOUT', 'User', current_user.id, f'User logged out: {current_user.username}')
    logout_user()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Your current password does not match.', 'danger')
            return render_template('auth/change_password.html', form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()
        log_audit('CHANGE_PASSWORD', 'User', current_user.id, 'User changed password')
        flash('Your password has been updated successfully!', 'success')
        return redirect(url_for('dashboard.index') if not current_user.is_student else url_for('student_portal.dashboard'))

    return render_template('auth/change_password.html', form=form)
