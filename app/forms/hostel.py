from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length, Optional

class HostelForm(FlaskForm):
    name = StringField('Hostel Name', validators=[DataRequired(), Length(max=150)])
    hostel_type = SelectField('Hostel Type', choices=[
        ('Boys', "Boys' Hostel"),
        ('Girls', "Girls' Hostel"),
        ('Co-ed', 'Co-educational / Faculty Hostel')
    ], validators=[DataRequired()])
    address = TextAreaField('Physical Address', validators=[DataRequired(), Length(max=255)])
    contact_number = StringField('Contact / Office Phone', validators=[DataRequired(), Length(max=30)])
    warden_name = StringField('Warden in-Charge', validators=[Optional(), Length(max=120)])
    total_floors = IntegerField('Total Floors', validators=[DataRequired(), NumberRange(min=1, max=30)])
    capacity = IntegerField('Total Hostel Capacity (Beds)', validators=[DataRequired(), NumberRange(min=1, max=5000)])
    description = TextAreaField('Description & Facilities Overview')
    status = SelectField('Operational Status', choices=[
        ('Active', 'Active'),
        ('Maintenance', 'Under Renovation / Maintenance'),
        ('Inactive', 'Inactive')
    ], default='Active', validators=[DataRequired()])
    submit = SubmitField('Save Hostel')


class RoomForm(FlaskForm):
    hostel_id = SelectField('Hostel', coerce=int, validators=[DataRequired()])
    floor_number = IntegerField('Floor Number', validators=[DataRequired(), NumberRange(min=0, max=30)])
    room_number = StringField('Room Number / Name (e.g. 101, A-202)', validators=[DataRequired(), Length(max=20)])
    room_type = SelectField('Room Type', choices=[
        ('Single', 'Single (1 Bed)'),
        ('Double', 'Double (2 Beds)'),
        ('Triple', 'Triple (3 Beds)'),
        ('Four-Seater', 'Four-Seater (4 Beds)')
    ], validators=[DataRequired()])
    total_beds = IntegerField('Bed Capacity', validators=[DataRequired(), NumberRange(min=1, max=10)])
    monthly_rent = DecimalField('Monthly Rent (PKR)', validators=[DataRequired(), NumberRange(min=0)])
    facilities = StringField('Facilities (e.g. WiFi, AC, Attached Bath, Study Table)', default='WiFi, Attached Bath, Study Table, Cupboard')
    status = SelectField('Room Status', choices=[
        ('Available', 'Available'),
        ('Maintenance', 'Maintenance')
    ], default='Available')
    submit = SubmitField('Save Room')


class BedForm(FlaskForm):
    bed_number = StringField('Bed Number / Identifier (e.g. Bed-1, Bed-A)', validators=[DataRequired(), Length(max=20)])
    status = SelectField('Status', choices=[
        ('Available', 'Available'),
        ('Occupied', 'Occupied'),
        ('Maintenance', 'Maintenance')
    ], default='Available', validators=[DataRequired()])
    submit = SubmitField('Save Bed')
