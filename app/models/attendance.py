from datetime import date, datetime
from app.models.base import db, TimestampMixin

class StudentAttendance(TimestampMixin, db.Model):
    __tablename__ = 'student_attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    status = db.Column(db.String(20), nullable=False, default='Present')  # Present, Absent, Leave
    remarks = db.Column(db.String(255))
    marked_by = db.Column(db.String(100), default='Warden')

    student = db.relationship('Student', back_populates='attendance_records')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'date', name='uix_student_attendance_date'),
    )

    def __repr__(self):
        return f'<Attendance Student:{self.student_id} Date:{self.date} Status:{self.status}>'


class LateEntry(TimestampMixin, db.Model):
    __tablename__ = 'late_entries'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    entry_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expected_time = db.Column(db.String(20), default='10:00 PM')
    actual_time = db.Column(db.String(20))
    reason = db.Column(db.Text, nullable=False)
    recorded_by = db.Column(db.String(100), default='Security Guard')
    remarks = db.Column(db.String(255))

    student = db.relationship('Student', back_populates='late_entries')

    def __repr__(self):
        return f'<LateEntry Student:{self.student_id} Time:{self.actual_time}>'
