import os
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from app import create_app
from app.models.base import db
from app.models.user import User, Role
from app.models.hostel import Hostel, Room, Bed, RoomAllocation, RoomTransferHistory
from app.models.student import Student, Guardian, Document
from app.models.finance import FeeType, FeeInvoice, FeeInvoiceItem, Payment
from app.models.attendance import StudentAttendance, LateEntry
from app.models.complaint import Complaint, ComplaintUpdate
from app.models.visitor import Visitor
from app.models.mess import MessMenu, MessSubscription
from app.models.staff import Employee, EmployeeAttendance, EmployeeSalary, Task
from app.models.communication import Announcement, Notification
from app.models.system import AuditLog, HostelSetting

app = create_app('development')

def seed_database():
    with app.app_context():
        print("Initializing database tables...")
        db.create_all()

        # Check if already seeded
        if User.query.filter_by(username='superadmin').first():
            print("Database appears to already be populated. Skipping duplicate seed.")
            return

        print("Seeding Roles and Permissions...")
        roles = {
            'Super Admin': 'Unrestricted master access across all hostels, financials, settings and users',
            'Hostel Admin': 'Administrative oversight of hostel operations, rooms, students, and employees',
            'Warden': 'Hostel residential supervision, daily attendance, disciplinary logs, and complaints',
            'Accountant': 'Hostel finance, fee invoicing, receipts, dues tracking, and financial ledgers',
            'Student': 'Resident self-service portal, room allocation view, complaints, and fee receipts',
            'Staff': 'Operational staff, cleaners, security guards, electricians, duty checklists'
        }
        role_objs = {}
        for r_name, r_desc in roles.items():
            r = Role.query.filter_by(name=r_name).first()
            if not r:
                r = Role(name=r_name, description=r_desc)
                db.session.add(r)
                db.session.flush()
            role_objs[r_name] = r

        print("Seeding Fee Types...")
        fee_types_data = [
            ('Admission Fee', 'One-time initial hostel admission & processing fee', 10000.00),
            ('Monthly Hostel Fee', 'Monthly accommodation and room maintenance charges', 15000.00),
            ('Security Deposit', 'Refundable hostel security deposit', 20000.00),
            ('Mess Charges', 'Monthly 3-meals mess catering subscription', 12000.00),
            ('Electricity Charges', 'Utility and air-cooler / heating surcharges', 3000.00),
            ('Other Charges', 'Laundry, gym, and recreational facility charges', 1500.00)
        ]
        fee_type_objs = {}
        for name, desc, amt in fee_types_data:
            ft = FeeType.query.filter_by(name=name).first()
            if not ft:
                ft = FeeType(name=name, description=desc, default_amount=Decimal(str(amt)))
                db.session.add(ft)
                db.session.flush()
            fee_type_objs[name] = ft

        print("Seeding System Settings...")
        settings_data = [
            ('institution_name', 'National University Hostels & Residencies', 'Official Institution Name', 'General'),
            ('curfew_time', '10:00 PM', 'Official Resident Evening Curfew Time', 'Discipline'),
            ('late_fee_per_day', '100', 'Late Fee Surcharge per Day (PKR)', 'Finance'),
            ('emergency_phone', '+92 51 9085 2026', '24/7 Security & Warden Emergency Helpline', 'Emergency'),
            ('visitor_allowed_hours', '4:00 PM - 8:00 PM', 'Visiting Hours for Parents & Guests', 'Security'),
            ('mess_daily_cutoff', '9:00 PM', 'Daily Mess Meal Cancellation Cutoff', 'Mess')
        ]
        for k, v, d, c in settings_data:
            if not HostelSetting.query.filter_by(key_name=k).first():
                hs = HostelSetting(key_name=k, value=v, description=d, category=c)
                db.session.add(hs)

        print("Seeding Super Admin, Admins, Wardens, and Accountants...")
        # 1 Super Admin
        super_admin = User(
            username='superadmin',
            email='superadmin@hostel.edu.pk',
            full_name='Engr. Asadullah Khan',
            role_id=role_objs['Super Admin'].id,
            is_active=True
        )
        super_admin.set_password('Admin@12345')
        db.session.add(super_admin)

        # 2 Hostel Admins
        admin1 = User(
            username='admin_iqbal',
            email='admin.iqbal@hostel.edu.pk',
            full_name='Muhammad Rizwan Qureshi',
            role_id=role_objs['Hostel Admin'].id,
            is_active=True
        )
        admin1.set_password('HostelAdmin@123')

        admin2 = User(
            username='admin_fatima',
            email='admin.fatima@hostel.edu.pk',
            full_name='Dr. Samina Shaheen',
            role_id=role_objs['Hostel Admin'].id,
            is_active=True
        )
        admin2.set_password('HostelAdmin@123')
        db.session.add_all([admin1, admin2])

        # 3 Wardens
        warden1 = User(
            username='warden_tariq',
            email='warden.tariq@hostel.edu.pk',
            full_name='Prof. Tariq Mehmood',
            role_id=role_objs['Warden'].id,
            is_active=True
        )
        warden1.set_password('Warden@123')

        warden2 = User(
            username='warden_ayesha',
            email='warden.ayesha@hostel.edu.pk',
            full_name='Prof. Ayesha Siddiqui',
            role_id=role_objs['Warden'].id,
            is_active=True
        )
        warden2.set_password('Warden@123')

        warden3 = User(
            username='warden_usman',
            email='warden.usman@hostel.edu.pk',
            full_name='Usman Ghani Abbasi',
            role_id=role_objs['Warden'].id,
            is_active=True
        )
        warden3.set_password('Warden@123')
        db.session.add_all([warden1, warden2, warden3])

        # 2 Accountants
        acc1 = User(
            username='accountant_bilal',
            email='accountant.bilal@hostel.edu.pk',
            full_name='Bilal Ahmad FCA',
            role_id=role_objs['Accountant'].id,
            is_active=True
        )
        acc1.set_password('Accountant@123')

        acc2 = User(
            username='accountant_sadia',
            email='accountant.sadia@hostel.edu.pk',
            full_name='Sadia Parveen ACMA',
            role_id=role_objs['Accountant'].id,
            is_active=True
        )
        acc2.set_password('Accountant@123')
        db.session.add_all([acc1, acc2])
        db.session.flush()

        print("Seeding 10 Staff Members...")
        staff_data = [
            ('EMP-101', 'Subedar (R) Muhammad Rafiq', 'Security Guard', '37405-1122334-1', '+92 301 5551001', 'Morning (7:00 AM - 3:00 PM)', 38000),
            ('EMP-102', 'Havaldar (R) Gulzar Khan', 'Security Guard', '17301-2233445-1', '+92 302 5551002', 'Night (11:00 PM - 7:00 AM)', 42000),
            ('EMP-103', 'Muhammad Akram', 'Electrician', '35201-3344556-1', '+92 303 5551003', 'General (9:00 AM - 5:00 PM)', 45000),
            ('EMP-104', 'Liaquat Ali', 'Maintenance Staff', '35202-4455667-1', '+92 304 5551004', 'General (9:00 AM - 5:00 PM)', 40000),
            ('EMP-105', 'Ustad Bashir Ahmad', 'Mess Staff', '38403-5566778-1', '+92 305 5551005', 'Morning (7:00 AM - 3:00 PM)', 50000),
            ('EMP-106', 'Sajid Masih', 'Cleaner', '35201-6677889-1', '+92 306 5551006', 'Morning (7:00 AM - 3:00 PM)', 32000),
            ('EMP-107', 'Asif Raza', 'Cleaner', '35201-7788990-1', '+92 307 5551007', 'Evening (3:00 PM - 11:00 PM)', 32000),
            ('EMP-108', 'Naveed Akhtar', 'Electrician', '37405-8899001-1', '+92 308 5551008', 'Evening (3:00 PM - 11:00 PM)', 45000),
            ('EMP-109', 'Naimat Ullah', 'Mess Staff', '17301-9900112-1', '+92 309 5551009', 'Evening (3:00 PM - 11:00 PM)', 45000),
            ('EMP-110', 'Allah Ditta', 'Security Guard', '38403-1011121-1', '+92 310 5551010', 'Evening (3:00 PM - 11:00 PM)', 38000),
        ]
        employee_objs = []
        for code, name, desig, cnic, phone, shift, sal in staff_data:
            # Create user account for security guard 1 for demo
            emp_user = None
            if code == 'EMP-101':
                emp_user = User(
                    username='emp_guard_01',
                    email='guard.rafiq@hostel.edu.pk',
                    full_name=name,
                    role_id=role_objs['Staff'].id,
                    is_active=True
                )
                emp_user.set_password('Staff@12345')
                db.session.add(emp_user)
                db.session.flush()

            emp = Employee(
                user_id=emp_user.id if emp_user else None,
                employee_code=code,
                full_name=name,
                designation=desig,
                cnic=cnic,
                phone_number=phone,
                email=f"{code.lower()}@hostel.edu.pk",
                address='Hostel Staff Quarters, Sector H-12, Islamabad',
                joining_date=date(2023, 1, 15),
                salary=Decimal(str(sal)),
                duty_shift=shift,
                status='Active'
            )
            db.session.add(emp)
            employee_objs.append(emp)
        db.session.flush()

        print("Seeding Hostels...")
        hostels_data = [
            ('Allama Iqbal Boys Hostel', 'Boys', 'Block A, University Campus, Sector H-12, Islamabad', '+92 51 9085 2101', 'Prof. Tariq Mehmood', 3, 120, 'Flagship senior boys hostel with attached baths and high speed fiber internet.'),
            ('Fatima Jinnah Girls Hostel', 'Girls', 'Block C, University Campus, Sector H-12, Islamabad', '+92 51 9085 2102', 'Prof. Ayesha Siddiqui', 3, 100, 'Secure residential facility for female scholars with 24/7 security and dedicated female staff.'),
            ('Sir Syed Boys Hostel', 'Boys', 'Block B, University Campus, Sector H-12, Islamabad', '+92 51 9085 2103', 'Usman Ghani Abbasi', 2, 80, 'Freshmen undergraduate hostel with spacious study rooms and sports grounds.')
        ]
        hostel_objs = []
        for h_name, h_type, addr, phone, warden, floors, cap, desc in hostels_data:
            h = Hostel(
                name=h_name,
                hostel_type=h_type,
                address=addr,
                contact_number=phone,
                warden_name=warden,
                total_floors=floors,
                capacity=cap,
                description=desc,
                status='Active'
            )
            db.session.add(h)
            hostel_objs.append(h)
        db.session.flush()

        print("Seeding 30 Rooms with 100+ Beds...")
        # 30 Rooms distributed across hostels:
        # Hostel 1: 12 rooms (101-104 on F1, 201-204 on F2, 301-304 on F3)
        # Hostel 2: 10 rooms (101-103 on F1, 201-204 on F2, 301-303 on F3)
        # Hostel 3: 8 rooms (101-104 on F1, 201-204 on F2)
        room_types_specs = [
            ('Single', 1, 25000.00, 'AC, Attached Bath, Refrigerator, Study Table, Balcony'),
            ('Double', 2, 16000.00, 'Attached Bath, Study Table, Cupboard, Ceiling Fan'),
            ('Triple', 3, 13000.00, 'Common Bath, Study Table, Cupboard, High Speed WiFi'),
            ('Four-Seater', 4, 11000.00, 'Spacious Room, Cupboard, Study Desks, Common Bath')
        ]

        all_beds = []
        room_count = 0
        h_plan = [
            (hostel_objs[0], 3, 4),  # 3 floors, 4 rooms each = 12 rooms
            (hostel_objs[1], 3, 3),  # 3 floors, 3-4 rooms each = 10 rooms (extra on F2)
            (hostel_objs[2], 2, 4),  # 2 floors, 4 rooms each = 8 rooms
        ]

        created_rooms = []
        for h_obj, num_floors, rooms_per_floor in h_plan:
            for fl in range(1, num_floors + 1):
                count_this_floor = rooms_per_floor
                if h_obj == hostel_objs[1] and fl == 2:
                    count_this_floor = 4  # total 10 for hostel 2

                for rm_idx in range(1, count_this_floor + 1):
                    room_count += 1
                    rm_num = f"{fl}0{rm_idx}"
                    
                    # Distribute room types
                    type_idx = (fl + rm_idx) % 4
                    r_type, r_beds, r_rent, r_fac = room_types_specs[type_idx]

                    room = Room(
                        hostel_id=h_obj.id,
                        floor_number=fl,
                        room_number=rm_num,
                        room_type=r_type,
                        total_beds=r_beds,
                        monthly_rent=Decimal(str(r_rent)),
                        status='Available',
                        facilities=r_fac
                    )
                    db.session.add(room)
                    db.session.flush()
                    created_rooms.append(room)

                    # Create beds
                    for b_num in range(1, r_beds + 1):
                        bed = Bed(
                            room_id=room.id,
                            bed_number=f"Bed-{b_num}",
                            status='Available'
                        )
                        db.session.add(bed)
                        all_beds.append(bed)

        db.session.flush()
        print(f"Created {len(created_rooms)} rooms and {len(all_beds)} beds total.")

        print("Seeding 100 Students with Realistic Pakistani Profiles...")
        pak_first_male = [
            'Muhammad', 'Ali', 'Hamza', 'Ahmed', 'Hassan', 'Usman', 'Bilal', 'Zain', 'Omer',
            'Daniyal', 'Talha', 'Haris', 'Saad', 'Fahad', 'Abdullah', 'Zeeshan', 'Shahzaib',
            'Waleed', 'Mustafa', 'Arham', 'Taimoor', 'Sheraz', 'Kashif', 'Farhan', 'Junaid'
        ]
        pak_first_female = [
            'Fatima', 'Ayesha', 'Zainab', 'Maryam', 'Khadija', 'Mahnoor', 'Hira', 'Sana',
            'Iqra', 'Bushra', 'Anam', 'Laiba', 'Mehak', 'Alishba', 'Noor', 'Rabia', 'Rida'
        ]
        pak_surnames = [
            'Khan', 'Malik', 'Chaudhry', 'Qureshi', 'Abbasi', 'Butt', 'Sheikh', 'Ansari',
            'Memon', 'Shah', 'Jatoi', 'Tareen', 'Mirza', 'Raza', 'Dar', 'Bhatti', 'Siddiqui'
        ]
        pak_cities = [
            'Lahore', 'Rawalpindi', 'Islamabad', 'Karachi', 'Peshawar', 'Multan',
            'Faisalabad', 'Abbottabad', 'Quetta', 'Gujranwala', 'Sialkot', 'Hyderabad', 'Bahawalpur'
        ]
        universities = [
            'National University of Sciences & Technology (NUST)',
            'FAST-NUCES Islamabad Campus',
            'COMSATS University Islamabad',
            'Quaid-i-Azam University Islamabad',
            'University of Engineering & Technology (UET)',
            'Institute of Space Technology (IST)'
        ]
        departments = [
            ('Computer Science', 'BS Computer Science'),
            ('Software Engineering', 'BS Software Engineering'),
            ('Electrical Engineering', 'BS Electrical Engineering'),
            ('Artificial Intelligence', 'BS Artificial Intelligence'),
            ('Business Administration', 'BBA (Honors)'),
            ('Data Science', 'BS Data Science'),
            ('Civil Engineering', 'BS Civil Engineering')
        ]
        semesters = ['1st Semester', '2nd Semester', '3rd Semester', '4th Semester', '5th Semester', '6th Semester', '7th Semester', '8th Semester']

        created_students = []
        random.seed(42)  # Deterministic seed for reproducible testing

        # Let's create 70 Male students (for boys hostels) and 30 Female students (for girls hostel)
        for i in range(1, 101):
            is_female = (i > 70)
            if is_female:
                first_name = random.choice(pak_first_female)
                gender = 'Female'
            else:
                first_name = random.choice(pak_first_male)
                gender = 'Male'

            surname = random.choice(pak_surnames)
            full_name = f"{first_name} {surname}"
            father_name = f"{random.choice(pak_first_male)} {surname}"

            student_code = f"HMS-2026-{i:03d}"
            # Unique realistic Pakistani CNIC format
            # Area code: 35201 (Punjab), 42101 (Sindh), 17301 (KP), 61101 (ICT)
            area_code = random.choice(['35201', '37405', '42101', '17301', '61101', '38403', '54400'])
            cnic = f"{area_code}-{1000000 + i * 73:07d}-{1 if not is_female else 2}"
            email = f"student.{i:03d}@hostel.edu.pk"
            phone = f"+92 3{random.choice(['00', '01', '02', '12', '21', '33', '45'])}{random.randint(1000000, 9999999)}"
            emg_phone = f"+92 3{random.choice(['00', '11', '22', '31'])}{random.randint(1000000, 9999999)}"

            dept, degree = random.choice(departments)
            city = random.choice(pak_cities)
            univ = random.choice(universities)
            sem = random.choice(semesters)
            adm_date = date(2026, 1, 10) + timedelta(days=random.randint(0, 200))
            dob = date(2003, random.randint(1, 12), random.randint(1, 28))

            # Create User account for student
            username = f"hms_2026_{i:03d}"
            stu_user = User(
                username=username,
                email=email,
                full_name=full_name,
                role_id=role_objs['Student'].id,
                is_active=True
            )
            stu_user.set_password('Student@12345')
            db.session.add(stu_user)
            db.session.flush()

            student = Student(
                user_id=stu_user.id,
                student_id_code=student_code,
                full_name=full_name,
                father_name=father_name,
                cnic=cnic,
                email=email,
                phone_number=phone,
                emergency_contact=emg_phone,
                gender=gender,
                date_of_birth=dob,
                address=f"House #{random.randint(10, 450)}, Street #{random.randint(1, 25)}, Sector/Mohallah, {city}",
                city=city,
                university_name=univ,
                department=dept,
                degree_program=degree,
                semester=sem,
                admission_date=adm_date,
                profile_picture='default_student.png',
                status='Active'
            )
            db.session.add(student)
            db.session.flush()

            # Create Guardian
            guardian = Guardian(
                student_id=student.id,
                name=father_name,
                relationship='Father',
                phone_number=emg_phone,
                cnic=f"{area_code}-{2000000 + i * 51:07d}-1",
                occupation=random.choice(['Senior Civil Servant', 'Business Owner', 'Engineer', 'Bank Manager', 'Doctor', 'Professor', 'Landlord']),
                address=student.address
            )
            db.session.add(guardian)
            created_students.append(student)

        db.session.flush()
        print(f"Created {len(created_students)} students and linked guardian profiles.")

        print("Seeding Room Allocations (Allocating ~70 beds, keeping ~30 beds available)...")
        # Match boys to boys hostels (hostel 0, 2) and girls to girls hostel (hostel 1)
        male_students = [s for s in created_students if s.gender == 'Male']
        female_students = [s for s in created_students if s.gender == 'Female']

        boys_beds = [b for b in all_beds if b.room.hostel.hostel_type == 'Boys']
        girls_beds = [b for b in all_beds if b.room.hostel.hostel_type == 'Girls']

        allocated_count = 0
        # Allocate up to 50 male students
        for s, b in zip(male_students[:50], boys_beds[:50]):
            alloc = RoomAllocation(
                student_id=s.id,
                room_id=b.room_id,
                bed_id=b.id,
                allocation_date=s.admission_date,
                check_in_date=s.admission_date,
                status='Active',
                remarks='Standard room allocation'
            )
            b.status = 'Occupied'
            b.room.sync_status()
            db.session.add(alloc)
            allocated_count += 1

        # Allocate up to 20 female students
        for s, b in zip(female_students[:20], girls_beds[:20]):
            alloc = RoomAllocation(
                student_id=s.id,
                room_id=b.room_id,
                bed_id=b.id,
                allocation_date=s.admission_date,
                check_in_date=s.admission_date,
                status='Active',
                remarks='Allocated in Fatima Jinnah Girls Hostel'
            )
            b.status = 'Occupied'
            b.room.sync_status()
            db.session.add(alloc)
            allocated_count += 1

        db.session.flush()
        print(f"Allocated {allocated_count} students to beds successfully.")

        print("Seeding Fee Invoices & Payment Transactions...")
        # Create Invoices for students
        today = date.today()
        inv_count = 0
        pay_count = 0

        for idx, student in enumerate(created_students):
            # Create a monthly fee invoice
            inv_num = f"INV-2026-{1000 + idx}"
            issue_d = date(2026, 10, 1)
            due_d = date(2026, 10, 15)
            rent_amt = float(student.current_room.monthly_rent) if student.current_room else 15000.00
            total_amt = Decimal(str(rent_amt))

            # Vary statuses: ~50% paid, ~30% partial, ~20% overdue/unpaid
            if idx % 3 == 0:
                status = 'Paid'
                paid_amt = total_amt
            elif idx % 3 == 1:
                status = 'Partial'
                paid_amt = Decimal(str(round(rent_amt * 0.5, 2)))
            else:
                status = 'Overdue'
                paid_amt = Decimal('0.00')

            invoice = FeeInvoice(
                invoice_number=inv_num,
                student_id=student.id,
                title='Hostel Accommodation & Utility Fee - October 2026',
                issue_date=issue_d,
                due_date=due_d,
                total_amount=total_amt,
                paid_amount=paid_amt,
                late_fine=Decimal('500.00') if status == 'Overdue' else Decimal('0.00'),
                status=status,
                notes='Fee payment acknowledged via official university accounts office.'
            )
            db.session.add(invoice)
            db.session.flush()
            inv_count += 1

            # Invoice item
            item = FeeInvoiceItem(
                invoice_id=invoice.id,
                fee_type_id=fee_type_objs['Monthly Hostel Fee'].id,
                description=f"Room Rent & Facilities ({student.current_room.room_type if student.current_room else 'Standard'})",
                amount=total_amt
            )
            db.session.add(item)

            # If paid or partial, add Payment record
            if paid_amt > 0:
                rcp_num = f"RCP-2026-{1000 + idx}"
                payment = Payment(
                    receipt_number=rcp_num,
                    invoice_id=invoice.id,
                    student_id=student.id,
                    payment_date=issue_d + timedelta(days=random.randint(2, 10)),
                    amount=paid_amt,
                    payment_method=random.choice(['Bank Transfer', 'Cash', 'Online Payment']),
                    transaction_id=f"PK-TXN-{random.randint(100000, 999999)}",
                    received_by='Bilal Ahmad FCA (Accountant)',
                    status='Completed',
                    remarks='Payment verified against bank statement.'
                )
                db.session.add(payment)
                pay_count += 1

        db.session.flush()
        print(f"Generated {inv_count} fee invoices and {pay_count} payment receipts.")

        print("Seeding Daily Student Attendance Records...")
        # Seed 7 days of attendance for students
        for day_offset in range(7):
            att_date = today - timedelta(days=day_offset)
            for s in created_students[:40]:  # 40 students with records
                # 90% Present, 5% Absent, 5% Leave
                roll = random.random()
                if roll < 0.90:
                    st = 'Present'
                    rem = ''
                elif roll < 0.95:
                    st = 'Absent'
                    rem = 'Unexcused roll call absence'
                else:
                    st = 'Leave'
                    rem = 'Official weekend home pass'

                att = StudentAttendance(
                    student_id=s.id,
                    date=att_date,
                    status=st,
                    remarks=rem,
                    marked_by='Prof. Tariq Mehmood (Warden)'
                )
                db.session.add(att)

        # A few late curfew entries
        for s in created_students[:5]:
            le = LateEntry(
                student_id=s.id,
                actual_time=f"11:{random.randint(10, 55)} PM",
                reason=random.choice(['Late night university software project lab work', 'Delayed public transport return from Lahore', 'Family function attendance']),
                recorded_by='Subedar (R) Muhammad Rafiq'
            )
            db.session.add(le)

        print("Seeding Complaints & Grievance Tickets...")
        sample_complaints = [
            ('Electricity', 'Ceiling Fan Making Squeaking Noise', 'The ceiling fan in Room 101 vibrates loudly at speeds 3 and 4.', 'Medium', 'Resolved', employee_objs[2]),
            ('Internet', 'WiFi Signal Drop in Room Corner', 'WiFi signal is extremely weak near Bed-2. Unable to attend online Zoom lecture.', 'High', 'In Progress', employee_objs[2]),
            ('Water', 'Bathroom Sink Faucet Dripping Constantly', 'Water tap in attached bathroom leaks constantly throughout the night.', 'Medium', 'Resolved', employee_objs[3]),
            ('Room Maintenance', 'Cupboard Lock Handle Jammed', 'Key cannot turn in wardrobe drawer lock.', 'Low', 'Pending', employee_objs[3]),
            ('Cleaning', 'Corridor Dustbin Overflowing', 'Dustbin outside Room 204 needs janitorial emptying.', 'Low', 'Resolved', employee_objs[5]),
            ('Food / Mess', 'Dinner Served Lukewarm', 'Chapati was cold during 8:30 PM dinner serving.', 'Medium', 'Resolved', employee_objs[4]),
            ('Electricity', 'Study Lamp Socket Not Powering', 'Desk plug point has no current.', 'High', 'Pending', employee_objs[2]),
            ('Security', 'Unauthorized Noise After Midnight', 'Loud talking in common room after 11:30 PM.', 'Medium', 'Resolved', employee_objs[0]),
            ('Water', 'Low Water Pressure in Shower', 'Water pressure drops significantly in the morning between 7 AM and 8 AM.', 'High', 'In Progress', employee_objs[3]),
            ('Room Maintenance', 'Study Chair Armrest Loose', 'Chair armrest broke during exam study hours.', 'Low', 'Pending', employee_objs[3]),
        ]

        for idx, (cat, title, desc, prio, status, emp) in enumerate(sample_complaints):
            cmp_ticket = f"CMP-2026-{101 + idx}"
            stu = created_students[idx]
            complaint = Complaint(
                ticket_number=cmp_ticket,
                student_id=stu.id,
                category=cat,
                title=title,
                description=desc,
                priority=prio,
                status=status,
                assigned_to_employee_id=emp.id if emp else None,
                admin_response="Technician dispatched to inspect and resolve." if status in ['In Progress', 'Resolved'] else None,
                student_feedback="Great work, technician fixed the issue within 2 hours." if status == 'Resolved' else None,
                student_rating=5 if status == 'Resolved' else None,
                resolved_at=datetime.utcnow() if status == 'Resolved' else None
            )
            db.session.add(complaint)

        print("Seeding Gate Visitor Log...")
        sample_visitors = [
            ('Tariq Mehmood Malik', '35201-8899001-1', '+92 300 4455667', 1, 'Father', 'Visiting son and delivering books & semester fees', True),
            ('Sultan Ahmed Qureshi', '35202-7788991-1', '+92 301 9988776', 2, 'Uncle', 'Family visit and weekend lunch', True),
            ('Mrs. Farzana Bibi', '37405-6677881-2', '+92 321 3344556', 71, 'Mother', 'Mother visiting resident in Fatima Jinnah Girls Hostel', True),
            ('Shahid Hussain', '17301-5566771-1', '+92 333 1122334', 3, 'Brother', 'Dropping semester project supplies', False), # Currently inside
            ('Dr. Khalid Munir', '61101-4455661-1', '+92 345 5566778', 4, 'Guardian', 'Official academic guardian check-in', False), # Currently inside
        ]
        for name, cnic, phone, s_idx, rel, purp, departed in sample_visitors:
            vis = Visitor(
                visitor_name=name,
                cnic=cnic,
                phone_number=phone,
                student_id=created_students[s_idx].id,
                relation=rel,
                purpose=purp,
                check_in=datetime.utcnow() - timedelta(hours=random.randint(1, 5)),
                check_out=datetime.utcnow() if departed else None,
                security_officer='Subedar (R) Muhammad Rafiq'
            )
            db.session.add(vis)

        print("Seeding Weekly Mess Schedule...")
        mess_plan = [
            ('Monday', 'Breakfast', 'Anda Paratha, Chana Masala, Milk Tea', '7:00 AM - 9:30 AM', 'Fresh Desi Chai'),
            ('Monday', 'Lunch', 'Daal Chawal, Shami Kabab, Fresh Salad, Mint Raita', '12:30 PM - 2:30 PM', ''),
            ('Monday', 'Dinner', 'Chicken Karahi, Roti, Salad', '7:30 PM - 9:30 PM', 'Special Chef Recipe'),

            ('Tuesday', 'Breakfast', 'Bread, Butter, Jam, Omelette / Boiled Egg, Tea', '7:00 AM - 9:30 AM', ''),
            ('Tuesday', 'Lunch', 'Aloo Palak, Tandoori Roti, Pickle', '12:30 PM - 2:30 PM', ''),
            ('Tuesday', 'Dinner', 'Beef Pulao, Raita, Shami Kabab', '7:30 PM - 9:30 PM', ''),

            ('Wednesday', 'Breakfast', 'Halwa Puri, Chana, Achaar, Karak Chai', '7:00 AM - 9:30 AM', 'Wednesday Traditional Breakfast'),
            ('Wednesday', 'Lunch', 'Kadhi Pakora, Steamed Basmati Rice', '12:30 PM - 2:30 PM', ''),
            ('Wednesday', 'Dinner', 'Chicken Qorma, Naan, Salad', '7:30 PM - 9:30 PM', ''),

            ('Thursday', 'Breakfast', 'Aloo Paratha, Dahi, Tea', '7:00 AM - 9:30 AM', ''),
            ('Thursday', 'Lunch', 'Mixed Vegetable Curry, Roti, Raita', '12:30 PM - 2:30 PM', ''),
            ('Thursday', 'Dinner', 'Daal Mash Special, Chapli Kabab, Roti', '7:30 PM - 9:30 PM', ''),

            ('Friday', 'Breakfast', 'French Toast, Omelette, Tea', '7:00 AM - 9:30 AM', ''),
            ('Friday', 'Lunch', 'Special Chicken Biryani, Cold Drink, Raita, Salad', '1:30 PM - 3:00 PM', 'Special Friday Jummah Feast'),
            ('Friday', 'Dinner', 'Chicken Handi, Roghani Naan, Kheer Sweet Dish', '7:30 PM - 9:30 PM', 'Friday Special Dessert'),

            ('Saturday', 'Breakfast', 'Khagina, Paratha, Chai', '7:30 AM - 10:00 AM', 'Weekend Extended Timing'),
            ('Saturday', 'Lunch', 'Lobio Daal, Steamed Rice, Achaar', '1:00 PM - 3:00 PM', ''),
            ('Saturday', 'Dinner', 'Chicken Manchurian, Egg Fried Rice', '7:30 PM - 9:30 PM', 'Chinese Cuisine Night'),

            ('Sunday', 'Breakfast', 'Special Nihari, Naan, Tea', '8:00 AM - 10:30 AM', 'Sunday Special Nihari'),
            ('Sunday', 'Lunch', 'Aloo Keema, Roti, Fresh Salad', '1:00 PM - 3:00 PM', ''),
            ('Sunday', 'Dinner', 'Chicken Tikka Boti, Paratha, Green Chutney', '8:00 PM - 10:00 PM', 'Sunday BBQ Night')
        ]
        for day, meal, items, timing, note in mess_plan:
            mm = MessMenu(
                day_of_week=day,
                meal_type=meal,
                menu_items=items,
                timing=timing,
                special_note=note
            )
            db.session.add(mm)

        print("Seeding Institutional Announcements...")
        announcements_data = [
            ('Official Hostel Curfew & Gate Timing Notice', 'All residents are strictly reminded that main hostel gates close at 10:00 PM sharp. Any arrival after curfew requires warden approval and entry log recording.', 'All', 'Important', 'Prof. Tariq Mehmood (Chief Warden)'),
            ('Hostel & Mess Fee Deadline - November 2026', 'Monthly hostel accommodation and mess invoices for November have been issued. Residents must deposit dues before the 15th to avoid late payment fines.', 'Students', 'Urgent', 'Bilal Ahmad FCA (Accountant)'),
            ('Scheduled Backup Generator Maintenance', 'Backup power generators in Allama Iqbal and Fatima Jinnah hostels will undergo routine servicing on Saturday from 2:00 PM to 4:00 PM.', 'All', 'Normal', 'Hostel Administration'),
            ('Mess Committee Monthly Resident Review Meeting', 'The monthly mess review meeting will be held in the Central Common Room on Wednesday at 5:00 PM. Representatives from all wings are invited to discuss food quality.', 'Students', 'Normal', 'Mess Committee')
        ]
        for title, content, aud, prio, author in announcements_data:
            ann = Announcement(
                title=title,
                content=content,
                target_audience=aud,
                priority=prio,
                author_name=author,
                is_active=True
            )
            db.session.add(ann)

        print("Committing all database transactions...")
        db.session.commit()
        print("\n==================================================================")
        print("SUCCESS: Pakistani realistic fictional sample dataset created!")
        print("Super Admin: superadmin@hostel.edu.pk / Admin@12345")
        print("Hostel Admin: admin.iqbal@hostel.edu.pk / HostelAdmin@123")
        print("Warden: warden.tariq@hostel.edu.pk / Warden@123")
        print("Accountant: accountant.bilal@hostel.edu.pk / Accountant@123")
        print("Student (Sample 001): hms_2026_001 / Student@12345")
        print("Staff Guard: emp_guard_01 / Staff@12345")
        print("==================================================================")

if __name__ == '__main__':
    seed_database()
