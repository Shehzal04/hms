from datetime import datetime, date
from app.models.base import db, TimestampMixin

class Announcement(TimestampMixin, db.Model):
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    content = db.Column(db.Text, nullable=False)
    target_audience = db.Column(db.String(50), default='All')  # All, Students, Staff, Wardens
    priority = db.Column(db.String(20), default='Normal')  # Normal, Important, Urgent
    author_name = db.Column(db.String(100), default='Hostel Administration')
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.Date)

    def __repr__(self):
        return f'<Announcement {self.title}>'


class Notification(TimestampMixin, db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f'<Notification User:{self.user_id} - {self.title}>'
