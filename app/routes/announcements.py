from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.base import db
from app.models.communication import Announcement, Notification
from app.models.user import User, Role
from app.forms.operations import AnnouncementForm
from app.services.auth_service import role_required, log_audit

announcements_bp = Blueprint('announcements', __name__, url_prefix='/announcements')

@announcements_bp.route('/')
@login_required
def list_announcements():
    query = Announcement.query
    if current_user.is_student:
        query = query.filter(
            Announcement.is_active == True,
            Announcement.target_audience.in_(['All', 'Students'])
        )
    elif current_user.is_staff:
        query = query.filter(
            Announcement.is_active == True,
            Announcement.target_audience.in_(['All', 'Staff'])
        )

    announcements = query.order_by(Announcement.priority.desc(), Announcement.created_at.desc()).all()
    return render_template('announcements/list.html', announcements=announcements)


@announcements_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def create_announcement():
    form = AnnouncementForm()
    if form.validate_on_submit():
        announcement = Announcement(
            title=form.title.data.strip(),
            content=form.content.data.strip(),
            target_audience=form.target_audience.data,
            priority=form.priority.data,
            author_name=current_user.full_name,
            is_active=form.is_active.data,
            expires_at=form.expires_at.data
        )
        db.session.add(announcement)
        db.session.flush()

        # Generate in-app notifications for users based on target_audience
        target_role = None
        if form.target_audience.data == 'Students':
            target_role = Role.query.filter_by(name='Student').first()
        elif form.target_audience.data == 'Staff':
            target_role = Role.query.filter_by(name='Staff').first()

        user_query = User.query.filter_by(is_active=True)
        if target_role:
            user_query = user_query.filter_by(role_id=target_role.id)

        target_users = user_query.all()
        for u in target_users:
            notif = Notification(
                user_id=u.id,
                title=f"Notice: {announcement.title}",
                message=announcement.content[:120] + "...",
                link="/announcements"
            )
            db.session.add(notif)

        db.session.commit()
        log_audit('CREATE_ANNOUNCEMENT', 'Announcement', announcement.id, f"Published notice: {announcement.title}")
        flash('Announcement published and notifications sent successfully!', 'success')
        return redirect(url_for('announcements.list_announcements'))

    return render_template('announcements/create.html', form=form)


@announcements_bp.route('/<int:announcement_id>/toggle', methods=['POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def toggle_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    announcement.is_active = not announcement.is_active
    db.session.commit()
    flash(f"Announcement marked as {'Active' if announcement.is_active else 'Archived'}.", 'info')
    return redirect(url_for('announcements.list_announcements'))


@announcements_bp.route('/<int:announcement_id>/delete', methods=['POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin')
def delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    title = announcement.title
    db.session.delete(announcement)
    db.session.commit()
    flash(f"Announcement '{title}' deleted.", 'info')
    return redirect(url_for('announcements.list_announcements'))
