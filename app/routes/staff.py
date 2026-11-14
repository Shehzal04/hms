from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.staff import Employee, Task, EmployeeAttendance, EmployeeSalary
from app.models.complaint import Complaint
from app.models.user import User, Role
from app.forms.operations import EmployeeForm, TaskForm, TaskUpdateForm
from app.services.auth_service import role_required, log_audit

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

@staff_bp.route('/')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Accountant')
def list_employees():
    page = request.args.get('page', 1, type=int)
    designation = request.args.get('designation', '').strip()
    status_filter = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()

    query = Employee.query
    if designation:
        query = query.filter_by(designation=designation)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Employee.full_name.ilike(search_pattern)) |
            (Employee.employee_code.ilike(search_pattern)) |
            (Employee.cnic.ilike(search_pattern)) |
            (Employee.phone_number.ilike(search_pattern))
        )

    pagination = query.order_by(Employee.joining_date.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )

    designations = [
        'Warden', 'Accountant', 'Security Guard', 'Cleaner',
        'Electrician', 'Maintenance Staff', 'Mess Staff'
    ]

    return render_template(
        'staff/list.html',
        pagination=pagination,
        employees=pagination.items,
        designations=designations,
        selected_designation=designation,
        selected_status=status_filter,
        search=search
    )


@staff_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin')
def add_employee():
    form = EmployeeForm()
    if request.method == 'GET':
        form.joining_date.data = date.today()

    if form.validate_on_submit():
        if Employee.query.filter_by(employee_code=form.employee_code.data.strip()).first():
            flash('Employee code already exists.', 'danger')
            return render_template('staff/add_edit.html', form=form, title='Add New Staff Member')

        if Employee.query.filter_by(cnic=form.cnic.data.strip()).first():
            flash('An employee with this CNIC already exists.', 'danger')
            return render_template('staff/add_edit.html', form=form, title='Add New Staff Member')

        emp_user = None
        if form.create_user_account.data:
            role_name = 'Staff'
            if form.designation.data == 'Warden':
                role_name = 'Warden'
            elif form.designation.data == 'Accountant':
                role_name = 'Accountant'

            role_obj = Role.query.filter_by(name=role_name).first()
            if role_obj:
                username = form.employee_code.data.strip().lower().replace('-', '_')
                emp_user = User(
                    username=username,
                    email=form.email.data.strip() if form.email.data else f"{username}@hostel.local",
                    full_name=form.full_name.data.strip(),
                    role_id=role_obj.id,
                    is_active=True
                )
                emp_user.set_password(form.user_password.data.strip() or 'Staff@12345')
                db.session.add(emp_user)
                db.session.flush()

        emp = Employee(
            user_id=emp_user.id if emp_user else None,
            employee_code=form.employee_code.data.strip().upper(),
            full_name=form.full_name.data.strip(),
            designation=form.designation.data,
            cnic=form.cnic.data.strip(),
            phone_number=form.phone_number.data.strip(),
            email=form.email.data.strip() if form.email.data else None,
            address=form.address.data.strip(),
            joining_date=form.joining_date.data,
            salary=form.salary.data,
            duty_shift=form.duty_shift.data,
            status=form.status.data
        )
        db.session.add(emp)
        db.session.commit()
        log_audit('CREATE_EMPLOYEE', 'Employee', emp.id, f"Added employee {emp.full_name} ({emp.employee_code})")
        flash(f"Staff member {emp.full_name} ({emp.employee_code}) added successfully!", 'success')
        return redirect(url_for('staff.view_employee', employee_id=emp.id))

    return render_template('staff/add_edit.html', form=form, title='Add New Staff Member')


@staff_bp.route('/<int:employee_id>')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Accountant')
def view_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    tasks = employee.tasks.order_by(Task.created_at.desc()).all()
    task_form = TaskForm()
    task_form.employee_id.choices = [(employee.id, employee.full_name)]
    return render_template('staff/view.html', employee=employee, tasks=tasks, task_form=task_form)


@staff_bp.route('/tasks/assign', methods=['POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def assign_task():
    form = TaskForm()
    employees = Employee.query.filter_by(status='Active').all()
    form.employee_id.choices = [(e.id, e.full_name) for e in employees]

    if form.validate_on_submit():
        task = Task(
            employee_id=form.employee_id.data,
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            priority=form.priority.data,
            due_date=form.due_date.data,
            assigned_by=current_user.full_name
        )
        db.session.add(task)
        db.session.commit()
        log_audit('ASSIGN_TASK', 'Task', task.id, f"Assigned task '{task.title}' to Employee ID {task.employee_id}")
        flash('Task assigned successfully!', 'success')
        return redirect(url_for('staff.view_employee', employee_id=form.employee_id.data))

    flash('Failed to assign task. Please fill in all required fields.', 'danger')
    return redirect(url_for('staff.list_employees'))


@staff_bp.route('/my-duties', methods=['GET', 'POST'])
@login_required
def my_duties():
    # Staff portal dashboard
    if not current_user.is_staff and not current_user.is_warden:
        return redirect(url_for('dashboard.index'))

    emp = current_user.employee_profile
    if not emp:
        flash("No employee record linked with this user account.", "warning")
        return redirect(url_for('dashboard.index'))

    tasks = emp.tasks.order_by(Task.status.desc(), Task.created_at.desc()).all()
    assigned_complaints = emp.assigned_complaints.order_by(Complaint.created_at.desc()).all()

    return render_template(
        'staff/my_duties.html',
        employee=emp,
        tasks=tasks,
        complaints=assigned_complaints
    )


@staff_bp.route('/tasks/<int:task_id>/update', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    new_status = request.form.get('status')
    notes = request.form.get('completion_notes', '').strip()

    if new_status in ['Pending', 'In Progress', 'Completed']:
        task.status = new_status
        if notes:
            task.completion_notes = notes
        db.session.commit()
        flash(f"Task '{task.title}' updated to {new_status}.", 'success')

    if current_user.is_staff:
        return redirect(url_for('staff.my_duties'))
    return redirect(url_for('staff.view_employee', employee_id=task.employee_id))
