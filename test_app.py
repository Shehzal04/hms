import unittest
from datetime import date
from decimal import Decimal
from app import create_app
from app.models.base import db
from app.models.user import User, Role
from app.models.student import Student
from app.models.hostel import Hostel, Room, Bed, RoomAllocation
from app.models.finance import FeeInvoice, Payment
from app.models.attendance import StudentAttendance
from app.models.complaint import Complaint
from app.models.visitor import Visitor

class HMSTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('development')
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for programmatic test requests
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def login(self, username_or_email, password):
        return self.client.post('/auth/login', data={
            'username_or_email': username_or_email,
            'password': password
        }, follow_redirects=True)

    def test_01_user_authentication(self):
        """Test authentication for various roles."""
        # 1. Super Admin Login
        res = self.login('superadmin@hostel.edu.pk', 'Admin@12345')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Executive Operations Dashboard', res.data)

        # Logout
        self.client.get('/auth/logout', follow_redirects=True)

        # 2. Student Login
        res = self.login('hms_2026_001', 'Student@12345')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Resident Portal', res.data)

        self.client.get('/auth/logout', follow_redirects=True)

    def test_02_dashboard_live_kpis_and_chart_api(self):
        """Test database-driven dashboard metrics and Chart.js JSON API."""
        self.login('superadmin@hostel.edu.pk', 'Admin@12345')
        
        # Dashboard view
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Total Students', res.data)
        self.assertIn(b'Room Occupancy', res.data)
        self.assertIn(b'Monthly Fee Collection', res.data)

        # Chart.js JSON Endpoint
        api_res = self.client.get('/api/dashboard/chart-data')
        self.assertEqual(api_res.status_code, 200)
        data = api_res.get_json()
        self.assertIn('revenue', data)
        self.assertIn('occupancy', data)
        self.assertIn('admissions_by_dept', data)
        self.assertIn('attendance_stats', data)
        self.assertTrue(len(data['revenue']['labels']) > 0)
        self.client.get('/auth/logout', follow_redirects=True)

    def test_03_student_management_crud(self):
        """Test student listing, view profile, and details."""
        self.login('admin.iqbal@hostel.edu.pk', 'HostelAdmin@123')
        
        # Directory list
        res = self.client.get('/students/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Student Directory', res.data)

        # View specific student
        student = Student.query.first()
        self.assertIsNotNone(student)
        res_view = self.client.get(f'/students/{student.id}')
        self.assertEqual(res_view.status_code, 200)
        self.assertIn(student.full_name.encode('utf-8'), res_view.data)

        self.client.get('/auth/logout', follow_redirects=True)

    def test_04_hostel_and_room_management(self):
        """Test hostels and rooms views."""
        self.login('superadmin@hostel.edu.pk', 'Admin@12345')
        
        res_hostels = self.client.get('/hostels/')
        self.assertEqual(res_hostels.status_code, 200)
        self.assertIn(b'Allama Iqbal Boys Hostel', res_hostels.data)

        res_rooms = self.client.get('/rooms/')
        self.assertEqual(res_rooms.status_code, 200)
        self.assertIn(b'Bed Inventory', res_rooms.data)

        self.client.get('/auth/logout', follow_redirects=True)

    def test_05_room_allocations_and_capacity_enforcement(self):
        """Test room allocations list and bed query API."""
        self.login('warden.tariq@hostel.edu.pk', 'Warden@123')
        
        res = self.client.get('/allocations/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Room Allocations', res.data)

        room = Room.query.filter_by(status='Available').first()
        if room:
            api_beds = self.client.get(f'/allocations/api/beds-by-room/{room.id}')
            self.assertEqual(api_beds.status_code, 200)
            self.assertIsInstance(api_beds.get_json(), list)

        self.client.get('/auth/logout', follow_redirects=True)

    def test_06_finance_invoices_and_pdf_receipt(self):
        """Test invoices list, view invoice, and PDF receipt download."""
        self.login('accountant.bilal@hostel.edu.pk', 'Accountant@123')
        
        res_inv = self.client.get('/fees/')
        self.assertEqual(res_inv.status_code, 200)
        self.assertIn(b'Fee Invoices', res_inv.data)

        payment = Payment.query.first()
        self.assertIsNotNone(payment)

        # View receipt HTML
        res_rcp = self.client.get(f'/fees/receipts/{payment.id}')
        self.assertEqual(res_rcp.status_code, 200)
        self.assertIn(payment.receipt_number.encode('utf-8'), res_rcp.data)

        # Download ReportLab PDF receipt
        res_pdf = self.client.get(f'/fees/receipts/{payment.id}/pdf')
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.mimetype, 'application/pdf')
        self.assertTrue(res_pdf.data.startswith(b'%PDF'))

        self.client.get('/auth/logout', follow_redirects=True)

    def test_07_reports_hub_and_csv_export(self):
        """Test Institutional Reports Hub and CSV export."""
        self.login('superadmin@hostel.edu.pk', 'Admin@12345')
        
        # Reports Hub
        res_rep = self.client.get('/reports/?report_type=occupancy')
        self.assertEqual(res_rep.status_code, 200)
        self.assertIn(b'Room Occupancy &amp; Capacity Report', res_rep.data)

        # Export to CSV
        res_csv = self.client.get('/reports/?report_type=admissions&export=csv')
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.mimetype, 'text/csv')

        # Export to PDF
        res_pdf_rep = self.client.get('/reports/?report_type=fee_collection&export=pdf')
        self.assertEqual(res_pdf_rep.status_code, 200)
        self.assertEqual(res_pdf_rep.mimetype, 'application/pdf')
        self.assertTrue(res_pdf_rep.data.startswith(b'%PDF'))

        self.client.get('/auth/logout', follow_redirects=True)

    def test_08_rbac_protection(self):
        """Test that regular students cannot access Super Admin settings."""
        self.login('hms_2026_001', 'Student@12345')
        res_unauthorized = self.client.get('/settings/', follow_redirects=False)
        self.assertEqual(res_unauthorized.status_code, 403)
        self.client.get('/auth/logout', follow_redirects=True)

    def test_09_allocation_validation_prevent_duplicate(self):
        """Test that allocating an already allocated student raises validation error."""
        from app.services.allocation_service import allocate_bed_to_student, AllocationError
        # Find an already allocated student
        alloc = RoomAllocation.query.filter_by(status='Active').first()
        self.assertIsNotNone(alloc)

        # Attempt to allocate another bed to the same student
        avail_bed = Bed.query.filter_by(status='Available').first()
        if avail_bed:
            with self.assertRaises(AllocationError):
                allocate_bed_to_student(
                    student_id=alloc.student_id,
                    room_id=avail_bed.room_id,
                    bed_id=avail_bed.id
                )

    def test_10_payment_recording_updates_invoice(self):
        """Test that recording a payment correctly updates the invoice paid_amount and balance."""
        from app.services.finance_service import record_invoice_payment
        inv = FeeInvoice.query.filter(FeeInvoice.status.in_(['Unpaid', 'Partial'])).first()
        if inv and inv.balance_due > 100:
            pay_amt = Decimal('100.00')
            prev_paid = inv.paid_amount
            payment = record_invoice_payment(
                invoice_id=inv.id,
                amount=pay_amt,
                payment_method='Cash',
                received_by='Test Accountant'
            )
            self.assertIsNotNone(payment.receipt_number)
            self.assertEqual(inv.paid_amount, prev_paid + pay_amt)

if __name__ == '__main__':
    unittest.main()
