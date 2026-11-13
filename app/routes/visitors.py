from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.student import Student
from app.models.visitor import Visitor
from app.forms.operations import VisitorForm
from app.services.auth_service import role_required, log_audit, send_notification

visitors_bp = Blueprint('visitors', __name__, url_prefix='/visitors')

@visitors_bp.route('/')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Staff')
def list_visitors():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'inside').strip()

    query = Visitor.query.join(Student)

    if status_filter == 'inside':
        query = query.filter(Visitor.check_out == None)
    elif status_filter == 'departed':
        query = query.filter(Visitor.check_out != None)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Visitor.visitor_name.ilike(search_pattern)) |
            (Visitor.cnic.ilike(search_pattern)) |
            (Visitor.phone_number.ilike(search_pattern)) |
            (Student.full_name.ilike(search_pattern))
        )

    pagination = query.order_by(Visitor.check_in.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )

    inside_count = Visitor.query.filter(Visitor.check_out == None).count()
    return render_template(
        'visitors/list.html',
        pagination=pagination,
        visitors=pagination.items,
        search=search,
        status_filter=status_filter,
        inside_count=inside_count
    )


@visitors_bp.route('/register', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Staff')
def register_visitor():
    form = VisitorForm()
    students = Student.query.filter_by(status='Active').order_by(Student.full_name.asc()).all()
    form.student_id.choices = [(s.id, f"{s.student_id_code} - {s.full_name}") for s in students]

    if form.validate_on_submit():
        visitor = Visitor(
            visitor_name=form.visitor_name.data.strip(),
            cnic=form.cnic.data.strip(),
            phone_number=form.phone_number.data.strip(),
            student_id=form.student_id.data,
            relation=form.relation.data,
            purpose=form.purpose.data.strip(),
            check_in=datetime.utcnow(),
            security_officer=form.security_officer.data.strip(),
            remarks=form.remarks.data
        )
        db.session.add(visitor)
        db.session.commit()
        log_audit('REGISTER_VISITOR', 'Visitor', visitor.id, f"Registered visitor {visitor.visitor_name} for student id {visitor.student_id}")

        # Notify student
        if visitor.student.user_id:
            send_notification(
                user_id=visitor.student.user_id,
                title="Visitor Arrived at Gate",
                message=f"{visitor.visitor_name} ({visitor.relation}) has checked in to visit you at the main gate reception.",
                link="/portal/my-visitors"
            )

        flash(f"Visitor '{visitor.visitor_name}' registered successfully!", 'success')
        return redirect(url_for('visitors.list_visitors'))

    return render_template('visitors/register.html', form=form)


@visitors_bp.route('/<int:visitor_id>/checkout', methods=['POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Staff')
def checkout_visitor(visitor_id):
    visitor = Visitor.query.get_or_404(visitor_id)
    if not visitor.check_out:
        visitor.check_out = datetime.utcnow()
        db.session.commit()
        log_audit('CHECKOUT_VISITOR', 'Visitor', visitor.id, f"Visitor {visitor.visitor_name} departed")
        flash(f"Visitor {visitor.visitor_name} departure recorded.", 'info')
    return redirect(url_for('visitors.list_visitors'))
