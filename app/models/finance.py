from datetime import date, datetime
from app.models.base import db, TimestampMixin

class FeeType(TimestampMixin, db.Model):
    __tablename__ = 'fee_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    default_amount = db.Column(db.Numeric(10, 2), default=0.00)

    items = db.relationship('FeeInvoiceItem', back_populates='fee_type', lazy='dynamic')

    def __repr__(self):
        return f'<FeeType {self.name}>'


class FeeInvoice(TimestampMixin, db.Model):
    __tablename__ = 'fee_invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)  # e.g., 'Hostel & Mess Fee - November 2026'
    issue_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    paid_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    late_fine = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    status = db.Column(db.String(20), nullable=False, default='Unpaid')  # Unpaid, Partial, Paid, Overdue
    notes = db.Column(db.Text)

    student = db.relationship('Student', back_populates='fee_invoices')
    items = db.relationship('FeeInvoiceItem', back_populates='invoice', cascade='all, delete-orphan', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='invoice', cascade='all, delete-orphan', lazy='dynamic')

    @property
    def grand_total(self):
        return float(self.total_amount) + float(self.late_fine)

    @property
    def balance_due(self):
        bal = self.grand_total - float(self.paid_amount)
        return max(0.0, round(bal, 2))

    @property
    def is_overdue(self):
        return self.status != 'Paid' and date.today() > self.due_date

    def recalculate_status(self):
        """Update invoice status based on paid amounts and due dates."""
        paid = float(self.paid_amount)
        total = self.grand_total
        if paid >= total and total > 0:
            self.status = 'Paid'
        elif paid > 0:
            self.status = 'Partial'
        elif date.today() > self.due_date:
            self.status = 'Overdue'
        else:
            self.status = 'Unpaid'

    def __repr__(self):
        return f'<Invoice {self.invoice_number} ({self.status})>'


class FeeInvoiceItem(TimestampMixin, db.Model):
    __tablename__ = 'fee_invoice_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('fee_invoices.id'), nullable=False)
    fee_type_id = db.Column(db.Integer, db.ForeignKey('fee_types.id'), nullable=False)
    description = db.Column(db.String(255))
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)

    invoice = db.relationship('FeeInvoice', back_populates='items')
    fee_type = db.relationship('FeeType', back_populates='items')

    def __repr__(self):
        return f'<InvoiceItem {self.description}: {self.amount}>'


class Payment(TimestampMixin, db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('fee_invoices.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False, default='Cash')  # Cash, Bank Transfer, Online Payment
    transaction_id = db.Column(db.String(100))
    received_by = db.Column(db.String(100), default='Accountant')
    status = db.Column(db.String(20), default='Completed')  # Completed, Pending Verification, Cancelled
    remarks = db.Column(db.Text)

    invoice = db.relationship('FeeInvoice', back_populates='payments')
    student = db.relationship('Student', back_populates='payments')

    def __repr__(self):
        return f'<Payment {self.receipt_number} Rs.{self.amount}>'
