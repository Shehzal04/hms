from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, EmailField, DateField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional

class StudentForm(FlaskForm):
    student_id_code = StringField('Student ID Code', validators=[DataRequired(), Length(max=30)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    father_name = StringField('Father Name', validators=[DataRequired(), Length(max=120)])
    cnic = StringField('CNIC / B-Form Number', validators=[DataRequired(), Length(min=13, max=25)])
    email = EmailField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=25)])
    emergency_contact = StringField('Emergency Contact Number', validators=[DataRequired(), Length(max=25)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    address = TextAreaField('Permanent Home Address', validators=[DataRequired(), Length(max=255)])
    city = StringField('City / Domicile', validators=[DataRequired(), Length(max=60)])
    university_name = StringField('University / College Name', validators=[DataRequired(), Length(max=150)])
    department = StringField('Department / Faculty', validators=[DataRequired(), Length(max=100)])
    degree_program = StringField('Degree Program (e.g. BSCS, BSEE, MBBS)', validators=[DataRequired(), Length(max=100)])
    semester = SelectField('Current Semester / Year', choices=[
        ('1st Semester', '1st Semester'),
        ('2nd Semester', '2nd Semester'),
        ('3rd Semester', '3rd Semester'),
        ('4th Semester', '4th Semester'),
        ('5th Semester', '5th Semester'),
        ('6th Semester', '6th Semester'),
        ('7th Semester', '7th Semester'),
        ('8th Semester', '8th Semester'),
        ('Postgraduate', 'Postgraduate')
    ], validators=[DataRequired()])
    admission_date = DateField('Hostel Admission Date', validators=[DataRequired()])
    status = SelectField('Admission Status', choices=[
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
        ('Alumni', 'Alumni')
    ], default='Active', validators=[DataRequired()])
    profile_picture = FileField('Profile Photo', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Only image files (JPG, PNG, WEBP) are allowed.')
    ])

    # Guardian details in the same comprehensive enrollment form
    guardian_name = StringField('Guardian Name', validators=[DataRequired(), Length(max=120)])
    guardian_relation = SelectField('Relationship', choices=[
        ('Father', 'Father'),
        ('Mother', 'Mother'),
        ('Brother', 'Brother'),
        ('Uncle', 'Uncle'),
        ('Guardian', 'Other Legal Guardian')
    ], default='Father', validators=[DataRequired()])
    guardian_phone = StringField('Guardian Phone Number', validators=[DataRequired(), Length(max=25)])
    guardian_cnic = StringField('Guardian CNIC', validators=[Optional(), Length(max=25)])
    guardian_occupation = StringField('Guardian Occupation', validators=[Optional(), Length(max=100)])
    guardian_address = TextAreaField('Guardian Address', validators=[Optional(), Length(max=255)])

    submit = SubmitField('Save Student Profile')


class DocumentUploadForm(FlaskForm):
    doc_title = StringField('Document Title', validators=[DataRequired(), Length(max=120)])
    doc_type = SelectField('Document Type', choices=[
        ('CNIC / B-Form Copy', 'CNIC / B-Form Copy'),
        ('University ID Card', 'University ID Card'),
        ('Admission Letter', 'Admission Letter'),
        ('Domicile Certificate', 'Domicile Certificate'),
        ('Affidavit / Undertaking', 'Affidavit / Undertaking'),
        ('Medical Fitness Certificate', 'Medical Fitness Certificate'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    doc_file = FileField('Upload File', validators=[
        DataRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'], 'Allowed formats: PDF, JPG, PNG, DOCX')
    ])
    submit = SubmitField('Upload Document')
