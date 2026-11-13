from datetime import datetime, date
from app.models.base import db, TimestampMixin

class Hostel(TimestampMixin, db.Model):
    __tablename__ = 'hostels'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    hostel_type = db.Column(db.String(20), nullable=False, default='Boys')  # Boys, Girls, Co-ed
    address = db.Column(db.String(255), nullable=False)
    contact_number = db.Column(db.String(30), nullable=False)
    warden_name = db.Column(db.String(120))
    total_floors = db.Column(db.Integer, default=3, nullable=False)
    capacity = db.Column(db.Integer, default=100, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='Active', nullable=False)  # Active, Maintenance, Inactive

    rooms = db.relationship('Room', back_populates='hostel', cascade='all, delete-orphan', lazy='dynamic')
    mess_menus = db.relationship('MessMenu', back_populates='hostel', cascade='all, delete-orphan', lazy='dynamic')

    @property
    def total_rooms_count(self):
        return self.rooms.count()

    @property
    def total_beds_count(self):
        return sum(room.total_beds for room in self.rooms.all())

    @property
    def occupied_beds_count(self):
        return sum(room.occupied_beds_count for room in self.rooms.all())

    @property
    def available_beds_count(self):
        return max(0, self.total_beds_count - self.occupied_beds_count)

    @property
    def occupancy_rate(self):
        total = self.total_beds_count
        if total == 0:
            return 0
        return round((self.occupied_beds_count / total) * 100, 1)

    def __repr__(self):
        return f'<Hostel {self.name} ({self.hostel_type})>'


class Room(TimestampMixin, db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    hostel_id = db.Column(db.Integer, db.ForeignKey('hostels.id'), nullable=False)
    floor_number = db.Column(db.Integer, nullable=False, default=1)
    room_number = db.Column(db.String(20), nullable=False)
    room_type = db.Column(db.String(30), nullable=False, default='Double')  # Single, Double, Triple, Four-Seater
    total_beds = db.Column(db.Integer, nullable=False, default=2)
    monthly_rent = db.Column(db.Numeric(10, 2), nullable=False, default=15000.00)
    status = db.Column(db.String(20), nullable=False, default='Available')  # Available, Occupied, Maintenance
    facilities = db.Column(db.String(255), default='WiFi, Attached Bath, Cupboard, Study Table')

    hostel = db.relationship('Hostel', back_populates='rooms')
    beds = db.relationship('Bed', back_populates='room', cascade='all, delete-orphan', lazy='dynamic')
    allocations = db.relationship('RoomAllocation', back_populates='room', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('hostel_id', 'room_number', name='uix_hostel_room_number'),
    )

    @property
    def occupied_beds_count(self):
        return self.beds.filter_by(status='Occupied').count()

    @property
    def available_beds_count(self):
        return self.beds.filter_by(status='Available').count()

    @property
    def is_full(self):
        return self.available_beds_count == 0

    def sync_status(self):
        """Update room status based on beds occupancy."""
        if self.status == 'Maintenance':
            return
        if self.is_full and self.total_beds > 0:
            self.status = 'Occupied'
        else:
            self.status = 'Available'

    def __repr__(self):
        return f'<Room {self.room_number} - {self.hostel.name if self.hostel else ""}>'


class Bed(TimestampMixin, db.Model):
    __tablename__ = 'beds'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    bed_number = db.Column(db.String(20), nullable=False)  # e.g., 'Bed A', 'Bed 1'
    status = db.Column(db.String(20), nullable=False, default='Available')  # Available, Occupied, Maintenance

    room = db.relationship('Room', back_populates='beds')
    allocations = db.relationship('RoomAllocation', back_populates='bed', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('room_id', 'bed_number', name='uix_room_bed_number'),
    )

    @property
    def current_allocation(self):
        return self.allocations.filter_by(status='Active').first()

    def __repr__(self):
        return f'<Bed {self.bed_number} in Room {self.room.room_number if self.room else ""}>'


class RoomAllocation(TimestampMixin, db.Model):
    __tablename__ = 'room_allocations'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'), nullable=False)
    allocation_date = db.Column(db.Date, nullable=False, default=date.today)
    check_in_date = db.Column(db.Date, nullable=False, default=date.today)
    expected_check_out_date = db.Column(db.Date)
    actual_check_out_date = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False, default='Active')  # Active, Transferred, Checked Out
    remarks = db.Column(db.Text)

    student = db.relationship('Student', back_populates='room_allocations')
    room = db.relationship('Room', back_populates='allocations')
    bed = db.relationship('Bed', back_populates='allocations')

    def __repr__(self):
        return f'<Allocation Student:{self.student_id} Bed:{self.bed_id} Status:{self.status}>'


class RoomTransferHistory(TimestampMixin, db.Model):
    __tablename__ = 'room_transfer_history'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    from_room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    from_bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'), nullable=False)
    to_room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    to_bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'), nullable=False)
    transfer_date = db.Column(db.Date, nullable=False, default=date.today)
    reason = db.Column(db.Text)
    approved_by = db.Column(db.String(100))

    student = db.relationship('Student', foreign_keys=[student_id])
    from_room = db.relationship('Room', foreign_keys=[from_room_id])
    from_bed = db.relationship('Bed', foreign_keys=[from_bed_id])
    to_room = db.relationship('Room', foreign_keys=[to_room_id])
    to_bed = db.relationship('Bed', foreign_keys=[to_bed_id])

    def __repr__(self):
        return f'<Transfer Student:{self.student_id} Date:{self.transfer_date}>'
