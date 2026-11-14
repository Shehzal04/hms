from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.student import Student
from app.models.attendance import StudentAttendance, LateEntry
from app.forms.operations import LateEntryForm
from app.services.auth_service import role_required, log_audit

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def index():
    selected_date_str = request.args.get('date', date.today().isoformat())
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = date.today()

    active_students = Student.query.filter_by(status='Active').order_by(Student.full_name.asc()).all()

    # Existing attendance map for this date
    records = StudentAttendance.query.filter_by(date=selected_date).all()
    record_map = {r.student_id: r for r in records}

    present_count = sum(1 for r in records if r.status == 'Present')
    absent_count = sum(1 for r in records if r.status == 'Absent')
    leave_count = sum(1 for r in records if r.status == 'Leave')
    unmarked_count = len(active_students) - len(records)

    return render_template(
        'attendance/mark.html',
        students=active_students,
        record_map=record_map,
        selected_date=selected_date,
        present_count=present_count,
        absent_count=absent_count,
        leave_count=leave_count,
        unmarked_count=max(0, unmarked_count)
    )


@attendance_bp.route('/save-daily', methods=['POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def save_daily_attendance():
    date_str = request.form.get('date')
    try:
        att_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        att_date = date.today()

    active_students = Student.query.filter_by(status='Active').all()
    updated_count = 0

    for s in active_students:
        status_val = request.form.get(f"status_{s.id}")
        remarks_val = request.form.get(f"remarks_{s.id}", "").strip()

        if status_val in ['Present', 'Absent', 'Leave']:
            record = StudentAttendance.query.filter_by(student_id=s.id, date=att_date).first()
            if record:
                record.status = status_val
                record.remarks = remarks_val
                record.marked_by = current_user.full_name
            else:
                record = StudentAttendance(
                    student_id=s.id,
                    date=att_date,
                    status=status_val,
                    remarks=remarks_val,
                    marked_by=current_user.full_name
                )
                db.session.add(record)
            updated_count += 1

    db.session.commit()
    log_audit('MARK_ATTENDANCE', 'StudentAttendance', None, f"Marked attendance for {updated_count} students on {att_date}")
    flash(f"Attendance for {att_date.strftime('%d-%b-%Y')} saved successfully ({updated_count} records processed).", 'success')
    return redirect(url_for('attendance.index', date=att_date.isoformat()))


@attendance_bp.route('/history')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def attendance_history():
    page = request.args.get('page', 1, type=int)
    student_id = request.args.get('student_id', type=int)
    from_date_str = request.args.get('from_date', '')
    to_date_str = request.args.get('to_date', '')

    query = StudentAttendance.query.join(Student)

    if student_id:
        query = query.filter(StudentAttendance.student_id == student_id)
    if from_date_str:
        try:
            from_d = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            query = query.filter(StudentAttendance.date >= from_d)
        except ValueError:
            pass
    if to_date_str:
        try:
            to_d = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            query = query.filter(StudentAttendance.date <= to_d)
        except ValueError:
            pass

    pagination = query.order_by(StudentAttendance.date.desc(), Student.full_name.asc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )

    students = Student.query.filter_by(status='Active').order_by(Student.full_name.asc()).all()
    return render_template(
        'attendance/history.html',
        pagination=pagination,
        records=pagination.items,
        students=students,
        selected_student=student_id,
        from_date=from_date_str,
        to_date=to_date_str
    )


@attendance_bp.route('/late-entries', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def late_entries():
    form = LateEntryForm()
    students = Student.query.filter_by(status='Active').order_by(Student.full_name.asc()).all()
    form.student_id.choices = [(s.id, f"{s.student_id_code} - {s.full_name}") for s in students]

    if form.validate_on_submit():
        late_entry = LateEntry(
            student_id=form.student_id.data,
            actual_time=form.actual_time.data.strip(),
            reason=form.reason.data.strip(),
            recorded_by=form.recorded_by.data.strip()
        )
        db.session.add(late_entry)
        db.session.commit()
        log_audit('LOG_LATE_ENTRY', 'LateEntry', late_entry.id, f"Recorded late entry for student id {late_entry.student_id}")
        flash('Late entry recorded successfully.', 'warning')
        return redirect(url_for('attendance.late_entries'))

    entries = LateEntry.query.order_by(LateEntry.created_at.desc()).limit(50).all()
    return render_template('attendance/late_entries.html', form=form, entries=entries)
