from datetime import date
from app.models.base import db, TimestampMixin

class Employee(TimestampMixin, db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)
    employee_code = db.Column(db.String(30), unique=True, nullable=False, index=True)  # e.g., 'EMP-101'
    full_name = db.Column(db.String(120), nullable=False)
    designation = db.Column(db.String(80), nullable=False)  # Warden, Security Guard, Cleaner, Electrician, Maintenance Staff, Mess Staff, Accountant
    cnic = db.Column(db.String(25), nullable=False, unique=True)
    phone_number = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.String(255), nullable=False)
    joining_date = db.Column(db.Date, nullable=False, default=date.today)
    salary = db.Column(db.Numeric(10, 2), nullable=False, default=35000.00)
    duty_shift = db.Column(db.String(50), default='Morning (8:00 AM - 4:00 PM)')
    status = db.Column(db.String(20), default='Active')  # Active, On Leave, Resigned, Terminated

    user = db.relationship('User', back_populates='employee_profile')
    assigned_complaints = db.relationship('Complaint', back_populates='assigned_employee', lazy='dynamic')
    tasks = db.relationship('Task', back_populates='employee', cascade='all, delete-orphan', lazy='dynamic')
    attendance = db.relationship('EmployeeAttendance', back_populates='employee', cascade='all, delete-orphan', lazy='dynamic')
    salaries = db.relationship('EmployeeSalary', back_populates='employee', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<Employee {self.employee_code} - {self.full_name} ({self.designation})>'


class EmployeeAttendance(TimestampMixin, db.Model):
    __tablename__ = 'employee_attendance'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    status = db.Column(db.String(20), nullable=False, default='Present')  # Present, Absent, Leave, Half Day
    remarks = db.Column(db.String(255))

    employee = db.relationship('Employee', back_populates='attendance')

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'date', name='uix_employee_attendance_date'),
    )

    def __repr__(self):
        return f'<EmpAttendance Emp:{self.employee_id} Date:{self.date} Status:{self.status}>'


class EmployeeSalary(TimestampMixin, db.Model):
    __tablename__ = 'employee_salaries'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    month = db.Column(db.String(20), nullable=False)  # e.g., 'November'
    year = db.Column(db.Integer, nullable=False)  # e.g., 2026
    base_salary = db.Column(db.Numeric(10, 2), nullable=False)
    bonus = db.Column(db.Numeric(10, 2), default=0.00)
    deductions = db.Column(db.Numeric(10, 2), default=0.00)
    net_salary = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.String(50), default='Bank Transfer')
    status = db.Column(db.String(20), default='Paid')  # Paid, Pending

    employee = db.relationship('Employee', back_populates='salaries')

    def __repr__(self):
        return f'<Salary Emp:{self.employee_id} {self.month} {self.year} Rs.{self.net_salary}>'


class Task(TimestampMixin, db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='Medium')  # Low, Medium, High, Urgent
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Pending')  # Pending, In Progress, Completed
    assigned_by = db.Column(db.String(100), default='Hostel Admin')
    completion_notes = db.Column(db.Text)

    employee = db.relationship('Employee', back_populates='tasks')

    def __repr__(self):
        return f'<Task {self.title} -> {self.employee.full_name if self.employee else ""}>'
