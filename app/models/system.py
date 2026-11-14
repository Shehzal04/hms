from datetime import datetime
from app.models.base import db, TimestampMixin

class AuditLog(TimestampMixin, db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_email = db.Column(db.String(120))
    action = db.Column(db.String(100), nullable=False)  # CREATE_STUDENT, ALLOCATE_ROOM, RECORD_PAYMENT, etc.
    entity_type = db.Column(db.String(50))  # Student, Room, Payment, etc.
    entity_id = db.Column(db.String(50))
    ip_address = db.Column(db.String(50))
    details = db.Column(db.Text)

    user = db.relationship('User', back_populates='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_email}>'


class HostelSetting(TimestampMixin, db.Model):
    __tablename__ = 'hostel_settings'

    id = db.Column(db.Integer, primary_key=True)
    key_name = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.String(50), default='General')

    @classmethod
    def get_val(cls, key, default=''):
        item = cls.query.filter_by(key_name=key).first()
        return item.value if item else default

    def __repr__(self):
        return f'<Setting {self.key_name}={self.value}>'
