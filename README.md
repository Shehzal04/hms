# HostelFlow HMS - Modern Enterprise Hostel Management System

A professional, full-featured, responsive, and robust **Hostel Management System (HMS)** architected for universities, colleges, and private student residencies. Built with **Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Bootstrap 5, Chart.js, and ReportLab**.

---

## 🌟 Key Features

### 1. Multi-Role Authentication & Access Control (RBAC)
- **Super Admin**: Unrestricted system administration, multi-hostel control, role management, system settings, and complete security audit trail logs.
- **Hostel Admin**: Residential operations, student admissions, room inventory, employee task dispatching, and reports.
- **Warden**: Daily roll calls, attendance tracking, curfew gate logs, student discipline, visitor clearances, and complaint management.
- **Accountant**: Fee invoices generation, partial and full payment collections, transaction receipts, outstanding balance reports, and ReportLab PDF downloads.
- **Student**: Self-service resident portal, room & bed view, roommate details, fee ledger, complaint submission with photos, satisfaction ratings, visitor records, and mess schedules.
- **Staff**: Operational checklist, assigned maintenance tickets, and status progress reporting.

### 2. Executive Operations Dashboard
- **Live Database-Driven Metrics**: Total active residents, room count, occupied vs. available beds, occupancy rate, current month fee collections, outstanding receivables, staff count, today's roll call rate, and open complaint tickets.
- **Interactive Chart.js Visualizations**:
  - Monthly fee collection trend line chart (last 6 months)
  - Bed occupancy doughnut ratio
  - Admissions distribution by academic department bar chart
  - Overall student attendance distribution pie chart
- **Live Tables**: Recent student admissions and recent fee payment vouchers with one-click receipt views.

### 3. Student Lifecycle & Profile Management
- Complete student CRUD with Pakistani CNIC/B-Form validation, emergency contacts, academic department, semester, and home address.
- Comprehensive parent/guardian details and emergency contact logs.
- Document repository supporting PDF and image uploads (matric/FSc result cards, domicile, affidavits, university ID).
- Auto-provisioning of resident portal accounts upon enrollment.

### 4. Housing & Room Inventory
- Multi-hostel support (Boys', Girls', and Co-educational facilities).
- Rooms categorization: Single, Double, Triple, and Four-Seater rooms.
- Visual bed grid indicator showing **Available (Green)**, **Occupied (Red)**, and **Maintenance (Yellow)** statuses.
- Automatic room capacity sync preventing over-allocation.

### 5. Room Allocation System
- Bed-level precision allocation with check-in and expected check-out dates.
- Dynamic AJAX bed dropdowns ensuring only vacant beds can be selected.
- Formal room transfer workflow with audit history logging.
- Bed release clearance upon student departure or graduation.

### 6. Finance & Invoicing Engine
- Customizable fee types: Admission Fee, Monthly Hostel Fee, Security Deposit, Mess Charges, and Utility Surcharges.
- Invoices generation with due dates and late surcharge calculations.
- Multi-channel payment recording (Cash, Bank Transfer, 1Link, Raast, Online Portal).
- Official printable fee receipts and **ReportLab downloadable PDF vouchers**.

### 7. Attendance & Curfew Monitoring
- Interactive daily roll call interface with single-click "Mark All Present" functionality.
- Present, Absent, and Permitted Leave tracking.
- Gate late entry log for curfew monitoring and arrival delay recording.
- Individual and institutional attendance percentage calculations.

### 8. Complaint Ticketing & Service Dispatch
- Category-based complaints: Electricity, Plumbing, Internet/WiFi, Carpentry, Cleaning, Mess, Security.
- Image attachment uploads for maintenance inspection.
- Administrative workflow: Pending &rarr; In Progress (Assigned Staff) &rarr; Resolved &rarr; Rejected.
- Student post-resolution satisfaction feedback and 1-to-5 star ratings.

### 9. Visitor Management
- Gate visitor registration with visitor CNIC verification, contact details, student visited, and relationship.
- Real-time indicator of guests currently inside the building.
- Official departure check-out recording.

### 10. Weekly Mess Management
- 7-day breakfast, lunch, and dinner schedule matrix with timings and chef notes.
- Quick editor for daily menus.
- Mess subscription meal packages.

### 11. Staff Management & Payroll
- Employee directory covering Wardens, Security Guards, Cleaners, Electricians, Maintenance Staff, and Chefs.
- Shift assignments and salary records.
- Duty and task assignment board with progress tracking.

### 12. Institutional Reports & Analytics Hub
- **Admissions Report**: Demographic and faculty breakdown.
- **Occupancy Report**: Building, floor, room, and bed metrics.
- **Available Vacancies Report**: Filterable open beds.
- **Fee Collection Report**: Financial ledgers and transaction slip numbers.
- **Outstanding Dues Report**: Balances due and overdue invoices.
- **Attendance Summary Report**: Student roll call records.
- **Complaints & Visitors Reports**: Institutional service audits.
- **One-click Exporting**: Native UTF-8 CSV exports and ReportLab PDF reports.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.13, Flask 3.1.2 |
| **ORM & Database** | Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0, SQLite (Dev) / MySQL (Primary Production) |
| **Authentication** | Flask-Login 0.6.3, Werkzeug Security (PBKDF2/SHA256 password hashing) |
| **Forms & Security** | Flask-WTF 1.3.0, WTForms 3.3.1, CSRF Protection |
| **PDF Engine** | ReportLab 4.5.1 (High-resolution official receipts & reports) |
| **Frontend** | HTML5, CSS3, Bootstrap 5.3.3, Bootstrap Icons 1.11, Chart.js 4.4 |
| **Architecture** | MVC Architecture, 16 Modular Flask Blueprints, Services Layer |

---

## 📂 Project Structure

```
hostel_management/
│
├── app/
│   ├── __init__.py                # App factory, extensions, blueprints, context processors
│   ├── config.py                  # Environment and database configuration
│   ├── models/                    # Normalized Relational Database Models
│   │   ├── __init__.py
│   │   ├── base.py                # db instance & TimestampMixin
│   │   ├── user.py                # User, Role models
│   │   ├── hostel.py              # Hostel, Room, Bed, RoomAllocation, RoomTransferHistory
│   │   ├── student.py             # Student, Guardian, Document models
│   │   ├── finance.py             # FeeType, FeeInvoice, FeeInvoiceItem, Payment
│   │   ├── attendance.py          # StudentAttendance, LateEntry models
│   │   ├── complaint.py           # Complaint, ComplaintUpdate models
│   │   ├── visitor.py             # Visitor model
│   │   ├── mess.py                # MessMenu, MessSubscription models
│   │   ├── staff.py               # Employee, EmployeeAttendance, EmployeeSalary, Task
│   │   ├── communication.py       # Announcement, Notification models
│   │   └── system.py              # AuditLog, HostelSetting models
│   │
│   ├── routes/                    # Modular Flask Blueprints
│   │   ├── auth.py                # Authentication, login, logout, password change
│   │   ├── dashboard.py           # Executive dashboard & Chart.js JSON endpoints
│   │   ├── students.py            # Student directory, CRUD, profile view, documents
│   │   ├── hostels.py             # Hostels management & floor matrix
│   │   ├── rooms.py               # Rooms, beds inventory, and status toggles
│   │   ├── allocations.py         # Room allocations, transfers, checkouts, dynamic beds API
│   │   ├── fees.py                # Invoices, payments, receipts, PDF downloads
│   │   ├── attendance.py          # Daily roll call, bulk attendance, late entry log
│   │   ├── complaints.py          # Complaint tickets, staff dispatch, student ratings
│   │   ├── visitors.py            # Gate visitor registrations and checkouts
│   │   ├── mess.py                # Weekly meal matrix & subscriptions
│   │   ├── staff.py               # Employee records & duty assignments
│   │   ├── announcements.py       # Public notices & in-app notifications
│   │   ├── reports.py             # Reports hub with CSV & PDF export
│   │   ├── settings.py            # System parameters, RBAC user admin, audit trail
│   │   └── student_portal.py      # Resident self-service portal
│   │
│   ├── forms/                     # Flask-WTF Forms & Input Validators
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── student.py
│   │   ├── hostel.py
│   │   └── operations.py
│   │
│   ├── services/                  # Business Logic Layer
│   │   ├── auth_service.py        # RBAC decorator, audit logging, notifications
│   │   ├── allocation_service.py  # Bed allocation, transfer & checkout validation
│   │   ├── finance_service.py     # Invoicing, payments & balance calculations
│   │   └── reporting_service.py   # CSV generator & ReportLab PDF builder
│   │
│   ├── static/                    # Assets
│   │   ├── css/style.css          # Premium SaaS theme styling & print media queries
│   │   ├── js/main.js             # Sidebar toggles, dynamic bed AJAX, Chart.js loaders
│   │   └── uploads/               # Upload directories (profiles, documents, complaints)
│   │
│   └── templates/                 # Jinja2 SaaS Templates (50+ templates)
│       ├── base.html              # Core SaaS responsive shell with notification bell
│       ├── auth/
│       ├── dashboard/
│       ├── students/
│       ├── hostels/
│       ├── rooms/
│       ├── allocations/
│       ├── fees/
│       ├── attendance/
│       ├── complaints/
│       ├── visitors/
│       ├── mess/
│       ├── staff/
│       ├── announcements/
│       ├── reports/
│       ├── settings/
│       ├── student_portal/
│       └── errors/
│
├── config.py                      # Root configuration loader
├── run.py                         # Application entrypoint
├── seed.py                        # Realistic Pakistani fictional sample data seeder
├── test_app.py                    # Comprehensive 10-point automated test suite
├── requirements.txt               # Production dependencies
├── .env.example                   # Environment configuration template
└── README.md                      # Full documentation
```

---

## 🚀 Quick Start & Installation

### Step 1: Open the Project Directory
```powershell
cd C:\Users\HAK3\.gemini\antigravity\scratch\hostel_management
```

### Step 2: Install Dependencies (if not already present)
```powershell
pip install -r requirements.txt
```

### Step 3: Seed the Database with Realistic Pakistani Sample Data
```powershell
python seed.py
```
*This populates the database with 1 Super Admin, 2 Hostel Admins, 3 Wardens, 2 Accountants, 10 Staff Members, 3 Hostels, 30 Rooms, 74+ Beds, 100 Pakistani Students, 70 Active Room Allocations, 100 Fee Invoices, 67 Payments, Attendance records, Complaints, Visitors, and Weekly Mess Menus.*

### Step 4: Run the Application
```powershell
python run.py
```
Open your browser and navigate to:
**http://127.0.0.1:5000**

---

## 🔑 Default Login Credentials

| Role | Email / Username | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `superadmin@hostel.edu.pk` | `Admin@12345` | Complete system access, settings, RBAC, all hostels |
| **Hostel Admin** | `admin.iqbal@hostel.edu.pk` | `HostelAdmin@123` | Hostel buildings, student admissions, rooms, employees |
| **Warden** | `warden.tariq@hostel.edu.pk` | `Warden@123` | Attendance roll calls, curfew logs, complaints, visitors |
| **Accountant** | `accountant.bilal@hostel.edu.pk` | `Accountant@123` | Invoicing, payments collection, receipts, finance reports |
| **Student** | `hms_2026_001` | `Student@12345` | Personal portal, allocated room, fees, submit complaints |
| **Staff Guard** | `emp_guard_01` | `Staff@12345` | Assigned maintenance tasks, security gate records |

> **Tip**: The login page includes quick-click demo credential pills to sign into any role with a single click.

---

## 🗄️ Database Setup (SQLite & MySQL)

### Development (SQLite) - Default
Out of the box, `DATABASE_URL=sqlite:///hms.db` in `.env` is ready with zero additional database server setup needed.

### Production (MySQL)
To switch to MySQL:
1. Create a database in MySQL:
   ```sql
   CREATE DATABASE hostel_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. Update `.env`:
   ```env
   DATABASE_URL=mysql+pymysql://root:your_mysql_password@localhost:3306/hostel_db?charset=utf8mb4
   ```
3. Run the database seed script:
   ```powershell
   python seed.py
   ```

---

## 🧪 Automated Test Suite

A complete 10-point test suite is included in `test_app.py`. To execute:
```powershell
python test_app.py
```
**Test Coverage Includes:**
1. Authentication across multiple roles and session tracking.
2. Executive dashboard database-driven KPIs and Chart.js JSON API responses.
3. Student management CRUD and profile view rendering.
4. Hostel building and room inventory management.
5. Bed-level allocation and dynamic available bed query API.
6. Fee invoicing, payment balance updates, and ReportLab PDF receipt generation.
7. Reports Hub filtering, CSV export with UTF-8 BOM, and PDF generation.
8. Role-based authorization enforcement (HTTP 403 Forbidden checks).
9. Allocation constraints preventing over-allocation and duplicate active resident allocations.
10. Financial ledger payment updates and balance calculation verification.

---

## 📄 License
Designed and engineered for educational institutions and commercial hostel management enterprises.
