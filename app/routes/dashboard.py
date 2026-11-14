from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, jsonify, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models.base import db
from app.models.student import Student
from app.models.hostel import Hostel, Room, Bed, RoomAllocation
from app.models.finance import FeeInvoice, Payment
from app.models.attendance import StudentAttendance
from app.models.complaint import Complaint
from app.models.staff import Employee, Task
from app.models.communication import Announcement
from app.models.visitor import Visitor

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    if current_user.is_student:
        return redirect(url_for('student_portal.dashboard'))
    elif current_user.is_staff:
        return redirect(url_for('staff.my_duties'))
    return redirect(url_for('dashboard.index'))


@dashboard_bp.route('/dashboard')
@login_required
def index():
    if current_user.is_student:
        return redirect(url_for('student_portal.dashboard'))
    elif current_user.is_staff:
        return redirect(url_for('staff.my_duties'))

    today = date.today()
    first_of_month = today.replace(day=1)

    # 1. Total Students
    total_students = Student.query.filter_by(status='Active').count()

    # 2. Rooms & Bed metrics
    total_rooms = Room.query.count()
    total_beds = Bed.query.count()
    occupied_beds = Bed.query.filter_by(status='Occupied').count()
    available_beds = Bed.query.filter_by(status='Available').count()
    maintenance_beds = Bed.query.filter_by(status='Maintenance').count()
    
    total_capacity = total_beds
    occupancy_percentage = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0

    # 3. Financial metrics
    # Monthly fee collection (current month)
    monthly_collection = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.payment_date >= first_of_month
    ).scalar()

    # Total pending payments across all invoices
    total_invoiced = db.session.query(func.coalesce(func.sum(FeeInvoice.total_amount), 0)).scalar()
    total_paid = db.session.query(func.coalesce(func.sum(FeeInvoice.paid_amount), 0)).scalar()
    pending_payments = max(0, float(total_invoiced) - float(total_paid))

    # 4. Total Employees
    total_employees = Employee.query.filter_by(status='Active').count()

    # 5. Today's Student Attendance
    today_present = StudentAttendance.query.filter_by(date=today, status='Present').count()
    today_absent = StudentAttendance.query.filter_by(date=today, status='Absent').count()
    today_leave = StudentAttendance.query.filter_by(date=today, status='Leave').count()
    today_attendance_total = today_present + today_absent + today_leave
    today_attendance_rate = round((today_present / today_attendance_total * 100), 1) if today_attendance_total > 0 else 0

    # 6. Pending Complaints
    pending_complaints = Complaint.query.filter(Complaint.status.in_(['Pending', 'In Progress'])).count()

    # 7. Active Visitors inside premises
    active_visitors = Visitor.query.filter(Visitor.check_out == None).count()

    # 8. Recent Admissions (last 5)
    recent_admissions = Student.query.order_by(Student.admission_date.desc(), Student.id.desc()).limit(6).all()

    # 9. Recent Payments (last 5)
    recent_payments = Payment.query.order_by(Payment.payment_date.desc(), Payment.id.desc()).limit(6).all()

    # 10. Recent Active Announcements
    recent_announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).limit(4).all()

    # 11. Hostels quick summary
    hostels_summary = Hostel.query.all()

    return render_template(
        'dashboard/index.html',
        total_students=total_students,
        total_rooms=total_rooms,
        total_beds=total_beds,
        occupied_beds=occupied_beds,
        available_beds=available_beds,
        maintenance_beds=maintenance_beds,
        total_capacity=total_capacity,
        occupancy_percentage=occupancy_percentage,
        monthly_collection=float(monthly_collection),
        pending_payments=float(pending_payments),
        total_employees=total_employees,
        today_present=today_present,
        today_absent=today_absent,
        today_leave=today_leave,
        today_attendance_rate=today_attendance_rate,
        pending_complaints=pending_complaints,
        active_visitors=active_visitors,
        recent_admissions=recent_admissions,
        recent_payments=recent_payments,
        recent_announcements=recent_announcements,
        hostels_summary=hostels_summary
    )


@dashboard_bp.route('/api/dashboard/chart-data')
@login_required
def chart_data():
    """
    Returns live database-driven JSON data for Chart.js interactive charts:
    - Monthly Revenue (last 6 months)
    - Student Admissions (by month)
    - Room Occupancy (Occupied vs Available)
    - Fee Collection Statistics (Collected vs Pending)
    - Attendance Statistics (Present, Absent, Leave)
    """
    today = date.today()

    # 1. Monthly Revenue (last 6 calendar months)
    revenue_labels = []
    revenue_data = []
    for i in range(5, -1, -1):
        # Calculate month date
        m_date = today.replace(day=1) - timedelta(days=i * 28)
        m_start = m_date.replace(day=1)
        # Next month start
        if m_start.month == 12:
            m_end = m_start.replace(year=m_start.year + 1, month=1)
        else:
            m_end = m_start.replace(month=m_start.month + 1)

        m_label = m_start.strftime('%b %Y')
        month_sum = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
            Payment.payment_date >= m_start,
            Payment.payment_date < m_end
        ).scalar()

        revenue_labels.append(m_label)
        revenue_data.append(float(month_sum))

    # 2. Student Admissions by Department
    dept_stats = db.session.query(
        Student.department, func.count(Student.id)
    ).filter_by(status='Active').group_by(Student.department).limit(6).all()

    dept_labels = [d[0] for d in dept_stats]
    dept_counts = [d[1] for d in dept_stats]

    # 3. Room Occupancy
    occupied_beds = Bed.query.filter_by(status='Occupied').count()
    available_beds = Bed.query.filter_by(status='Available').count()
    maintenance_beds = Bed.query.filter_by(status='Maintenance').count()

    # 4. Fee Collection Overall
    total_collected = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).scalar()
    total_invoiced = db.session.query(func.coalesce(func.sum(FeeInvoice.total_amount), 0)).scalar()
    total_pending = max(0.0, float(total_invoiced) - float(total_collected))

    # 5. Attendance distribution (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    attendance_counts = db.session.query(
        StudentAttendance.status, func.count(StudentAttendance.id)
    ).filter(StudentAttendance.date >= thirty_days_ago).group_by(StudentAttendance.status).all()
    
    att_map = {'Present': 0, 'Absent': 0, 'Leave': 0}
    for status, count in attendance_counts:
        if status in att_map:
            att_map[status] = count

    return jsonify({
        'revenue': {
            'labels': revenue_labels,
            'data': revenue_data
        },
        'admissions_by_dept': {
            'labels': dept_labels,
            'data': dept_counts
        },
        'occupancy': {
            'labels': ['Occupied Beds', 'Available Beds', 'Under Maintenance'],
            'data': [occupied_beds, available_beds, maintenance_beds]
        },
        'finance_overview': {
            'labels': ['Collected Fees (PKR)', 'Pending Dues (PKR)'],
            'data': [float(total_collected), total_pending]
        },
        'attendance_stats': {
            'labels': ['Present', 'Absent', 'On Leave'],
            'data': [att_map['Present'], att_map['Absent'], att_map['Leave']]
        }
    })
