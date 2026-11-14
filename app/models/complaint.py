from datetime import datetime
from app.models.base import db, TimestampMixin

class Complaint(TimestampMixin, db.Model):
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Electricity, Water, Internet, Room Maintenance, Cleaning, Food / Mess, Security, Other
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255))
    priority = db.Column(db.String(20), nullable=False, default='Medium')  # Low, Medium, High, Urgent
    status = db.Column(db.String(20), nullable=False, default='Pending')  # Pending, In Progress, Resolved, Rejected
    assigned_to_employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    admin_response = db.Column(db.Text)
    student_feedback = db.Column(db.Text)
    student_rating = db.Column(db.Integer)  # 1 to 5 stars
    resolved_at = db.Column(db.DateTime)

    student = db.relationship('Student', back_populates='complaints')
    assigned_employee = db.relationship('Employee', back_populates='assigned_complaints')
    updates = db.relationship('ComplaintUpdate', back_populates='complaint', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<Complaint {self.ticket_number} ({self.status})>'


class ComplaintUpdate(TimestampMixin, db.Model):
    __tablename__ = 'complaint_updates'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    updated_by = db.Column(db.String(100), nullable=False)
    action_note = db.Column(db.Text, nullable=False)
    status_change = db.Column(db.String(50))

    complaint = db.relationship('Complaint', back_populates='updates')

    def __repr__(self):
        return f'<ComplaintUpdate {self.id} for {self.complaint_id}>'
