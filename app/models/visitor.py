from datetime import datetime
from app.models.base import db, TimestampMixin

class Visitor(TimestampMixin, db.Model):
    __tablename__ = 'visitors'

    id = db.Column(db.Integer, primary_key=True)
    visitor_name = db.Column(db.String(120), nullable=False)
    cnic = db.Column(db.String(25), nullable=False, index=True)
    phone_number = db.Column(db.String(25), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    relation = db.Column(db.String(50), nullable=False)  # Father, Mother, Brother, Friend, Guardian, Other
    purpose = db.Column(db.String(255), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    check_out = db.Column(db.DateTime)
    id_verified = db.Column(db.Boolean, default=True)
    security_officer = db.Column(db.String(100), default='Main Gate Security')
    remarks = db.Column(db.Text)

    student = db.relationship('Student', back_populates='visitors')

    @property
    def is_currently_inside(self):
        return self.check_out is None

    def __repr__(self):
        return f'<Visitor {self.visitor_name} visited Student {self.student_id}>'
