import io
import csv
from datetime import datetime
from flask import Response, make_response
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_csv_response(filename, headers, rows):
    """
    Generate downloadable CSV with UTF-8 BOM for Windows Excel compatibility.
    """
    output = io.StringIO()
    # Write UTF-8 BOM
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def generate_pdf_receipt_buffer(payment):
    """
    Generate a formal Hostel Management System payment receipt PDF using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#0d6efd'),
        alignment=1, # Center
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'ReceiptSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#6c757d'),
        alignment=1,
        spaceAfter=15
    )
    bold_style = ParagraphStyle(
        'BoldText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#212529')
    )
    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#333333')
    )

    elements = []

    # Header
    elements.append(Paragraph("HOSTELFLOW MANAGEMENT SYSTEM", title_style))
    elements.append(Paragraph("Official Payment Acknowledgment & E-Receipt", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0d6efd'), spaceAfter=15))

    # Meta Table: Receipt No, Date, Student details
    student = payment.student
    invoice = payment.invoice
    room = student.current_room
    bed = student.current_bed
    hostel = student.current_hostel

    meta_data = [
        [
            Paragraph(f"<b>Receipt No:</b> {payment.receipt_number}", normal_style),
            Paragraph(f"<b>Payment Date:</b> {payment.payment_date.strftime('%d-%b-%Y')}", normal_style)
        ],
        [
            Paragraph(f"<b>Invoice Ref:</b> {invoice.invoice_number if invoice else 'N/A'}", normal_style),
            Paragraph(f"<b>Payment Method:</b> {payment.payment_method}", normal_style)
        ],
        [
            Paragraph(f"<b>Student Name:</b> {student.full_name}", normal_style),
            Paragraph(f"<b>Student ID:</b> {student.student_id_code}", normal_style)
        ],
        [
            Paragraph(f"<b>CNIC:</b> {student.cnic}", normal_style),
            Paragraph(f"<b>Hostel / Room:</b> {hostel.name if hostel else 'N/A'} - Rm {room.room_number if room else 'N/A'}", normal_style)
        ],
        [
            Paragraph(f"<b>Transaction Ref:</b> {payment.transaction_id or 'Cash Transaction'}", normal_style),
            Paragraph(f"<b>Received By:</b> {payment.received_by}", normal_style)
        ],
    ]

    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    # Invoice breakdown table
    item_rows = [
        [
            Paragraph("<b>Item / Description</b>", bold_style),
            Paragraph("<b>Invoice Total</b>", bold_style),
            Paragraph("<b>Amount Paid</b>", bold_style),
            Paragraph("<b>Balance Remaining</b>", bold_style)
        ]
    ]

    item_rows.append([
        Paragraph(invoice.title if invoice else "Hostel Fee Payment", normal_style),
        Paragraph(f"Rs. {float(invoice.total_amount if invoice else payment.amount):,.2f}", normal_style),
        Paragraph(f"Rs. {float(payment.amount):,.2f}", normal_style),
        Paragraph(f"Rs. {float(invoice.balance_due if invoice else 0.0):,.2f}", normal_style)
    ])

    items_table = Table(item_rows, colWidths=[230, 100, 110, 100])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ced4da')),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 20))

    # Total Amount Callout Box
    total_data = [
        [
            Paragraph(f"<b>PAID AMOUNT (PKR):</b> Rs. {float(payment.amount):,.2f}", ParagraphStyle(
                'AmountPaid', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#198754')
            ))
        ]
    ]
    total_table = Table(total_data, colWidths=[540])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#d1e7dd')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#badbcc')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 30))

    # Signature & Footer
    sign_data = [
        [
            Paragraph("____________________________<br/>Student Signature", normal_style),
            Paragraph("____________________________<br/>Accounts Officer / Authorized Stamp", normal_style)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[270, 270])
    sign_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
    ]))
    elements.append(sign_table)
    elements.append(Spacer(1, 15))

    elements.append(Paragraph(
        "<i>* This is a computer-generated official receipt issued by the Hostel Management System. "
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.</i>",
        ParagraphStyle('Footer', parent=styles['Italic'], fontSize=8, textColor=colors.HexColor('#888888'), alignment=1)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_pdf_report_buffer(title, headers, rows, subtitle=None):
    """
    Generate general administrative PDF reports with tabular layout.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'RepTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0d6efd'), alignment=1, spaceAfter=4
    )
    sub_style = ParagraphStyle(
        'RepSub', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#6c757d'), alignment=1, spaceAfter=12
    )
    th_style = ParagraphStyle('TH', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=colors.white)
    td_style = ParagraphStyle('TD', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor('#212529'))

    elements = []
    elements.append(Paragraph("HOSTEL MANAGEMENT SYSTEM", title_style))
    elements.append(Paragraph(f"<b>{title.upper()}</b>" + (f" | {subtitle}" if subtitle else f" | Generated: {datetime.now().strftime('%d-%b-%Y')}"), sub_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0d6efd'), spaceAfter=10))

    # Build table
    table_data = []
    # Header row
    th_row = [Paragraph(f"<b>{h}</b>", th_style) for h in headers]
    table_data.append(th_row)

    # Content rows
    for r in rows:
        td_row = [Paragraph(str(cell), td_style) for cell in r]
        table_data.append(td_row)

    # Dynamic column widths based on number of columns
    col_count = len(headers)
    avail_width = 552.0  # letter width 612 - 60
    col_w = avail_width / col_count

    table = Table(table_data, colWidths=[col_w] * col_count)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 15))

    elements.append(Paragraph(
        f"Total Records: {len(rows)} | Generated by HostelFlow System on {datetime.now().strftime('%d-%b-%Y %I:%M %p')}",
        ParagraphStyle('Foot', parent=styles['Italic'], fontSize=8, textColor=colors.HexColor('#6c757d'), alignment=1)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
