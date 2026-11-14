from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.student import Student
from app.models.hostel import Hostel, Room, Bed, RoomAllocation, RoomTransferHistory
from app.forms.operations import AllocationForm, TransferForm, CheckoutForm
from app.services.allocation_service import allocate_bed_to_student, transfer_student_bed, checkout_student_allocation, AllocationError
from app.services.auth_service import role_required, log_audit, send_notification

allocations_bp = Blueprint('allocations', __name__, url_prefix='/allocations')

@allocations_bp.route('/')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Accountant')
def list_allocations():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'Active').strip()
    search = request.args.get('search', '').strip()

    query = RoomAllocation.query.join(Student).join(Room)

    if status_filter and status_filter != 'All':
        query = query.filter(RoomAllocation.status == status_filter)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Student.full_name.ilike(search_pattern)) |
            (Student.student_id_code.ilike(search_pattern)) |
            (Room.room_number.ilike(search_pattern))
        )

    pagination = query.order_by(RoomAllocation.allocation_date.desc(), RoomAllocation.id.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )

    return render_template(
        'allocations/list.html',
        pagination=pagination,
        allocations=pagination.items,
        status_filter=status_filter,
        search=search
    )


@allocations_bp.route('/allocate', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def allocate_room():
    # Only students without active allocation
    allocated_student_ids = db.session.query(RoomAllocation.student_id).filter_by(status='Active').scalar_subquery()
    unallocated_students = Student.query.filter(
        Student.status == 'Active',
        ~Student.id.in_(allocated_student_ids)
    ).order_by(Student.full_name.asc()).all()

    # Pre-select student if passed in query param
    preset_student_id = request.args.get('student_id', type=int)

    # Available rooms
    rooms_with_space = Room.query.filter(Room.status != 'Maintenance').all()
    rooms_available = [r for r in rooms_with_space if r.available_beds_count > 0]

    form = AllocationForm()
    form.student_id.choices = [(s.id, f"{s.student_id_code} - {s.full_name} ({s.gender})") for s in unallocated_students]
    form.room_id.choices = [(r.id, f"{r.hostel.name} - Room {r.room_number} ({r.room_type}, {r.available_beds_count} left)") for r in rooms_available]
    
    # Bed choices based on initial or submitted room
    selected_room_id = form.room_id.data or (rooms_available[0].id if rooms_available else None)
    if selected_room_id:
        beds = Bed.query.filter_by(room_id=selected_room_id, status='Available').all()
        form.bed_id.choices = [(b.id, b.bed_number) for b in beds]
    else:
        form.bed_id.choices = []

    if request.method == 'GET' and preset_student_id:
        form.student_id.data = preset_student_id
        form.check_in_date.data = date.today()

    if form.validate_on_submit():
        try:
            alloc = allocate_bed_to_student(
                student_id=form.student_id.data,
                room_id=form.room_id.data,
                bed_id=form.bed_id.data,
                check_in_date=form.check_in_date.data,
                expected_check_out_date=form.expected_check_out_date.data,
                remarks=form.remarks.data
            )
            log_audit('ALLOCATE_ROOM', 'RoomAllocation', alloc.id, f"Allocated Student {alloc.student.full_name} to Room {alloc.room.room_number}, Bed {alloc.bed.bed_number}")
            if alloc.student.user_id:
                send_notification(
                    user_id=alloc.student.user_id,
                    title="Room Allocated",
                    message=f"You have been allocated to {alloc.room.hostel.name}, Room {alloc.room.room_number}, {alloc.bed.bed_number}.",
                    link="/portal/my-room"
                )
            flash(f"Room {alloc.room.room_number} ({alloc.bed.bed_number}) allocated to {alloc.student.full_name} successfully!", 'success')
            return redirect(url_for('allocations.list_allocations'))
        except AllocationError as e:
            flash(str(e), 'danger')

    return render_template(
        'allocations/allocate.html',
        form=form,
        unallocated_count=len(unallocated_students),
        available_rooms_count=len(rooms_available)
    )


@allocations_bp.route('/<int:allocation_id>/transfer', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def transfer_allocation(allocation_id):
    alloc = RoomAllocation.query.get_or_404(allocation_id)
    if alloc.status != 'Active':
        flash('Only currently active room allocations can be transferred.', 'warning')
        return redirect(url_for('allocations.list_allocations'))

    # Available rooms with open beds
    rooms_with_space = [r for r in Room.query.filter(Room.status != 'Maintenance').all() if r.available_beds_count > 0]

    form = TransferForm()
    form.new_room_id.choices = [(r.id, f"{r.hostel.name} - Room {r.room_number} ({r.available_beds_count} beds free)") for r in rooms_with_space]

    target_room_id = form.new_room_id.data or (rooms_with_space[0].id if rooms_with_space else None)
    if target_room_id:
        beds = Bed.query.filter_by(room_id=target_room_id, status='Available').all()
        form.new_bed_id.choices = [(b.id, b.bed_number) for b in beds]
    else:
        form.new_bed_id.choices = []

    if form.validate_on_submit():
        try:
            new_alloc = transfer_student_bed(
                student_id=alloc.student_id,
                new_room_id=form.new_room_id.data,
                new_bed_id=form.new_bed_id.data,
                reason=form.reason.data.strip(),
                approved_by=current_user.full_name
            )
            log_audit('TRANSFER_ROOM', 'RoomAllocation', new_alloc.id, f"Transferred Student {new_alloc.student.full_name} to Room {new_alloc.room.room_number}")
            flash(f"Student transferred to Room {new_alloc.room.room_number} ({new_alloc.bed.bed_number}) successfully!", 'success')
            return redirect(url_for('allocations.list_allocations'))
        except AllocationError as e:
            flash(str(e), 'danger')

    return render_template('allocations/transfer.html', form=form, allocation=alloc)


@allocations_bp.route('/<int:allocation_id>/checkout', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def checkout_allocation(allocation_id):
    alloc = RoomAllocation.query.get_or_404(allocation_id)
    if alloc.status != 'Active':
        flash('This allocation is not currently active.', 'warning')
        return redirect(url_for('allocations.list_allocations'))

    form = CheckoutForm()
    if request.method == 'GET':
        form.check_out_date.data = date.today()

    if form.validate_on_submit():
        try:
            checkout_student_allocation(
                allocation_id=alloc.id,
                check_out_date=form.check_out_date.data,
                remarks=form.remarks.data
            )
            log_audit('CHECKOUT_ROOM', 'RoomAllocation', alloc.id, f"Checked out Student {alloc.student.full_name} from Room {alloc.room.room_number}")
            flash(f"Student {alloc.student.full_name} successfully checked out. Bed {alloc.bed.bed_number} is now Available.", 'info')
            return redirect(url_for('allocations.list_allocations'))
        except AllocationError as e:
            flash(str(e), 'danger')

    return render_template('allocations/checkout.html', form=form, allocation=alloc)


@allocations_bp.route('/history')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Accountant')
def transfer_history():
    transfers = RoomTransferHistory.query.order_by(RoomTransferHistory.transfer_date.desc()).all()
    return render_template('allocations/history.html', transfers=transfers)


# AJAX API: Dynamic Beds endpoint for dependent dropdowns
@allocations_bp.route('/api/beds-by-room/<int:room_id>')
@login_required
def get_available_beds_by_room(room_id):
    beds = Bed.query.filter_by(room_id=room_id, status='Available').all()
    data = [{'id': b.id, 'bed_number': b.bed_number} for b in beds]
    return jsonify(data)
