from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.base import db
from app.models.user import User, Role
from app.models.system import AuditLog, HostelSetting
from app.forms.auth import UserForm
from app.services.auth_service import role_required, log_audit

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
@login_required
@role_required('Super Admin')
def general_settings():
    settings = HostelSetting.query.order_by(HostelSetting.category.asc()).all()
    return render_template('settings/general.html', settings=settings)


@settings_bp.route('/save', methods=['POST'])
@login_required
@role_required('Super Admin')
def save_settings():
    settings = HostelSetting.query.all()
    for s in settings:
        val = request.form.get(s.key_name)
        if val is not None:
            s.value = val.strip()
    db.session.commit()
    log_audit('UPDATE_SETTINGS', 'HostelSetting', None, 'Updated system settings')
    flash('System settings updated successfully!', 'success')
    return redirect(url_for('settings.general_settings'))


@settings_bp.route('/users')
@login_required
@role_required('Super Admin')
def list_users():
    users = User.query.order_by(User.role_id.asc(), User.username.asc()).all()
    return render_template('settings/users.html', users=users)


@settings_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin')
def add_user():
    form = UserForm()
    roles = Role.query.all()
    form.role_id.choices = [(r.id, r.name) for r in roles]

    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data.strip().lower()).first():
            flash('Username already taken.', 'danger')
            return render_template('settings/user_add_edit.html', form=form, title='Add User')

        if User.query.filter_by(email=form.email.data.strip().lower()).first():
            flash('Email already registered.', 'danger')
            return render_template('settings/user_add_edit.html', form=form, title='Add User')

        user = User(
            username=form.username.data.strip().lower(),
            email=form.email.data.strip().lower(),
            full_name=form.full_name.data.strip(),
            role_id=form.role_id.data,
            is_active=form.is_active.data
        )
        pwd = form.password.data.strip() if form.password.data else 'Pass@12345'
        user.set_password(pwd)
        db.session.add(user)
        db.session.commit()
        log_audit('CREATE_USER', 'User', user.id, f"Created system user {user.username} ({user.role.name})")
        flash(f"User {user.username} created successfully!", 'success')
        return redirect(url_for('settings.list_users'))

    return render_template('settings/user_add_edit.html', form=form, title='Add System User')


@settings_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@role_required('Super Admin')
def toggle_user_status(user_id):
    if user_id == current_user.id:
        flash('You cannot disable your own active super admin account!', 'warning')
        return redirect(url_for('settings.list_users'))

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"User {user.username} is now {'Active' if user.is_active else 'Disabled'}.", 'info')
    return redirect(url_for('settings.list_users'))


@settings_bp.route('/audit-logs')
@login_required
@role_required('Super Admin', 'Hostel Admin')
def audit_logs():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()

    query = AuditLog.query
    if action_filter:
        query = query.filter(AuditLog.action.ilike(f"%{action_filter}%"))

    pagination = query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=30, error_out=False)
    return render_template('settings/audit_logs.html', pagination=pagination, logs=pagination.items, action_filter=action_filter)
