import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory, abort
from flask_login import login_required, current_user
from app.models.base import db
from app.models.student import Student, Guardian, Document
from app.models.user import User, Role
from app.forms.student import StudentForm, DocumentUploadForm
from app.services.auth_service import role_required, log_audit

students_bp = Blueprint('students', __name__, url_prefix='/students')

@students_bp.route('/')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Accountant')
def list_students():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    gender_filter = request.args.get('gender', '').strip()
    dept_filter = request.args.get('dept', '').strip()

    query = Student.query

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Student.full_name.ilike(search_pattern)) |
            (Student.student_id_code.ilike(search_pattern)) |
            (Student.cnic.ilike(search_pattern)) |
            (Student.email.ilike(search_pattern)) |
            (Student.phone_number.ilike(search_pattern))
        )

    if status_filter:
        query = query.filter_by(status=status_filter)

    if gender_filter:
        query = query.filter_by(gender=gender_filter)

    if dept_filter:
        query = query.filter(Student.department.ilike(f"%{dept_filter}%"))

    students_pagination = query.order_by(Student.admission_date.desc(), Student.id.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )

    # Distinct departments for filter dropdown
    departments = db.session.query(Student.department).distinct().all()
    departments = [d[0] for d in departments if d[0]]

    return render_template(
        'students/list.html',
        pagination=students_pagination,
        students=students_pagination.items,
        search=search,
        status_filter=status_filter,
        gender_filter=gender_filter,
        dept_filter=dept_filter,
        departments=departments
    )


@students_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def add_student():
    form = StudentForm()
    if form.validate_on_submit():
        # Check unique constraints
        if Student.query.filter_by(student_id_code=form.student_id_code.data.strip()).first():
            flash('A student with this Student ID already exists.', 'danger')
            return render_template('students/add_edit.html', form=form, title='Enroll New Student')

        if Student.query.filter_by(cnic=form.cnic.data.strip()).first():
            flash('A student with this CNIC already exists.', 'danger')
            return render_template('students/add_edit.html', form=form, title='Enroll New Student')

        if Student.query.filter_by(email=form.email.data.strip().lower()).first():
            flash('A student with this Email already exists.', 'danger')
            return render_template('students/add_edit.html', form=form, title='Enroll New Student')

        # Handle profile photo upload
        profile_filename = 'default_student.png'
        if form.profile_picture.data:
            file = form.profile_picture.data
            fname = secure_filename(file.filename)
            ext = fname.rsplit('.', 1)[1].lower() if '.' in fname else 'png'
            profile_filename = f"stu_{form.student_id_code.data}_{int(datetime.utcnow().timestamp())}.{ext}"
            dest_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles')
            os.makedirs(dest_dir, exist_ok=True)
            file.save(os.path.join(dest_dir, profile_filename))

        # Create user account for student self-service portal
        student_role = Role.query.filter_by(name='Student').first()
        student_user = None
        if student_role:
            # Generate student username
            clean_username = form.student_id_code.data.strip().replace('-', '_').lower()
            if not User.query.filter_by(username=clean_username).first():
                student_user = User(
                    username=clean_username,
                    email=form.email.data.strip().lower(),
                    full_name=form.full_name.data.strip(),
                    role_id=student_role.id,
                    is_active=True
                )
                student_user.set_password('Student@12345') # default first login password
                db.session.add(student_user)
                db.session.flush()

        # Create Student record
        student = Student(
            user_id=student_user.id if student_user else None,
            student_id_code=form.student_id_code.data.strip().upper(),
            full_name=form.full_name.data.strip(),
            father_name=form.father_name.data.strip(),
            cnic=form.cnic.data.strip(),
            email=form.email.data.strip().lower(),
            phone_number=form.phone_number.data.strip(),
            emergency_contact=form.emergency_contact.data.strip(),
            gender=form.gender.data,
            date_of_birth=form.date_of_birth.data,
            address=form.address.data.strip(),
            city=form.city.data.strip(),
            university_name=form.university_name.data.strip(),
            department=form.department.data.strip(),
            degree_program=form.degree_program.data.strip(),
            semester=form.semester.data,
            admission_date=form.admission_date.data,
            profile_picture=profile_filename,
            status=form.status.data
        )
        db.session.add(student)
        db.session.flush()

        # Create Guardian record
        guardian = Guardian(
            student_id=student.id,
            name=form.guardian_name.data.strip(),
            relationship=form.guardian_relation.data,
            phone_number=form.guardian_phone.data.strip(),
            cnic=form.guardian_cnic.data.strip() if form.guardian_cnic.data else None,
            occupation=form.guardian_occupation.data.strip() if form.guardian_occupation.data else None,
            address=form.guardian_address.data.strip() if form.guardian_address.data else form.address.data.strip()
        )
        db.session.add(guardian)

        db.session.commit()
        log_audit('CREATE_STUDENT', 'Student', student.id, f"Enrolled student {student.full_name} ({student.student_id_code})")
        flash(f"Student {student.full_name} successfully enrolled! Portal login created: {clean_username} (Default pass: Student@12345)", 'success')
        return redirect(url_for('students.view_student', student_id=student.id))

    return render_template('students/add_edit.html', form=form, title='Enroll New Student')


@students_bp.route('/<int:student_id>')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden', 'Accountant')
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    doc_form = DocumentUploadForm()
    return render_template('students/view.html', student=student, doc_form=doc_form)


@students_bp.route('/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    form = StudentForm(obj=student)
    guardian = student.primary_guardian

    if request.method == 'GET' and guardian:
        form.guardian_name.data = guardian.name
        form.guardian_relation.data = guardian.relationship
        form.guardian_phone.data = guardian.phone_number
        form.guardian_cnic.data = guardian.cnic
        form.guardian_occupation.data = guardian.occupation
        form.guardian_address.data = guardian.address

    if form.validate_on_submit():
        # Check duplicate CNIC / Email on other students
        existing_cnic = Student.query.filter(Student.cnic == form.cnic.data.strip(), Student.id != student.id).first()
        if existing_cnic:
            flash('Another student already has this CNIC.', 'danger')
            return render_template('students/add_edit.html', form=form, title='Edit Student Profile', student=student)

        existing_email = Student.query.filter(Student.email == form.email.data.strip().lower(), Student.id != student.id).first()
        if existing_email:
            flash('Another student already has this Email.', 'danger')
            return render_template('students/add_edit.html', form=form, title='Edit Student Profile', student=student)

        # Handle profile photo upload if provided
        if form.profile_picture.data:
            file = form.profile_picture.data
            fname = secure_filename(file.filename)
            ext = fname.rsplit('.', 1)[1].lower() if '.' in fname else 'png'
            profile_filename = f"stu_{student.student_id_code}_{int(datetime.utcnow().timestamp())}.{ext}"
            dest_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles')
            os.makedirs(dest_dir, exist_ok=True)
            file.save(os.path.join(dest_dir, profile_filename))
            student.profile_picture = profile_filename

        student.full_name = form.full_name.data.strip()
        student.father_name = form.father_name.data.strip()
        student.cnic = form.cnic.data.strip()
        student.email = form.email.data.strip().lower()
        student.phone_number = form.phone_number.data.strip()
        student.emergency_contact = form.emergency_contact.data.strip()
        student.gender = form.gender.data
        student.date_of_birth = form.date_of_birth.data
        student.address = form.address.data.strip()
        student.city = form.city.data.strip()
        student.university_name = form.university_name.data.strip()
        student.department = form.department.data.strip()
        student.degree_program = form.degree_program.data.strip()
        student.semester = form.semester.data
        student.admission_date = form.admission_date.data
        student.status = form.status.data

        # Update guardian
        if guardian:
            guardian.name = form.guardian_name.data.strip()
            guardian.relationship = form.guardian_relation.data
            guardian.phone_number = form.guardian_phone.data.strip()
            guardian.cnic = form.guardian_cnic.data.strip() if form.guardian_cnic.data else None
            guardian.occupation = form.guardian_occupation.data.strip() if form.guardian_occupation.data else None
            guardian.address = form.guardian_address.data.strip() if form.guardian_address.data else form.address.data.strip()
        else:
            new_guard = Guardian(
                student_id=student.id,
                name=form.guardian_name.data.strip(),
                relationship=form.guardian_relation.data,
                phone_number=form.guardian_phone.data.strip()
            )
            db.session.add(new_guard)

        # Keep User account email and name in sync
        if student.user:
            student.user.email = student.email
            student.user.full_name = student.full_name

        db.session.commit()
        log_audit('UPDATE_STUDENT', 'Student', student.id, f"Updated profile for {student.full_name}")
        flash('Student profile updated successfully!', 'success')
        return redirect(url_for('students.view_student', student_id=student.id))

    return render_template('students/add_edit.html', form=form, title='Edit Student Profile', student=student)


@students_bp.route('/<int:student_id>/delete', methods=['POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin')
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    name = student.full_name
    student_code = student.student_id_code

    # If student has active room allocation, release the bed first
    alloc = student.current_allocation
    if alloc:
        bed = alloc.bed
        if bed:
            bed.status = 'Available'
        alloc.status = 'Checked Out'
        if alloc.room:
            alloc.room.sync_status()

    # Deactivate or delete associated user account
    if student.user:
        db.session.delete(student.user)

    db.session.delete(student)
    db.session.commit()
    log_audit('DELETE_STUDENT', 'Student', student_id, f"Deleted student {name} ({student_code})")
    flash(f"Student {name} ({student_code}) has been removed from the system.", 'info')
    return redirect(url_for('students.list_students'))


@students_bp.route('/<int:student_id>/upload-document', methods=['POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def upload_document(student_id):
    student = Student.query.get_or_404(student_id)
    form = DocumentUploadForm()
    if form.validate_on_submit():
        file = form.doc_file.data
        fname = secure_filename(file.filename)
        ext = fname.rsplit('.', 1)[1].lower() if '.' in fname else 'pdf'
        doc_filename = f"doc_{student.student_id_code}_{int(datetime.utcnow().timestamp())}.{ext}"
        dest_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
        os.makedirs(dest_dir, exist_ok=True)
        file_path = os.path.join(dest_dir, doc_filename)
        file.save(file_path)
        file_size_kb = int(os.path.getsize(file_path) / 1024)

        doc = Document(
            student_id=student.id,
            doc_title=form.doc_title.data.strip(),
            doc_type=form.doc_type.data,
            file_path=doc_filename,
            file_size_kb=file_size_kb
        )
        db.session.add(doc)
        db.session.commit()
        log_audit('UPLOAD_DOCUMENT', 'Document', doc.id, f"Uploaded document {doc.doc_title} for {student.full_name}")
        flash('Document uploaded successfully!', 'success')
    else:
        flash('Failed to upload document. Please verify the file format and try again.', 'danger')

    return redirect(url_for('students.view_student', student_id=student.id))


@students_bp.route('/documents/<int:document_id>/delete', methods=['POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Warden')
def delete_document(document_id):
    doc = Document.query.get_or_404(document_id)
    student_id = doc.student_id
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', doc.file_path)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
    db.session.delete(doc)
    db.session.commit()
    flash('Document deleted.', 'info')
    return redirect(url_for('students.view_student', student_id=student_id))
