from functools import wraps
from flask import abort, flash, redirect, request, url_for
from flask_login import current_user
from app.models.base import db
from app.models.system import AuditLog
from app.models.communication import Notification

def role_required(*roles):
    """Decorator to enforce role-based access control."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            
            # Super Admin has overarching access to all views
            if current_user.is_super_admin:
                return f(*args, **kwargs)

            # Check if user role matches any allowed role
            user_role = current_user.role.name if current_user.role else ''
            if user_role not in roles:
                flash("You do not have administrative permission to access this resource.", "danger")
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_audit(action, entity_type=None, entity_id=None, details=None):
    """Record an audit trail event."""
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        user_email = current_user.email if current_user.is_authenticated else 'Anonymous/System'
        ip_addr = request.remote_addr if request else '127.0.0.1'

        log_entry = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            ip_address=ip_addr,
            details=details
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()


def send_notification(user_id, title, message, link=None):
    """Create an in-app notification for a given user."""
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link
        )
        db.session.add(notif)
        db.session.commit()
        return notif
    except Exception:
        db.session.rollback()
        return None
