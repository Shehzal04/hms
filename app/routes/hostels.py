from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.models.base import db
from app.models.hostel import Hostel, Room
from app.forms.hostel import HostelForm
from app.services.auth_service import role_required, log_audit

hostels_bp = Blueprint('hostels', __name__, url_prefix='/hostels')

@hostels_bp.route('/')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Accountant')
def list_hostels():
    hostels = Hostel.query.all()
    return render_template('hostels/list.html', hostels=hostels)


@hostels_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin')
def add_hostel():
    form = HostelForm()
    if form.validate_on_submit():
        if Hostel.query.filter_by(name=form.name.data.strip()).first():
            flash('A hostel with this name already exists.', 'danger')
            return render_template('hostels/add_edit.html', form=form, title='Add New Hostel')

        hostel = Hostel(
            name=form.name.data.strip(),
            hostel_type=form.hostel_type.data,
            address=form.address.data.strip(),
            contact_number=form.contact_number.data.strip(),
            warden_name=form.warden_name.data.strip() if form.warden_name.data else None,
            total_floors=form.total_floors.data,
            capacity=form.capacity.data,
            description=form.description.data.strip() if form.description.data else None,
            status=form.status.data
        )
        db.session.add(hostel)
        db.session.commit()
        log_audit('CREATE_HOSTEL', 'Hostel', hostel.id, f"Created hostel: {hostel.name}")
        flash(f"Hostel '{hostel.name}' has been created successfully!", 'success')
        return redirect(url_for('hostels.view_hostel', hostel_id=hostel.id))

    return render_template('hostels/add_edit.html', form=form, title='Add New Hostel')


@hostels_bp.route('/<int:hostel_id>')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Accountant')
def view_hostel(hostel_id):
    hostel = Hostel.query.get_or_404(hostel_id)
    rooms = hostel.rooms.order_by(Room.floor_number.asc(), Room.room_number.asc()).all()

    # Group rooms by floor
    floors = {}
    for r in rooms:
        floors.setdefault(r.floor_number, []).append(r)

    return render_template('hostels/view.html', hostel=hostel, rooms=rooms, floors=floors)


@hostels_bp.route('/<int:hostel_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin')
def edit_hostel(hostel_id):
    hostel = Hostel.query.get_or_404(hostel_id)
    form = HostelForm(obj=hostel)
    if form.validate_on_submit():
        existing = Hostel.query.filter(Hostel.name == form.name.data.strip(), Hostel.id != hostel.id).first()
        if existing:
            flash('Another hostel with this name already exists.', 'danger')
            return render_template('hostels/add_edit.html', form=form, title='Edit Hostel', hostel=hostel)

        hostel.name = form.name.data.strip()
        hostel.hostel_type = form.hostel_type.data
        hostel.address = form.address.data.strip()
        hostel.contact_number = form.contact_number.data.strip()
        hostel.warden_name = form.warden_name.data.strip() if form.warden_name.data else None
        hostel.total_floors = form.total_floors.data
        hostel.capacity = form.capacity.data
        hostel.description = form.description.data.strip() if form.description.data else None
        hostel.status = form.status.data

        db.session.commit()
        log_audit('UPDATE_HOSTEL', 'Hostel', hostel.id, f"Updated hostel: {hostel.name}")
        flash('Hostel updated successfully!', 'success')
        return redirect(url_for('hostels.view_hostel', hostel_id=hostel.id))

    return render_template('hostels/add_edit.html', form=form, title='Edit Hostel', hostel=hostel)


@hostels_bp.route('/<int:hostel_id>/delete', methods=['POST'])
@login_required
@role_required('Super Admin')
def delete_hostel(hostel_id):
    hostel = Hostel.query.get_or_404(hostel_id)
    if hostel.rooms.count() > 0:
        flash('Cannot delete this hostel because it contains rooms and student records. Please remove rooms first.', 'danger')
        return redirect(url_for('hostels.view_hostel', hostel_id=hostel.id))

    name = hostel.name
    db.session.delete(hostel)
    db.session.commit()
    log_audit('DELETE_HOSTEL', 'Hostel', hostel_id, f"Deleted hostel: {name}")
    flash(f"Hostel '{name}' has been deleted.", 'info')
    return redirect(url_for('hostels.list_hostels'))
