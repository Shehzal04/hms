from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required
from app.models.base import db
from app.models.hostel import Hostel, Room, Bed
from app.forms.hostel import RoomForm, BedForm
from app.services.auth_service import role_required, log_audit

rooms_bp = Blueprint('rooms', __name__, url_prefix='/rooms')

@rooms_bp.route('/')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Accountant')
def list_rooms():
    page = request.args.get('page', 1, type=int)
    hostel_id = request.args.get('hostel_id', type=int)
    room_type = request.args.get('room_type', '').strip()
    status_filter = request.args.get('status', '').strip()
    floor = request.args.get('floor', type=int)
    search = request.args.get('search', '').strip()

    query = Room.query

    if hostel_id:
        query = query.filter_by(hostel_id=hostel_id)
    if room_type:
        query = query.filter_by(room_type=room_type)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if floor is not None:
        query = query.filter_by(floor_number=floor)
    if search:
        query = query.filter(Room.room_number.ilike(f"%{search}%"))

    pagination = query.order_by(Room.hostel_id.asc(), Room.floor_number.asc(), Room.room_number.asc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )

    hostels = Hostel.query.all()
    return render_template(
        'rooms/list.html',
        pagination=pagination,
        rooms=pagination.items,
        hostels=hostels,
        selected_hostel=hostel_id,
        selected_type=room_type,
        selected_status=status_filter,
        selected_floor=floor,
        search=search
    )


@rooms_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin')
def add_room():
    form = RoomForm()
    form.hostel_id.choices = [(h.id, h.name) for h in Hostel.query.filter_by(status='Active').all()]

    if form.validate_on_submit():
        # Check duplicate room number in this hostel
        existing = Room.query.filter_by(hostel_id=form.hostel_id.data, room_number=form.room_number.data.strip()).first()
        if existing:
            flash(f"Room '{form.room_number.data}' already exists in the selected hostel.", 'danger')
            return render_template('rooms/add_edit.html', form=form, title='Add New Room')

        room = Room(
            hostel_id=form.hostel_id.data,
            floor_number=form.floor_number.data,
            room_number=form.room_number.data.strip(),
            room_type=form.room_type.data,
            total_beds=form.total_beds.data,
            monthly_rent=form.monthly_rent.data,
            facilities=form.facilities.data.strip() if form.facilities.data else '',
            status=form.status.data
        )
        db.session.add(room)
        db.session.flush()

        # Automatically generate Bed instances for this room
        # e.g., Bed-1, Bed-2, ...
        for b in range(1, room.total_beds + 1):
            bed = Bed(
                room_id=room.id,
                bed_number=f"Bed-{b}",
                status='Available'
            )
            db.session.add(bed)

        db.session.commit()
        log_audit('CREATE_ROOM', 'Room', room.id, f"Created room {room.room_number} with {room.total_beds} beds")
        flash(f"Room {room.room_number} created with {room.total_beds} beds initialized!", 'success')
        return redirect(url_for('rooms.view_room', room_id=room.id))

    return render_template('rooms/add_edit.html', form=form, title='Add New Room')


@rooms_bp.route('/<int:room_id>')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Accountant')
def view_room(room_id):
    room = Room.query.get_or_404(room_id)
    beds = room.beds.order_by(Bed.bed_number.asc()).all()
    bed_form = BedForm()
    return render_template('rooms/view.html', room=room, beds=beds, bed_form=bed_form)


@rooms_bp.route('/<int:room_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin')
def edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    form = RoomForm(obj=room)
    form.hostel_id.choices = [(h.id, h.name) for h in Hostel.query.all()]

    if form.validate_on_submit():
        existing = Room.query.filter(
            Room.hostel_id == form.hostel_id.data,
            Room.room_number == form.room_number.data.strip(),
            Room.id != room.id
        ).first()
        if existing:
            flash('Another room in this hostel already has this room number.', 'danger')
            return render_template('rooms/add_edit.html', form=form, title='Edit Room', room=room)

        room.hostel_id = form.hostel_id.data
        room.floor_number = form.floor_number.data
        room.room_number = form.room_number.data.strip()
        room.room_type = form.room_type.data
        room.monthly_rent = form.monthly_rent.data
        room.facilities = form.facilities.data.strip() if form.facilities.data else ''
        room.status = form.status.data

        # If bed count increased, add extra beds
        current_bed_count = room.beds.count()
        if form.total_beds.data > current_bed_count:
            for b in range(current_bed_count + 1, form.total_beds.data + 1):
                bed = Bed(room_id=room.id, bed_number=f"Bed-{b}", status='Available')
                db.session.add(bed)
            room.total_beds = form.total_beds.data

        room.sync_status()
        db.session.commit()
        log_audit('UPDATE_ROOM', 'Room', room.id, f"Updated room {room.room_number}")
        flash('Room details updated successfully!', 'success')
        return redirect(url_for('rooms.view_room', room_id=room.id))

    return render_template('rooms/add_edit.html', form=form, title='Edit Room', room=room)


@rooms_bp.route('/<int:room_id>/delete', methods=['POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin')
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    if room.occupied_beds_count > 0:
        flash('Cannot delete room because it currently has resident students allocated. Please check out or transfer students first.', 'danger')
        return redirect(url_for('rooms.view_room', room_id=room.id))

    room_num = room.room_number
    db.session.delete(room)
    db.session.commit()
    log_audit('DELETE_ROOM', 'Room', room_id, f"Deleted room {room_num}")
    flash(f"Room {room_num} deleted successfully.", 'info')
    return redirect(url_for('rooms.list_rooms'))


@rooms_bp.route('/<int:room_id>/add-bed', methods=['POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin')
def add_bed(room_id):
    room = Room.query.get_or_404(room_id)
    form = BedForm()
    if form.validate_on_submit():
        existing = Bed.query.filter_by(room_id=room.id, bed_number=form.bed_number.data.strip()).first()
        if existing:
            flash(f"Bed '{form.bed_number.data}' already exists in this room.", 'danger')
            return redirect(url_for('rooms.view_room', room_id=room.id))

        bed = Bed(
            room_id=room.id,
            bed_number=form.bed_number.data.strip(),
            status=form.status.data
        )
        db.session.add(bed)
        room.total_beds = room.beds.count() + 1
        room.sync_status()
        db.session.commit()
        flash(f"Bed {bed.bed_number} added.", 'success')
    return redirect(url_for('rooms.view_room', room_id=room.id))


@rooms_bp.route('/beds/<int:bed_id>/toggle-maintenance', methods=['POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def toggle_bed_maintenance(bed_id):
    bed = Bed.query.get_or_404(bed_id)
    if bed.status == 'Occupied':
        flash('Cannot set an occupied bed to maintenance. Student must be transferred first.', 'warning')
    elif bed.status == 'Maintenance':
        bed.status = 'Available'
        flash(f"{bed.bed_number} marked as Available.", 'success')
    else:
        bed.status = 'Maintenance'
        flash(f"{bed.bed_number} marked as Maintenance.", 'info')

    bed.room.sync_status()
    db.session.commit()
    return redirect(url_for('rooms.view_room', room_id=bed.room_id))
