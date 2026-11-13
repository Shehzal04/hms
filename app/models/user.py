from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.base import db, TimestampMixin

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    users = db.relationship('User', back_populates='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    avatar = db.Column(db.String(255), default='default_avatar.png')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    role = db.relationship('Role', back_populates='users')

    # Relationships
    student_profile = db.relationship('Student', back_populates='user', uselist=False)
    employee_profile = db.relationship('Employee', back_populates='user', uselist=False)
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        return self.role is not None and self.role.name.lower() == role_name.lower()

    @property
    def is_super_admin(self):
        return self.has_role('Super Admin')

    @property
    def is_hostel_admin(self):
        return self.has_role('Hostel Admin')

    @property
    def is_warden(self):
        return self.has_role('Warden')

    @property
    def is_accountant(self):
        return self.has_role('Accountant')

    @property
    def is_student(self):
        return self.has_role('Student')

    @property
    def is_staff(self):
        return self.has_role('Staff')

    @property
    def can_manage_hostel(self):
        return self.is_super_admin or self.is_hostel_admin

    @property
    def can_view_admin_panel(self):
        return self.is_super_admin or self.is_hostel_admin or self.is_warden or self.is_accountant

    def unread_notifications_count(self):
        return self.notifications.filter_by(is_read=False).count()

    def __repr__(self):
        return f'<User {self.username} ({self.role.name if self.role else "No Role"})>'
