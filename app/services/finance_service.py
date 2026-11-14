import random
from datetime import date
from decimal import Decimal
from app.models.base import db
from app.models.finance import FeeInvoice, FeeInvoiceItem, Payment, FeeType
from app.models.student import Student

def generate_invoice_number():
    year = date.today().year
    rand_part = random.randint(10000, 99999)
    return f"INV-{year}-{rand_part}"

def generate_receipt_number():
    year = date.today().year
    rand_part = random.randint(10000, 99999)
    return f"RCP-{year}-{rand_part}"

def create_student_invoice(student_id, title, due_date, items, notes=None, issue_date=None):
    """
    items: list of dicts: [{'fee_type_id': 1, 'description': 'Monthly Fee Nov', 'amount': 15000}]
    """
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Student not found.")

    invoice_number = generate_invoice_number()
    # Ensure uniqueness
    while FeeInvoice.query.filter_by(invoice_number=invoice_number).first():
        invoice_number = generate_invoice_number()

    total_amount = Decimal(0.0)
    for itm in items:
        total_amount += Decimal(str(itm.get('amount', 0)))

    invoice = FeeInvoice(
        invoice_number=invoice_number,
        student_id=student.id,
        title=title,
        issue_date=issue_date or date.today(),
        due_date=due_date,
        total_amount=total_amount,
        paid_amount=Decimal(0.0),
        status='Unpaid',
        notes=notes
    )
    db.session.add(invoice)
    db.session.flush()

    for itm in items:
        item_obj = FeeInvoiceItem(
            invoice_id=invoice.id,
            fee_type_id=itm['fee_type_id'],
            description=itm.get('description', ''),
            amount=Decimal(str(itm.get('amount', 0)))
        )
        db.session.add(item_obj)

    db.session.commit()
    return invoice


def record_invoice_payment(invoice_id, amount, payment_method='Cash', transaction_id=None, received_by='Accountant', remarks=None, payment_date=None):
    """
    Record payment against an invoice and update invoice status.
    """
    invoice = FeeInvoice.query.get(invoice_id)
    if not invoice:
        raise ValueError("Invoice not found.")

    pay_amount = Decimal(str(amount))
    if pay_amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    balance_remaining = Decimal(str(invoice.balance_due))
    if pay_amount > balance_remaining:
        raise ValueError(f"Payment amount (Rs. {pay_amount}) cannot exceed balance due (Rs. {balance_remaining}).")

    receipt_number = generate_receipt_number()
    while Payment.query.filter_by(receipt_number=receipt_number).first():
        receipt_number = generate_receipt_number()

    payment = Payment(
        receipt_number=receipt_number,
        invoice_id=invoice.id,
        student_id=invoice.student_id,
        payment_date=payment_date or date.today(),
        amount=pay_amount,
        payment_method=payment_method,
        transaction_id=transaction_id,
        received_by=received_by,
        status='Completed',
        remarks=remarks
    )
    db.session.add(payment)

    # Update invoice paid amount
    invoice.paid_amount = Decimal(str(invoice.paid_amount)) + pay_amount
    invoice.recalculate_status()

    db.session.commit()
    return payment
