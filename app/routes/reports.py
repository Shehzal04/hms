from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from flask_login import login_required
from app.models.base import db
from app.models.student import Student
from app.models.hostel import Hostel, Room, Bed, RoomAllocation
from app.models.finance import FeeInvoice, Payment
from app.models.attendance import StudentAttendance
from app.models.complaint import Complaint
from app.models.visitor import Visitor
from app.models.staff import Employee
from app.models.mess import MessSubscription
from app.services.reporting_service import generate_csv_response, generate_pdf_report_buffer
from app.services.auth_service import role_required

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Accountant', 'Warden')
def index():
    report_type = request.args.get('report_type', 'admissions').strip()
    from_date_str = request.args.get('from_date', '')
    to_date_str = request.args.get('to_date', '')
    export_format = request.args.get('export', '')

    headers = []
    rows = []
    title = "System Report"

    # 1. Student Admissions Report
    if report_type == 'admissions':
        title = "Student Admission Report"
        headers = ['Student ID', 'Full Name', 'Father Name', 'CNIC', 'Gender', 'University', 'Department', 'Admission Date', 'Status']
        query = Student.query
        if from_date_str:
            query = query.filter(Student.admission_date >= datetime.strptime(from_date_str, '%Y-%m-%d').date())
        if to_date_str:
            query = query.filter(Student.admission_date <= datetime.strptime(to_date_str, '%Y-%m-%d').date())
        students = query.order_by(Student.admission_date.desc()).all()
        for s in students:
            rows.append([
                s.student_id_code, s.full_name, s.father_name, s.cnic, s.gender,
                s.university_name, s.department, s.admission_date.strftime('%d-%b-%Y'), s.status
            ])

    # 2. Room Occupancy Report
    elif report_type == 'occupancy':
        title = "Room Occupancy & Capacity Report"
        headers = ['Hostel Name', 'Floor', 'Room Number', 'Type', 'Total Beds', 'Occupied Beds', 'Available Beds', 'Monthly Rent (PKR)', 'Status']
        rooms = Room.query.order_by(Room.hostel_id.asc(), Room.floor_number.asc(), Room.room_number.asc()).all()
        for r in rooms:
            rows.append([
                r.hostel.name, f"Floor {r.floor_number}", r.room_number, r.room_type,
                r.total_beds, r.occupied_beds_count, r.available_beds_count,
                f"{r.monthly_rent:,.0f}", r.status
            ])

    # 3. Available Rooms Report
    elif report_type == 'available_rooms':
        title = "Available Rooms & Vacancies Report"
        headers = ['Hostel Name', 'Floor', 'Room Number', 'Room Type', 'Available Beds', 'Rent / Month (PKR)', 'Facilities']
        rooms = Room.query.filter(Room.status != 'Maintenance').all()
        avail_rooms = [r for r in rooms if r.available_beds_count > 0]
        for r in avail_rooms:
            rows.append([
                r.hostel.name, f"Floor {r.floor_number}", r.room_number, r.room_type,
                r.available_beds_count, f"{r.monthly_rent:,.0f}", r.facilities
            ])

    # 4. Fee Collection Report
    elif report_type == 'fee_collection':
        title = "Fee Collection & Payments Report"
        headers = ['Receipt No', 'Date', 'Student ID', 'Student Name', 'Invoice Ref', 'Method', 'Txn ID', 'Received By', 'Amount (PKR)']
        query = Payment.query.join(Student)
        if from_date_str:
            query = query.filter(Payment.payment_date >= datetime.strptime(from_date_str, '%Y-%m-%d').date())
        if to_date_str:
            query = query.filter(Payment.payment_date <= datetime.strptime(to_date_str, '%Y-%m-%d').date())
        payments = query.order_by(Payment.payment_date.desc()).all()
        for p in payments:
            rows.append([
                p.receipt_number, p.payment_date.strftime('%d-%b-%Y'),
                p.student.student_id_code, p.student.full_name,
                p.invoice.invoice_number if p.invoice else 'N/A',
                p.payment_method, p.transaction_id or 'Cash', p.received_by,
                f"{p.amount:,.2f}"
            ])

    # 5. Pending Fee Report
    elif report_type == 'pending_fees':
        title = "Outstanding & Pending Dues Report"
        headers = ['Invoice No', 'Student ID', 'Student Name', 'Phone', 'Due Date', 'Total Amount', 'Paid Amount', 'Balance Due (PKR)', 'Status']
        query = FeeInvoice.query.filter(FeeInvoice.status.in_(['Unpaid', 'Partial', 'Overdue'])).join(Student)
        invoices = query.order_by(FeeInvoice.due_date.asc()).all()
        for inv in invoices:
            rows.append([
                inv.invoice_number, inv.student.student_id_code, inv.student.full_name,
                inv.student.phone_number, inv.due_date.strftime('%d-%b-%Y'),
                f"{inv.total_amount:,.0f}", f"{inv.paid_amount:,.0f}",
                f"{inv.balance_due:,.0f}", inv.status
            ])

    # 6. Student Attendance Report
    elif report_type == 'attendance':
        title = "Student Attendance Report"
        headers = ['Date', 'Student ID', 'Student Name', 'Hostel / Room', 'Status', 'Marked By', 'Remarks']
        query = StudentAttendance.query.join(Student)
        if from_date_str:
            query = query.filter(StudentAttendance.date >= datetime.strptime(from_date_str, '%Y-%m-%d').date())
        if to_date_str:
            query = query.filter(StudentAttendance.date <= datetime.strptime(to_date_str, '%Y-%m-%d').date())
        attendances = query.order_by(StudentAttendance.date.desc()).limit(200).all()
        for a in attendances:
            rm = a.student.current_room
            hst = a.student.current_hostel
            loc = f"{hst.name} Rm {rm.room_number}" if rm and hst else "Not Allocated"
            rows.append([
                a.date.strftime('%d-%b-%Y'), a.student.student_id_code, a.student.full_name,
                loc, a.status, a.marked_by, a.remarks or ''
            ])

    # 7. Complaint Report
    elif report_type == 'complaints':
        title = "Complaints & Grievances Report"
        headers = ['Ticket No', 'Date', 'Student Name', 'Category', 'Subject', 'Priority', 'Assigned Staff', 'Status']
        complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
        for c in complaints:
            rows.append([
                c.ticket_number, c.created_at.strftime('%d-%b-%Y'),
                c.student.full_name, c.category, c.title[:30], c.priority,
                c.assigned_employee.full_name if c.assigned_employee else 'Unassigned',
                c.status
            ])

    # 8. Visitor Report
    elif report_type == 'visitors':
        title = "Visitor Log Report"
        headers = ['Visitor Name', 'CNIC', 'Contact', 'Student Visited', 'Relationship', 'Purpose', 'Check-In', 'Check-Out', 'Status']
        visitors = Visitor.query.order_by(Visitor.check_in.desc()).all()
        for v in visitors:
            rows.append([
                v.visitor_name, v.cnic, v.phone_number, v.student.full_name,
                v.relation, v.purpose, v.check_in.strftime('%d-%b-%Y %I:%M %p'),
                v.check_out.strftime('%d-%b-%Y %I:%M %p') if v.check_out else 'Still Inside',
                'Departed' if v.check_out else 'Inside'
            ])

    # 9. Staff Report
    elif report_type == 'staff':
        title = "Staff & Employee Payroll Report"
        headers = ['Emp Code', 'Full Name', 'Designation', 'CNIC', 'Phone', 'Joining Date', 'Monthly Salary (PKR)', 'Shift', 'Status']
        employees = Employee.query.order_by(Employee.designation.asc()).all()
        for e in employees:
            rows.append([
                e.employee_code, e.full_name, e.designation, e.cnic, e.phone_number,
                e.joining_date.strftime('%d-%b-%Y'), f"{e.salary:,.0f}", e.duty_shift, e.status
            ])

    # Handle Exports
    if export_format == 'csv':
        filename = f"{report_type}_report_{date.today().strftime('%Y%m%d')}.csv"
        return generate_csv_response(filename, headers, rows)

    if export_format == 'pdf':
        pdf_buf = generate_pdf_report_buffer(title, headers, rows, subtitle=f"Date Range: {from_date_str or 'All'} to {to_date_str or 'Today'}")
        return send_file(
            pdf_buf,
            as_attachment=True,
            download_name=f"{report_type}_report_{date.today().strftime('%Y%m%d')}.pdf",
            mimetype='application/pdf'
        )

    return render_template(
        'reports/index.html',
        report_type=report_type,
        from_date=from_date_str,
        to_date=to_date_str,
        title=title,
        headers=headers,
        rows=rows,
        total_records=len(rows)
    )
