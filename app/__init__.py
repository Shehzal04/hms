import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from app.models.base import db
from app.models.user import User
from app.models.complaint import Complaint
from app.models.communication import Notification
from config import config_by_name

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'
migrate = Migrate()
csrf = CSRFProtect()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Ensure upload folders exist
    for sub in ['profiles', 'documents', 'complaints']:
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], sub), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.students import students_bp
    from app.routes.hostels import hostels_bp
    from app.routes.rooms import rooms_bp
    from app.routes.allocations import allocations_bp
    from app.routes.fees import fees_bp
    from app.routes.attendance import attendance_bp
    from app.routes.complaints import complaints_bp
    from app.routes.visitors import visitors_bp
    from app.routes.mess import mess_bp
    from app.routes.staff import staff_bp
    from app.routes.announcements import announcements_bp
    from app.routes.reports import reports_bp
    from app.routes.settings import settings_bp
    from app.routes.student_portal import student_portal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(hostels_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(allocations_bp)
    app.register_blueprint(fees_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(complaints_bp)
    app.register_blueprint(visitors_bp)
    app.register_blueprint(mess_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(announcements_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(student_portal_bp)

    # Context Processors
    @app.context_processor
    def inject_global_data():
        from flask_login import current_user
        notifs = []
        unread_count = 0
        pending_complaints_count = 0
        if current_user.is_authenticated:
            notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
            unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            if not current_user.is_student:
                pending_complaints_count = Complaint.query.filter_by(status='Pending').count()

        return {
            'app_name': 'HostelFlow HMS',
            'unread_notifs_count': unread_count,
            'recent_notifications': notifs,
            'pending_complaints_count': pending_complaints_count
        }

    # Custom Jinja Filters
    @app.template_filter('currency')
    def currency_filter(value):
        try:
            return f"Rs. {float(value):,.0f}"
        except (ValueError, TypeError):
            return "Rs. 0"

    @app.template_filter('date_format')
    def date_format_filter(value, fmt='%d-%b-%Y'):
        if value:
            return value.strftime(fmt)
        return 'N/A'

    @app.template_filter('datetime_format')
    def datetime_format_filter(value, fmt='%d-%b-%Y %I:%M %p'):
        if value:
            return value.strftime(fmt)
        return 'N/A'

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
