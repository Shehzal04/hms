from datetime import date
from app.models.base import db, TimestampMixin

class Student(TimestampMixin, db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)
    student_id_code = db.Column(db.String(30), unique=True, nullable=False, index=True)  # e.g., 'HMS-2026-001'
    full_name = db.Column(db.String(120), nullable=False, index=True)
    father_name = db.Column(db.String(120), nullable=False)
    cnic = db.Column(db.String(25), nullable=False, unique=True, index=True)  # CNIC / B-Form
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    phone_number = db.Column(db.String(25), nullable=False)
    emergency_contact = db.Column(db.String(25), nullable=False)
    gender = db.Column(db.String(15), nullable=False, default='Male')  # Male, Female
    date_of_birth = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(60), nullable=False)
    university_name = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    degree_program = db.Column(db.String(100), nullable=False)  # BSCS, BSEE, BBA, MBBS, etc.
    semester = db.Column(db.String(20), nullable=False, default='1st')
    admission_date = db.Column(db.Date, nullable=False, default=date.today)
    profile_picture = db.Column(db.String(255), default='default_student.png')
    status = db.Column(db.String(20), nullable=False, default='Active')  # Active, Inactive, Suspended, Alumni

    # Relationships
    user = db.relationship('User', back_populates='student_profile')
    guardians = db.relationship('Guardian', back_populates='student', cascade='all, delete-orphan', lazy='dynamic')
    documents = db.relationship('Document', back_populates='student', cascade='all, delete-orphan', lazy='dynamic')
    room_allocations = db.relationship('RoomAllocation', back_populates='student', lazy='dynamic', cascade='all, delete-orphan')
    fee_invoices = db.relationship('FeeInvoice', back_populates='student', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='student', lazy='dynamic', cascade='all, delete-orphan')
    attendance_records = db.relationship('StudentAttendance', back_populates='student', lazy='dynamic', cascade='all, delete-orphan')
    late_entries = db.relationship('LateEntry', back_populates='student', lazy='dynamic', cascade='all, delete-orphan')
    complaints = db.relationship('Complaint', back_populates='student', lazy='dynamic', cascade='all, delete-orphan')
    visitors = db.relationship('Visitor', back_populates='student', lazy='dynamic', cascade='all, delete-orphan')
    mess_subscriptions = db.relationship('MessSubscription', back_populates='student', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def current_allocation(self):
        return self.room_allocations.filter_by(status='Active').first()

    @property
    def current_room(self):
        alloc = self.current_allocation
        return alloc.room if alloc else None

    @property
    def current_bed(self):
        alloc = self.current_allocation
        return alloc.bed if alloc else None

    @property
    def current_hostel(self):
        room = self.current_room
        return room.hostel if room else None

    @property
    def primary_guardian(self):
        return self.guardians.first()

    @property
    def total_invoiced(self):
        return sum(inv.total_amount for inv in self.fee_invoices.all())

    @property
    def total_paid(self):
        return sum(inv.paid_amount for inv in self.fee_invoices.all())

    @property
    def pending_balance(self):
        return max(0, self.total_invoiced - self.total_paid)

    @property
    def attendance_percentage(self):
        total = self.attendance_records.count()
        if total == 0:
            return 100.0
        present = self.attendance_records.filter(
            db.or_(StudentAttendance.status == 'Present', StudentAttendance.status == 'Leave')
        ).count()
        return round((present / total) * 100, 1)

    def __repr__(self):
        return f'<Student {self.student_id_code} - {self.full_name}>'


class Guardian(TimestampMixin, db.Model):
    __tablename__ = 'guardians'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)  # Father, Mother, Brother, Uncle, Guardian
    cnic = db.Column(db.String(25))
    phone_number = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.String(255))
    occupation = db.Column(db.String(100))

    student = db.relationship('Student', back_populates='guardians')

    def __repr__(self):
        return f'<Guardian {self.name} ({self.relationship})>'


class Document(TimestampMixin, db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    doc_title = db.Column(db.String(120), nullable=False)
    doc_type = db.Column(db.String(50), nullable=False)  # CNIC, Domicile, Admission Letter, Affidavit, Other
    file_path = db.Column(db.String(255), nullable=False)
    file_size_kb = db.Column(db.Integer, default=0)

    student = db.relationship('Student', back_populates='documents')

    def __repr__(self):
        return f'<Document {self.doc_title} ({self.doc_type})>'

from app.models.attendance import StudentAttendance
