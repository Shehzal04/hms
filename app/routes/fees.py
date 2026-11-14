from datetime import date, timedelta
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, Response, send_file
from flask_login import login_required, current_user
from app.models.base import db
from app.models.student import Student
from app.models.finance import FeeType, FeeInvoice, FeeInvoiceItem, Payment
from app.forms.operations import InvoiceForm, PaymentForm
from app.services.finance_service import create_student_invoice, record_invoice_payment
from app.services.reporting_service import generate_pdf_receipt_buffer
from app.services.auth_service import role_required, log_audit, send_notification

fees_bp = Blueprint('fees', __name__, url_prefix='/fees')

@fees_bp.route('/')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Accountant', 'Warden')
def list_invoices():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()

    # Recalculate any overdue invoices
    today = date.today()
    overdue_invoices = FeeInvoice.query.filter(
        FeeInvoice.status.in_(['Unpaid', 'Partial']),
        FeeInvoice.due_date < today
    ).all()
    for inv in overdue_invoices:
        inv.status = 'Overdue'
    if overdue_invoices:
        db.session.commit()

    query = FeeInvoice.query.join(Student)

    if status_filter:
        query = query.filter(FeeInvoice.status == status_filter)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (FeeInvoice.invoice_number.ilike(search_pattern)) |
            (Student.full_name.ilike(search_pattern)) |
            (Student.student_id_code.ilike(search_pattern))
        )

    pagination = query.order_by(FeeInvoice.issue_date.desc(), FeeInvoice.id.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )

    # High-level fee metrics
    total_invoiced = sum(inv.total_amount for inv in FeeInvoice.query.all())
    total_collected = sum(p.amount for p in Payment.query.all())
    total_pending = max(0.0, float(total_invoiced) - float(total_collected))

    return render_template(
        'fees/invoices.html',
        pagination=pagination,
        invoices=pagination.items,
        status_filter=status_filter,
        search=search,
        total_invoiced=float(total_invoiced),
        total_collected=float(total_collected),
        total_pending=total_pending
    )


@fees_bp.route('/create-invoice', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Accountant')
def create_invoice():
    form = InvoiceForm()
    students = Student.query.filter_by(status='Active').order_by(Student.full_name.asc()).all()
    fee_types = FeeType.query.all()

    form.student_id.choices = [(s.id, f"{s.student_id_code} - {s.full_name}") for s in students]
    form.fee_type_id.choices = [(ft.id, f"{ft.name} (Default: Rs. {ft.default_amount:,.0f})") for ft in fee_types]

    preset_student_id = request.args.get('student_id', type=int)
    if request.method == 'GET':
        form.issue_date.data = date.today()
        form.due_date.data = date.today() + timedelta(days=10)
        if preset_student_id:
            form.student_id.data = preset_student_id
            form.title.data = f"Monthly Hostel Fee - {date.today().strftime('%B %Y')}"

    if form.validate_on_submit():
        try:
            items = [{
                'fee_type_id': form.fee_type_id.data,
                'description': form.title.data.strip(),
                'amount': form.amount.data
            }]
            invoice = create_student_invoice(
                student_id=form.student_id.data,
                title=form.title.data.strip(),
                issue_date=form.issue_date.data,
                due_date=form.due_date.data,
                items=items,
                notes=form.notes.data
            )
            log_audit('CREATE_INVOICE', 'FeeInvoice', invoice.id, f"Created Invoice {invoice.invoice_number} for Rs. {invoice.total_amount}")
            if invoice.student.user_id:
                send_notification(
                    user_id=invoice.student.user_id,
                    title="New Fee Invoice Issued",
                    message=f"Invoice {invoice.invoice_number} for Rs. {invoice.total_amount:,.0f} has been issued. Due: {invoice.due_date.strftime('%d-%b-%Y')}.",
                    link=f"/portal/my-fees"
                )
            flash(f"Invoice {invoice.invoice_number} generated successfully!", 'success')
            return redirect(url_for('fees.view_invoice', invoice_id=invoice.id))
        except Exception as e:
            flash(f"Error creating invoice: {str(e)}", 'danger')

    return render_template('fees/create_invoice.html', form=form)


@fees_bp.route('/<int:invoice_id>')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Accountant', 'Warden')
def view_invoice(invoice_id):
    invoice = FeeInvoice.query.get_or_404(invoice_id)
    payments = invoice.payments.order_by(Payment.payment_date.desc()).all()
    return render_template('fees/view_invoice.html', invoice=invoice, payments=payments)


@fees_bp.route('/record-payment', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Accountant')
def record_payment():
    form = PaymentForm()
    # Unpaid or partial invoices
    pending_invoices = FeeInvoice.query.filter(FeeInvoice.status.in_(['Unpaid', 'Partial', 'Overdue'])).order_by(FeeInvoice.due_date.asc()).all()
    form.invoice_id.choices = [
        (inv.id, f"{inv.invoice_number} - {inv.student.full_name} (Bal: Rs. {inv.balance_due:,.0f})")
        for inv in pending_invoices
    ]

    preset_invoice_id = request.args.get('invoice_id', type=int)
    if request.method == 'GET':
        form.payment_date.data = date.today()
        if preset_invoice_id:
            inv = FeeInvoice.query.get(preset_invoice_id)
            if inv:
                form.invoice_id.data = inv.id
                form.amount.data = inv.balance_due

    if form.validate_on_submit():
        try:
            payment = record_invoice_payment(
                invoice_id=form.invoice_id.data,
                amount=form.amount.data,
                payment_method=form.payment_method.data,
                transaction_id=form.transaction_id.data.strip() if form.transaction_id.data else None,
                received_by=current_user.full_name,
                remarks=form.remarks.data,
                payment_date=form.payment_date.data
            )
            log_audit('RECORD_PAYMENT', 'Payment', payment.id, f"Recorded Payment {payment.receipt_number} of Rs. {payment.amount} for {payment.student.full_name}")
            if payment.student.user_id:
                send_notification(
                    user_id=payment.student.user_id,
                    title="Payment Received",
                    message=f"Your payment of Rs. {payment.amount:,.0f} has been verified and recorded (Receipt: {payment.receipt_number}).",
                    link=f"/portal/my-fees"
                )
            flash(f"Payment recorded successfully! Receipt: {payment.receipt_number}", 'success')
            return redirect(url_for('fees.view_receipt', payment_id=payment.id))
        except ValueError as e:
            flash(str(e), 'danger')

    return render_template('fees/record_payment.html', form=form)


@fees_bp.route('/receipts/<int:payment_id>')
@login_required
def view_receipt(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    # Check authorization: Admin/Accountant or the specific student
    if current_user.is_student and payment.student.user_id != current_user.id:
        flash("You are not authorized to view this receipt.", "danger")
        return redirect(url_for('student_portal.dashboard'))

    return render_template('fees/receipt.html', payment=payment)


@fees_bp.route('/receipts/<int:payment_id>/pdf')
@login_required
def download_receipt_pdf(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    if current_user.is_student and payment.student.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for('student_portal.dashboard'))

    pdf_buffer = generate_pdf_receipt_buffer(payment)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Receipt_{payment.receipt_number}.pdf",
        mimetype='application/pdf'
    )


@fees_bp.route('/payments')
@login_required
@role_required('Super Admin', 'Hostel Admin', 'Accountant', 'Warden')
def list_payments():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()

    query = Payment.query.join(Student)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Payment.receipt_number.ilike(search_pattern)) |
            (Student.full_name.ilike(search_pattern)) |
            (Payment.transaction_id.ilike(search_pattern))
        )

    pagination = query.order_by(Payment.payment_date.desc(), Payment.id.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )
    return render_template('fees/payments_list.html', pagination=pagination, payments=pagination.items, search=search)
