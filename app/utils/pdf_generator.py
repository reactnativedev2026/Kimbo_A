import os
import uuid
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm


def format_currency(amount: float) -> str:
    return f"Rs.{amount:,.2f}"


def generate_purchase_pdf(
    purchase,
    product,
    contractor,
    payment_method: str,
    transaction_id: str,
    output_dir: str = "uploads/invoices"
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    file_name = f"purchase_{purchase.id}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(output_dir, file_name)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="Title",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        textColor=colors.white,
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        name="Subtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=11,
        leading=14,
        textColor=colors.whitesmoke,
        spaceAfter=18,
    )
    heading_style = ParagraphStyle(
        name="Heading",
        parent=styles["Normal"],
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    normal_style = ParagraphStyle(
        name="NormalText",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0f172a"),
    )
    muted_style = ParagraphStyle(
        name="MutedText",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
    )

    # Header card
    header_table = Table(
        [
            [Paragraph("SBBMS BUILD-MART", title_style)],
            [Paragraph("Payment Receipt & Token Summary", subtitle_style)],
        ],
        colWidths=[170 * mm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#059669")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#059669")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )

    amount_section = Table(
        [
            [Paragraph("Payment Amount", muted_style), Paragraph(format_currency(purchase.total_amount), heading_style)],
            [Paragraph("Receipt Generated", muted_style), ""],
        ],
        colWidths=[90 * mm, 80 * mm],
    )
    amount_section.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("SPAN", (0, 1), (1, 1)),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#d1fae5")),
                ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#065f46")),
                ("FONTSIZE", (0, 1), (-1, 1), 9),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
                ("TOPPADDING", (0, 1), (-1, 1), 6),
            ]
        )
    )

    purchase_info_data = [
        [Paragraph("Receipt/Purchase ID", muted_style), Paragraph(f"#KB-PUR-{purchase.id}", normal_style)],
        [Paragraph("Date & Time", muted_style), Paragraph(purchase.date.strftime("%d-%b-%Y %I:%M %p"), normal_style)],
        [Paragraph("Bill Number", muted_style), Paragraph(purchase.bill_number or "N/A", normal_style)],
    ]
    purchase_info_table = Table(purchase_info_data, colWidths=[90 * mm, 80 * mm])
    purchase_info_table.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    contractor_info_data = [
        [Paragraph("Contractor Name", muted_style), Paragraph(contractor.full_name if contractor else "Unknown Contractor", normal_style)],
        [Paragraph("Mobile Number", muted_style), Paragraph(contractor.mobile_number if contractor else "N/A", normal_style)],
        [Paragraph("Contractor Code", muted_style), Paragraph(contractor.contractor_code if contractor else "N/A", normal_style)],
    ]
    contractor_info_table = Table(contractor_info_data, colWidths=[90 * mm, 80 * mm])
    contractor_info_table.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    product_details_data = [
        [Paragraph(product.name if product else f"Product ID {purchase.product_id}", muted_style), Paragraph(
            f"{purchase.quantity_bought} {product.unit if product else 'Piece'} @ {format_currency(product.price_per_unit if product else 0.0)}/{product.unit if product else 'Piece'}",
            normal_style
        )],
        [Paragraph("Reward Points Earned", muted_style), Paragraph(f"+{purchase.tokens_earned} Points", ParagraphStyle(
            name="PointsStyle",
            parent=normal_style,
            textColor=colors.HexColor("#059669"),
            fontName="Helvetica-Bold"
        ))],
    ]
    product_details_table = Table(product_details_data, colWidths=[90 * mm, 80 * mm])
    product_details_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    payment_rows = [
        [Paragraph("Payment Mode", muted_style), Paragraph(payment_method.upper(), normal_style)]
    ]
    if transaction_id:
        payment_rows.append([Paragraph("UPI ID / Txn ID", muted_style), Paragraph(transaction_id, normal_style)])

    payment_info_table = Table(payment_rows, colWidths=[90 * mm, 80 * mm])
    payment_info_table.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    footer = Paragraph(
        "Thank you for doing business with us!", ParagraphStyle(
            name="Footer",
            parent=muted_style,
            alignment=TA_CENTER,
            spaceBefore=16,
        )
    )

    elements = [
        header_table,
        Spacer(1, 14),
        amount_section,
        Spacer(1, 10),
        purchase_info_table,
        Spacer(1, 10),
        contractor_info_table,
        Spacer(1, 10),
        Paragraph("Itemized Purchase", heading_style),
        product_details_table,
        Spacer(1, 10),
        payment_info_table,
        Spacer(1, 18),
        footer,
    ]

    doc.build(elements)
    return file_name
