import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.complaint import Complaint, ComplaintUpdate
from app.models.staff import Employee
from app.forms.operations import ComplaintAdminUpdateForm, ComplaintFeedbackForm
from app.services.auth_service import role_required, log_audit, send_notification

complaints_bp = Blueprint('complaints', __name__, url_prefix='/complaints')

@complaints_bp.route('/')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Staff')
def list_complaints():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '').strip()
    status_filter = request.args.get('status', '').strip()
    priority = request.args.get('priority', '').strip()

    query = Complaint.query

    # If employee staff member, show complaints assigned to them
    if current_user.is_staff and current_user.employee_profile:
        query = query.filter_by(assigned_to_employee_id=current_user.employee_profile.id)

    if category:
        query = query.filter_by(category=category)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority:
        query = query.filter_by(priority=priority)

    pagination = query.order_by(Complaint.created_at.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )

    # Category counts
    pending_count = Complaint.query.filter_by(status='Pending').count()
    in_progress_count = Complaint.query.filter_by(status='In Progress').count()
    resolved_count = Complaint.query.filter_by(status='Resolved').count()

    return render_template(
        'complaints/list.html',
        pagination=pagination,
        complaints=pagination.items,
        category=category,
        status_filter=status_filter,
        priority=priority,
        pending_count=pending_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count
    )


@complaints_bp.route('/<int:complaint_id>', methods=['GET', 'POST'])
@login_required
def view_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    
    # Permission check: Student can view their own, Staff can view assigned, Admins can view all
    if current_user.is_student:
        if complaint.student.user_id != current_user.id:
            flash('Unauthorized.', 'danger')
            return redirect(url_for('student_portal.dashboard'))

    form = ComplaintAdminUpdateForm(obj=complaint)
    employees = Employee.query.filter_by(status='Active').order_by(Employee.full_name.asc()).all()
    form.assigned_to_employee_id.choices = [(0, '-- Unassigned --')] + [(e.id, f"{e.full_name} ({e.designation})") for e in employees]

    feedback_form = ComplaintFeedbackForm()

    # Admin/Warden/Staff Update
    if form.validate_on_submit() and not current_user.is_student:
        prev_status = complaint.status
        new_status = form.status.data
        assigned_id = form.assigned_to_employee_id.data if form.assigned_to_employee_id.data != 0 else None

        complaint.status = new_status
        complaint.assigned_to_employee_id = assigned_id
        complaint.admin_response = form.admin_response.data.strip()
        if new_status == 'Resolved' and not complaint.resolved_at:
            complaint.resolved_at = datetime.utcnow()

        # Audit history note
        update_log = ComplaintUpdate(
            complaint_id=complaint.id,
            updated_by=current_user.full_name,
            action_note=form.admin_response.data.strip(),
            status_change=f"{prev_status} -> {new_status}"
        )
        db.session.add(update_log)
        db.session.commit()
        log_audit('UPDATE_COMPLAINT', 'Complaint', complaint.id, f"Updated ticket {complaint.ticket_number} to {new_status}")

        # Notify student
        if complaint.student.user_id:
            send_notification(
                user_id=complaint.student.user_id,
                title=f"Complaint #{complaint.ticket_number} Update",
                message=f"Status changed to {new_status}: {complaint.admin_response[:80]}...",
                link=f"/portal/my-complaints"
            )

        flash('Complaint ticket updated successfully!', 'success')
        return redirect(url_for('complaints.view_complaint', complaint_id=complaint.id))

    return render_template(
        'complaints/view.html',
        complaint=complaint,
        form=form,
        feedback_form=feedback_form
    )


@complaints_bp.route('/<int:complaint_id>/feedback', methods=['POST'])
@login_required
def submit_feedback(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    if not current_user.is_student or complaint.student.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('student_portal.dashboard'))

    form = ComplaintFeedbackForm()
    if form.validate_on_submit():
        complaint.student_feedback = form.student_feedback.data.strip()
        complaint.student_rating = form.student_rating.data
        db.session.commit()
        flash('Thank you for providing your feedback!', 'success')
    return redirect(url_for('complaints.view_complaint', complaint_id=complaint.id))
