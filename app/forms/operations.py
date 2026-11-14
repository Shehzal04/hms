from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, IntegerField, DecimalField, SelectField, TextAreaField,
    DateField, DateTimeLocalField, SubmitField, BooleanField, EmailField
)
from wtforms.validators import DataRequired, NumberRange, Length, Optional, Email

# Allocation Forms
class AllocationForm(FlaskForm):
    student_id = SelectField('Select Student', coerce=int, validators=[DataRequired()])
    room_id = SelectField('Select Room', coerce=int, validators=[DataRequired()])
    bed_id = SelectField('Select Available Bed', coerce=int, validators=[DataRequired()])
    check_in_date = DateField('Check-in Date', validators=[DataRequired()])
    expected_check_out_date = DateField('Expected Check-out Date', validators=[Optional()])
    remarks = TextAreaField('Allocation Remarks / Notes')
    submit = SubmitField('Allocate Bed')


class TransferForm(FlaskForm):
    new_room_id = SelectField('Target Room', coerce=int, validators=[DataRequired()])
    new_bed_id = SelectField('Target Bed', coerce=int, validators=[DataRequired()])
    reason = TextAreaField('Reason for Room Transfer', validators=[DataRequired(), Length(min=5)])
    submit = SubmitField('Process Room Transfer')


class CheckoutForm(FlaskForm):
    check_out_date = DateField('Actual Check-out Date', validators=[DataRequired()])
    remarks = TextAreaField('Checkout Clearance Notes', validators=[Optional()])
    submit = SubmitField('Confirm Checkout & Release Bed')


# Finance Forms
class InvoiceForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    title = StringField('Invoice Title / Description', validators=[DataRequired(), Length(max=150)])
    issue_date = DateField('Issue Date', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    fee_type_id = SelectField('Fee Type', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Amount (PKR)', validators=[DataRequired(), NumberRange(min=1)])
    notes = TextAreaField('Invoice Notes / Payment Instructions')
    submit = SubmitField('Generate Invoice')


class PaymentForm(FlaskForm):
    invoice_id = SelectField('Select Invoice', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Payment Amount (PKR)', validators=[DataRequired(), NumberRange(min=1)])
    payment_method = SelectField('Payment Method', choices=[
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer (1Link/Raast)'),
        ('Online Payment', 'Online Card / Portal Payment')
    ], validators=[DataRequired()])
    payment_date = DateField('Payment Date', validators=[DataRequired()])
    transaction_id = StringField('Transaction Ref / Slip Number (Optional)', validators=[Optional(), Length(max=100)])
    remarks = TextAreaField('Remarks / Deposit Slip Note')
    submit = SubmitField('Record Payment & Generate Receipt')


# Attendance Forms
class AttendanceMarkForm(FlaskForm):
    date = DateField('Attendance Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Leave', 'On Leave / Permitted')
    ], validators=[DataRequired()])
    remarks = StringField('Remarks (Optional)')
    submit = SubmitField('Save Attendance')


class LateEntryForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    actual_time = StringField('Arrival Time (e.g. 11:30 PM)', validators=[DataRequired()])
    reason = TextAreaField('Reason for Late Arrival', validators=[DataRequired()])
    recorded_by = StringField('Duty Guard / Warden Name', validators=[DataRequired()])
    submit = SubmitField('Log Late Entry')


# Complaint Forms
class ComplaintForm(FlaskForm):
    category = SelectField('Complaint Category', choices=[
        ('Electricity', 'Electricity & Wiring'),
        ('Water', 'Water Supply & Plumbing'),
        ('Internet', 'WiFi & Internet Connection'),
        ('Room Maintenance', 'Room Furniture & Carpentry'),
        ('Cleaning', 'Cleanliness & Janitorial'),
        ('Food / Mess', 'Mess & Food Quality'),
        ('Security', 'Security & Safety Concern'),
        ('Other Issues', 'Other Issues')
    ], validators=[DataRequired()])
    title = StringField('Subject / Issue Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Detailed Description of the Issue', validators=[DataRequired()])
    priority = SelectField('Priority Level', choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent')
    ], default='Medium', validators=[DataRequired()])
    image = FileField('Attach Photo (Optional)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Only image files permitted.')
    ])
    submit = SubmitField('Submit Complaint Ticket')


class ComplaintAdminUpdateForm(FlaskForm):
    status = SelectField('Update Status', choices=[
        ('Pending', 'Pending Review'),
        ('In Progress', 'In Progress / Assigned'),
        ('Resolved', 'Resolved & Closed'),
        ('Rejected', 'Rejected / Invalid')
    ], validators=[DataRequired()])
    assigned_to_employee_id = SelectField('Assign to Staff Member', coerce=int, validators=[Optional()])
    admin_response = TextAreaField('Administrative Resolution / Response Note', validators=[DataRequired()])
    submit = SubmitField('Update Ticket Status')


class ComplaintFeedbackForm(FlaskForm):
    student_feedback = TextAreaField('Your Feedback on the Resolution', validators=[DataRequired()])
    student_rating = SelectField('Satisfaction Rating', choices=[
        (5, '★★★★★ (5/5) Excellent'),
        (4, '★★★★☆ (4/5) Good'),
        (3, '★★★☆☆ (3/5) Average'),
        (2, '★★☆☆☆ (2/5) Poor'),
        (1, '★☆☆☆☆ (1/5) Very Poor')
    ], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit Feedback')


# Visitor Forms
class VisitorForm(FlaskForm):
    visitor_name = StringField('Visitor Full Name', validators=[DataRequired(), Length(max=120)])
    cnic = StringField('Visitor CNIC Number', validators=[DataRequired(), Length(max=25)])
    phone_number = StringField('Contact Phone Number', validators=[DataRequired(), Length(max=25)])
    student_id = SelectField('Resident Student Being Visited', coerce=int, validators=[DataRequired()])
    relation = SelectField('Relationship to Student', choices=[
        ('Father', 'Father'),
        ('Mother', 'Mother'),
        ('Brother', 'Brother'),
        ('Sister', 'Sister'),
        ('Uncle', 'Uncle / Relative'),
        ('Guardian', 'Official Guardian'),
        ('Friend / Colleague', 'Friend / Colleague')
    ], validators=[DataRequired()])
    purpose = StringField('Purpose of Visit', validators=[DataRequired(), Length(max=255)])
    security_officer = StringField('Gate Officer on Duty', default='Main Security Gate', validators=[DataRequired()])
    remarks = TextAreaField('Security / Belongings Remarks')
    submit = SubmitField('Register Visitor Check-In')


# Mess Forms
class MessMenuForm(FlaskForm):
    hostel_id = SelectField('Hostel (Optional for specific hostel)', coerce=int, validators=[Optional()])
    day_of_week = SelectField('Day of the Week', choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday')
    ], validators=[DataRequired()])
    meal_type = SelectField('Meal Type', choices=[
        ('Breakfast', 'Breakfast'),
        ('Lunch', 'Lunch'),
        ('Dinner', 'Dinner')
    ], validators=[DataRequired()])
    menu_items = TextAreaField('Menu Items & Dish Details', validators=[DataRequired()])
    timing = StringField('Serving Timing (e.g. 7:30 AM - 9:30 AM)', validators=[Optional()])
    special_note = StringField('Special Dietary / Chef Note', validators=[Optional()])
    submit = SubmitField('Save Meal Menu')


class MessSubscriptionForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    plan_name = StringField('Mess Plan', default='Standard 3-Meals Full Board', validators=[DataRequired()])
    monthly_fee = DecimalField('Monthly Fee (PKR)', default=12000.00, validators=[DataRequired()])
    dietary_preference = StringField('Dietary Preference', default='Standard Pakistani Halal')
    status = SelectField('Subscription Status', choices=[
        ('Active', 'Active'),
        ('Paused', 'Paused'),
        ('Cancelled', 'Cancelled')
    ], default='Active')
    submit = SubmitField('Save Mess Subscription')


# Staff Forms
class EmployeeForm(FlaskForm):
    employee_code = StringField('Employee Code (e.g. EMP-101)', validators=[DataRequired(), Length(max=30)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    designation = SelectField('Designation / Role', choices=[
        ('Warden', 'Hostel Warden'),
        ('Accountant', 'Accounts & Finance Officer'),
        ('Security Guard', 'Security Guard'),
        ('Cleaner', 'Sanitation & Cleaner'),
        ('Electrician', 'Electrician / Technician'),
        ('Maintenance Staff', 'Maintenance & Plumber'),
        ('Mess Staff', 'Mess Cook / Head Chef')
    ], validators=[DataRequired()])
    cnic = StringField('CNIC Number', validators=[DataRequired(), Length(max=25)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=25)])
    email = EmailField('Email Address (Optional)', validators=[Optional(), Email()])
    address = TextAreaField('Residential Address', validators=[DataRequired(), Length(max=255)])
    joining_date = DateField('Joining Date', validators=[DataRequired()])
    salary = DecimalField('Monthly Base Salary (PKR)', validators=[DataRequired(), NumberRange(min=1000)])
    duty_shift = SelectField('Shift', choices=[
        ('Morning (7:00 AM - 3:00 PM)', 'Morning (7:00 AM - 3:00 PM)'),
        ('Evening (3:00 PM - 11:00 PM)', 'Evening (3:00 PM - 11:00 PM)'),
        ('Night (11:00 PM - 7:00 AM)', 'Night (11:00 PM - 7:00 AM)'),
        ('General (9:00 AM - 5:00 PM)', 'General (9:00 AM - 5:00 PM)')
    ], default='General (9:00 AM - 5:00 PM)')
    status = SelectField('Employment Status', choices=[
        ('Active', 'Active'),
        ('On Leave', 'On Leave'),
        ('Resigned', 'Resigned'),
        ('Terminated', 'Terminated')
    ], default='Active')
    create_user_account = BooleanField('Create Portal Login Account for this Staff Member', default=False)
    user_password = StringField('Initial Password (if account enabled)', default='Staff@12345')
    submit = SubmitField('Save Employee')


class TaskForm(FlaskForm):
    employee_id = SelectField('Assign to Staff Member', coerce=int, validators=[DataRequired()])
    title = StringField('Task Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Detailed Task Description & Instructions', validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent')
    ], default='Medium')
    due_date = DateField('Due Date', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed')
    ], default='Pending')
    submit = SubmitField('Assign Task')


class TaskUpdateForm(FlaskForm):
    status = SelectField('Update Status', choices=[
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed')
    ], validators=[DataRequired()])
    completion_notes = TextAreaField('Notes / Progress Report', validators=[Optional()])
    submit = SubmitField('Update Task')


# Communication Forms
class AnnouncementForm(FlaskForm):
    title = StringField('Announcement Headline', validators=[DataRequired(), Length(max=180)])
    content = TextAreaField('Notice Body / Announcement Details', validators=[DataRequired()])
    target_audience = SelectField('Target Audience', choices=[
        ('All', 'Everyone (All Residents & Staff)'),
        ('Students', 'Students Only'),
        ('Staff', 'Staff & Employees Only'),
        ('Wardens', 'Wardens & Admins Only')
    ], default='All', validators=[DataRequired()])
    priority = SelectField('Priority Level', choices=[
        ('Normal', 'Normal Notice'),
        ('Important', 'Important Notice'),
        ('Urgent', 'Urgent / Action Required')
    ], default='Normal', validators=[DataRequired()])
    expires_at = DateField('Valid Until (Optional)', validators=[Optional()])
    is_active = BooleanField('Active & Published', default=True)
    submit = SubmitField('Publish Announcement')
