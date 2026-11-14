from datetime import date
from app.models.base import db, TimestampMixin

class MessMenu(TimestampMixin, db.Model):
    __tablename__ = 'mess_menus'

    id = db.Column(db.Integer, primary_key=True)
    hostel_id = db.Column(db.Integer, db.ForeignKey('hostels.id'), nullable=True)
    day_of_week = db.Column(db.String(20), nullable=False)  # Monday, Tuesday, ... Sunday
    meal_type = db.Column(db.String(20), nullable=False)  # Breakfast, Lunch, Dinner
    menu_items = db.Column(db.Text, nullable=False)  # e.g., 'Halwa Puri, Chana, Tea'
    timing = db.Column(db.String(50))  # e.g., '7:00 AM - 9:30 AM'
    special_note = db.Column(db.String(255))

    hostel = db.relationship('Hostel', back_populates='mess_menus')

    __table_args__ = (
        db.UniqueConstraint('hostel_id', 'day_of_week', 'meal_type', name='uix_hostel_day_meal'),
    )

    def __repr__(self):
        return f'<MessMenu {self.day_of_week} {self.meal_type}>'


class MessSubscription(TimestampMixin, db.Model):
    __tablename__ = 'mess_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    plan_name = db.Column(db.String(100), default='Standard 3-Meals Full Board')
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    end_date = db.Column(db.Date)
    monthly_fee = db.Column(db.Numeric(10, 2), nullable=False, default=12000.00)
    dietary_preference = db.Column(db.String(100), default='Standard Pakistani')
    status = db.Column(db.String(20), default='Active')  # Active, Paused, Cancelled

    student = db.relationship('Student', back_populates='mess_subscriptions')

    def __repr__(self):
        return f'<MessSubscription Student:{self.student_id} ({self.status})>'
