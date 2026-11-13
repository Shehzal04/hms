import os
from datetime import datetime, date
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app.models.base import db
from app.models.student import Student
from app.models.hostel import RoomAllocation, RoomTransferHistory, Room, Bed
from app.models.finance import FeeInvoice, Payment
from app.models.complaint import Complaint
from app.models.mess import MessMenu
from app.models.communication import Announcement, Notification
from app.models.visitor import Visitor
from app.models.attendance import StudentAttendance, LateEntry
from app.forms.operations import ComplaintForm, ComplaintFeedbackForm
from app.services.auth_service import log_audit

student_portal_bp = Blueprint('student_portal', __name__, url_prefix='/portal')

def get_current_student():
    if not current_user.is_authenticated or not current_user.student_profile:
        return None
    return current_user.student_profile


@student_portal_bp.route('/')
@student_portal_bp.route('/dashboard')
@login_required
def dashboard():
    student = get_current_student()
    if not student:
        flash("No student profile linked to your account.", "warning")
        return redirect(url_for('dashboard.index'))

    allocation = student.current_allocation
    invoices = student.fee_invoices.order_by(FeeInvoice.due_date.desc()).limit(5).all()
    complaints = student.complaints.order_by(Complaint.created_at.desc()).limit(5).all()
    announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.priority.desc(), Announcement.created_at.desc()).limit(4).all()
    
    # Recent attendance (last 10 days)
    recent_attendance = student.attendance_records.order_by(StudentAttendance.date.desc()).limit(10).all()

    return render_template(
        'student_portal/index.html',
        student=student,
        allocation=allocation,
        invoices=invoices,
        complaints=complaints,
        announcements=announcements,
        recent_attendance=recent_attendance
    )


@student_portal_bp.route('/my-room')
@login_required
def my_room():
    student = get_current_student()
    if not student:
        return redirect(url_for('dashboard.index'))
    allocation = student.current_allocation
    all_allocations = student.room_allocations.order_by(RoomAllocation.allocation_date.desc()).all()
    room_mates = []
    if allocation and allocation.room:
        room_mates = [
            alloc.student for alloc in allocation.room.allocations.filter_by(status='Active').all()
            if alloc.student_id != student.id
        ]
    return render_template('student_portal/my_room.html', student=student, allocation=allocation, all_allocations=all_allocations, room_mates=room_mates)


@student_portal_bp.route('/my-fees')
@login_required
def my_fees():
    student = get_current_student()
    if not student:
        return redirect(url_for('dashboard.index'))
    invoices = student.fee_invoices.order_by(FeeInvoice.due_date.desc()).all()
    payments = student.payments.order_by(Payment.payment_date.desc()).all()
    return render_template('student_portal/my_fees.html', student=student, invoices=invoices, payments=payments)


@student_portal_bp.route('/my-attendance')
@login_required
def my_attendance():
    student = get_current_student()
    if not student:
        return redirect(url_for('dashboard.index'))
    records = student.attendance_records.order_by(StudentAttendance.date.desc()).all()
    total_days = len(records)
    present_days = sum(1 for r in records if r.status in ['Present', 'Leave'])
    att_rate = round((present_days / total_days * 100), 1) if total_days > 0 else 100.0
    return render_template('student_portal/my_attendance.html', student=student, records=records, att_rate=att_rate, total_days=total_days, present_days=present_days)


@student_portal_bp.route('/my-complaints', methods=['GET', 'POST'])
@login_required
def my_complaints():
    student = get_current_student()
    if not student:
        return redirect(url_for('dashboard.index'))

    form = ComplaintForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            file = form.image.data
            fname = secure_filename(file.filename)
            ext = fname.rsplit('.', 1)[1].lower() if '.' in fname else 'jpg'
            image_filename = f"cmp_{student.student_id_code}_{int(datetime.utcnow().timestamp())}.{ext}"
            dest_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'complaints')
            os.makedirs(dest_dir, exist_ok=True)
            file.save(os.path.join(dest_dir, image_filename))

        # Ticket format: CMP-YEAR-RANDOM
        ticket_number = f"CMP-{date.today().year}-{datetime.utcnow().strftime('%f')[:4]}"
        complaint = Complaint(
            ticket_number=ticket_number,
            student_id=student.id,
            category=form.category.data,
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            priority=form.priority.data,
            image_path=image_filename,
            status='Pending'
        )
        db.session.add(complaint)
        db.session.commit()
        log_audit('SUBMIT_COMPLAINT', 'Complaint', complaint.id, f"Student {student.full_name} submitted ticket {complaint.ticket_number}")
        flash(f"Complaint ticket #{complaint.ticket_number} submitted! The warden/staff will review it shortly.", 'success')
        return redirect(url_for('student_portal.my_complaints'))

    complaints = student.complaints.order_by(Complaint.created_at.desc()).all()
    feedback_form = ComplaintFeedbackForm()
    return render_template('student_portal/my_complaints.html', student=student, complaints=complaints, form=form, feedback_form=feedback_form)


@student_portal_bp.route('/my-visitors')
@login_required
def my_visitors():
    student = get_current_student()
    if not student:
        return redirect(url_for('dashboard.index'))
    visitors = student.visitors.order_by(Visitor.check_in.desc()).all()
    return render_template('student_portal/my_visitors.html', student=student, visitors=visitors)


@student_portal_bp.route('/mess-menu')
@login_required
def mess_menu():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    meals = ['Breakfast', 'Lunch', 'Dinner']
    all_menus = MessMenu.query.all()
    schedule = {day: {meal: None for meal in meals} for day in days}
    for m in all_menus:
        if m.day_of_week in schedule and m.meal_type in schedule[m.day_of_week]:
            schedule[m.day_of_week][m.meal_type] = m
    return render_template('student_portal/mess_menu.html', schedule=schedule, days=days, meals=meals)


@student_portal_bp.route('/notifications/mark-read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
    return ('', 204)
