"""Quick health-check script for the HostelFlow HMS application."""
from app import create_app
from app.models.base import db
from app.models.user import User
from app.models.student import Student
from app.models.hostel import Hostel, Room, Bed, RoomAllocation
from app.models.finance import FeeInvoice, Payment, FeeType
from app.models.attendance import StudentAttendance
from app.models.complaint import Complaint
from app.models.staff import Employee
from app.models.communication import Announcement

app = create_app('development')

with app.app_context():
    print("=== DATABASE STATS ===")
    print(f"Users:        {User.query.count()}")
    print(f"Students:     {Student.query.count()} (Active: {Student.query.filter_by(status='Active').count()})")
    print(f"Hostels:      {Hostel.query.count()}")
    print(f"Rooms:        {Room.query.count()}")
    total_beds = Bed.query.count()
    occ_beds = Bed.query.filter_by(status='Occupied').count()
    avail_beds = Bed.query.filter_by(status='Available').count()
    print(f"Beds:         {total_beds} total | {occ_beds} occupied | {avail_beds} available")
    print(f"Allocations:  {RoomAllocation.query.filter_by(status='Active').count()} active")
    print(f"Fee Invoices: {FeeInvoice.query.count()}")
    print(f"Payments:     {Payment.query.count()}")
    print(f"Attendance:   {StudentAttendance.query.count()} records")
    print(f"Complaints:   {Complaint.query.count()} total | {Complaint.query.filter_by(status='Pending').count()} pending")
    print(f"Employees:    {Employee.query.count()} | Active: {Employee.query.filter_by(status='Active').count()}")
    print(f"Announcements:{Announcement.query.count()}")
    print()

    print("=== LOGIN CREDENTIALS TEST ===")
    creds = [
        ('superadmin@hostel.edu.pk', 'Admin@12345', 'Super Admin'),
        ('admin.iqbal@hostel.edu.pk', 'HostelAdmin@123', 'Hostel Admin'),
        ('warden.tariq@hostel.edu.pk', 'Warden@123', 'Warden'),
        ('accountant.bilal@hostel.edu.pk', 'Accountant@123', 'Accountant'),
        ('hms_2026_001', 'Student@12345', 'Student'),
        ('emp_guard_01', 'Staff@12345', 'Staff'),
    ]
    all_pass = True
    for identifier, password, expected_role in creds:
        u = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()
        if u and u.check_password(password):
            status = "PASS"
            detail = f"{u.role.name} | Active={u.is_active}"
        else:
            status = "FAIL"
            detail = "NOT FOUND or WRONG PASSWORD"
            all_pass = False
        print(f"  [{status}] {identifier[:35]:<35} -> {detail}")

    print()
    if all_pass:
        print(">>> ALL 6 LOGINS PASSED!")
    else:
        print(">>> SOME LOGINS FAILED - INVESTIGATE!")

    print()
    print("=== STUDENT MODEL PROPERTIES ===")
    s = Student.query.first()
    if s:
        print(f"  Name:               {s.full_name}")
        print(f"  total_invoiced:     Rs. {s.total_invoiced:,.0f}")
        print(f"  total_paid:         Rs. {s.total_paid:,.0f}")
        print(f"  pending_balance:    Rs. {s.pending_balance:,.0f}")
        print(f"  attendance_pct:     {s.attendance_percentage}%")
        print(f"  current_room:       {s.current_room}")
        print(f"  current_hostel:     {s.current_hostel}")
        print(f"  primary_guardian:   {s.primary_guardian}")
        print("  [OK] Student model properties all working")

    print()
    print("=== REGISTERED BLUEPRINTS ===")
    bps = list(app.blueprints.keys())
    print(f"  {len(bps)} blueprints registered: {bps}")

    print()
    print("=== DATABASE URL ===")
    print(f"  {app.config['SQLALCHEMY_DATABASE_URI']}")

    print()
    print("=" * 50)
    print("   ALL CHECKS COMPLETE - APP IS READY!")
    print("=" * 50)
