import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

HOTEL_NAME = "GRAND AZURE"
HOTEL_ADDRESS = "123, Marina Drive, Mumbai - 400001"
HOTEL_PHONE = "+91 98765 43210"
HOTEL_EMAIL = "reservations@grandazure.com"
HOTEL_GST = "27AABCG1234A1Z5"

# Minimal Modern Palette
PRIMARY = colors.HexColor("#18181b")     # Stark black
TEXT_MAIN = colors.HexColor("#0F172A")   # Near black
TEXT_SUBTLE = colors.HexColor("#64748B") # Slate gray
BORDER = colors.HexColor("#E2E8F0")      # Soft border border
BG_LIGHT = colors.HexColor("#F8FAFC")    # Light background for headers
SUCCESS = colors.HexColor("#10B981")     # Green for paid
WARNING = colors.HexColor("#F59E0B")     # Amber for pending

def generate_invoice(booking, services, output_path=None):
    if output_path is None:
        downloads = os.path.expanduser("~/Desktop")
        output_path = os.path.join(downloads, f"Invoice_{booking['booking_ref']}.pdf")

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()

    def style(name, **kw):
        return ParagraphStyle(name, parent=styles['Normal'], **kw)

    # Typography setup
    h1_style = style('H1', fontSize=24, textColor=PRIMARY, fontName='Helvetica-Bold', alignment=TA_LEFT)
    h1_right = style('H1R', fontSize=24, textColor=TEXT_SUBTLE, fontName='Helvetica-Bold', alignment=TA_RIGHT)
    
    label_style = style('Label', fontSize=9, textColor=TEXT_SUBTLE, fontName='Helvetica', leading=14)
    value_style = style('Value', fontSize=10, textColor=TEXT_MAIN, fontName='Helvetica-Bold', leading=14)
    
    th_style = style('TH', fontSize=9, textColor=TEXT_SUBTLE, fontName='Helvetica-Bold', alignment=TA_CENTER)
    td_style = style('TD', fontSize=10, textColor=TEXT_MAIN, fontName='Helvetica', alignment=TA_CENTER)
    td_left = style('TDL', fontSize=10, textColor=TEXT_MAIN, fontName='Helvetica', alignment=TA_LEFT)
    td_right = style('TDR', fontSize=10, textColor=TEXT_MAIN, fontName='Helvetica', alignment=TA_RIGHT)

    total_label = style('TotLbl', fontSize=10, textColor=TEXT_SUBTLE, fontName='Helvetica', alignment=TA_RIGHT)
    total_val = style('TotVal', fontSize=11, textColor=TEXT_MAIN, fontName='Helvetica-Bold', alignment=TA_RIGHT)
    grand_label = style('GrndLbl', fontSize=12, textColor=PRIMARY, fontName='Helvetica-Bold', alignment=TA_RIGHT)
    grand_val = style('GrndVal', fontSize=14, textColor=PRIMARY, fontName='Helvetica-Bold', alignment=TA_RIGHT)

    story = []
    W = 170 * mm

    # ── Header Section ──
    now = datetime.now().strftime("%d %b %Y")
    header_data = [
        [Paragraph(HOTEL_NAME, h1_style), Paragraph("INVOICE", h1_right)],
        [Paragraph(f"{HOTEL_ADDRESS}<br/>{HOTEL_PHONE} | {HOTEL_EMAIL}<br/>GSTIN: {HOTEL_GST}", label_style),
         Paragraph(f"<b>Invoice #:</b> {booking['booking_ref']}<br/><b>Date:</b> {now}", 
                   style('InfoRight', fontSize=10, textColor=TEXT_MAIN, alignment=TA_RIGHT, leading=14))],
    ]
    header_table = Table(header_data, colWidths=[100*mm, 70*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,0), 24),
        ('BOTTOMPADDING', (0,1), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width=W, thickness=1, color=BORDER, spaceAfter=20))

    # ── Guest & Booking Details ──
    b_status = booking.get('status', '')
    p_method = booking.get('payment_method', 'Cash')
    
    details_data = [
        [Paragraph('<b>BILLED TO</b>', label_style), Paragraph('<b>BOOKING DETAILS</b>', label_style)],
        [Paragraph(f"{booking.get('customer_name', '')}", value_style), 
         Paragraph(f"Status: {b_status}", value_style)],
        [Paragraph(f"{booking.get('phone', '')}", value_style), 
         Paragraph(f"Payment Method: {p_method}", value_style)],
        [Paragraph(f"{booking.get('email', '')}", value_style), ''],
    ]
    details_table = Table(details_data, colWidths=[100*mm, 70*mm])
    details_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(details_table)
    story.append(Spacer(1, 20))

    # ── Stay Details Table ──
    stay_data = [
        [Paragraph('ROOM', th_style), Paragraph('TYPE', th_style), 
         Paragraph('CHECK IN', th_style), Paragraph('CHECK OUT', th_style), 
         Paragraph('NIGHTS', th_style), Paragraph('RATE', th_style), Paragraph('AMOUNT', th_style)]
    ]
    stay_data.append([
        Paragraph(booking.get('room_number', ''), td_style),
        Paragraph(booking.get('room_type', ''), td_style),
        Paragraph(booking.get('check_in_date', ''), td_style),
        Paragraph(booking.get('check_out_date', ''), td_style),
        Paragraph(str(booking.get('total_nights', 1)), td_style),
        Paragraph(f"Rs. {booking.get('price_per_night', 0):,.2f}", td_style),
        Paragraph(f"Rs. {booking.get('room_charges', 0):,.2f}", td_right),
    ])
    
    # Modern clean table style Without heavy solid fills
    table_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('LINEBELOW', (0,0), (-1,0), 1, BORDER),
        ('LINEBELOW', (0,1), (-1,-1), 1, BORDER),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ])
    
    stay_table = Table(stay_data, colWidths=[18*mm, 30*mm, 28*mm, 28*mm, 18*mm, 24*mm, 24*mm])
    stay_table.setStyle(table_style)
    story.append(stay_table)
    story.append(Spacer(1, 20))

    # ── Extra Services Table ──
    if services:
        story.append(Paragraph("ADDITIONAL SERVICES", style('SH', fontSize=9, fontName='Helvetica-Bold', textColor=TEXT_SUBTLE, spaceAfter=8)))
        svc_data = [[Paragraph('DATE', th_style), Paragraph('SERVICE', th_style), Paragraph('QTY', th_style), Paragraph('UNIT PRICE', th_style), Paragraph('AMOUNT', th_style)]]
        
        for s in services:
            svc_data.append([
                Paragraph(s.get('date',''), td_style),
                Paragraph(s.get('service_type','') + (f" - {s.get('description')}" if s.get('description') else ""), td_left),
                Paragraph(str(s.get('quantity',1)), td_style),
                Paragraph(f"Rs. {s.get('unit_price',0):,.2f}", td_style),
                Paragraph(f"Rs. {s.get('amount',0):,.2f}", td_right)
            ])
            
        svc_table = Table(svc_data, colWidths=[24*mm, 78*mm, 16*mm, 26*mm, 26*mm])
        svc_table.setStyle(table_style)
        story.append(svc_table)
        story.append(Spacer(1, 20))

    # ── Billing Summary ──
    room_charges = booking.get('room_charges', 0)
    extra = booking.get('extra_charges', 0)
    discount = booking.get('discount_amount', 0)
    tax = booking.get('tax_amount', 0)
    total = booking.get('total_amount', 0)
    paid = booking.get('paid_amount', 0)
    balance = total - paid

    coupon = booking.get('coupon_code', '')
    disc_label = f"Discount ({coupon})" if coupon else "Discount"

    bill_rows = [
        [Paragraph('Room Charges:', total_label), Paragraph(f"Rs. {room_charges:,.2f}", total_val)],
        [Paragraph('Extra Services:', total_label), Paragraph(f"Rs. {extra:,.2f}", total_val)],
    ]
    if discount > 0:
        bill_rows.append([Paragraph(disc_label+':', total_label), Paragraph(f"-Rs. {discount:,.2f}", total_val)])
        
    bill_rows += [
        [Paragraph('GST (12%):', total_label), Paragraph(f"Rs. {tax:,.2f}", total_val)],
        [Paragraph('TOTAL AMOUNT:', grand_label), Paragraph(f"Rs. {total:,.2f}", grand_val)],
        [Paragraph('Paid Amount:', total_label), Paragraph(f"Rs. {paid:,.2f}", style('TotPaid', fontSize=11, textColor=SUCCESS, fontName='Helvetica-Bold', alignment=TA_RIGHT))],
        [Paragraph('BALANCE DUE:', grand_label), Paragraph(f"Rs. {balance:,.2f}", grand_val)],
    ]

    bill_table = Table(bill_rows, colWidths=[130*mm, 40*mm])
    
    # Calculate rows for styling lines
    total_idx = len(bill_rows) - 3    # TOTAL AMOUNT row
    balance_idx = len(bill_rows) - 1  # BALANCE DUE row
    
    bill_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LINEABOVE', (0, total_idx), (-1, total_idx), 1, PRIMARY),
        ('LINEBELOW', (0, total_idx), (-1, total_idx), 1, BORDER),
        ('LINEABOVE', (0, balance_idx), (-1, balance_idx), 1, BORDER),
        ('BACKGROUND', (0, balance_idx), (-1, balance_idx), BG_LIGHT),
    ]))
    
    story.append(bill_table)
    story.append(Spacer(1, 25))

    # ── Payment Details footer ──
    pay_status = booking.get('payment_status', 'Pending')
    
    status_color = SUCCESS if pay_status == 'Paid' else WARNING
    status_text = f"<font color='{status_color.hexval()}'>{pay_status.upper()}</font>"

    terms_data = [
        [Paragraph('PAYMENT STATUS', label_style)],
        [Paragraph(status_text, style('Stat', fontSize=14, fontName='Helvetica-Bold'))],
    ]
    terms_table = Table(terms_data, colWidths=[W])
    terms_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(terms_table)
    
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width=W, thickness=0.5, color=BORDER, spaceAfter=10))
    story.append(Paragraph("Thank you for choosing Grand Azure. We hope to see you again!",
                           style('Footer', fontSize=9, textColor=TEXT_SUBTLE, alignment=TA_CENTER)))
    story.append(Paragraph("This is a computer-generated document. No signature is required.",
                           style('Footer2', fontSize=8, textColor=BORDER, alignment=TA_CENTER)))

    doc.build(story)
    return output_path
