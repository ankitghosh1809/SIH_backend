"""
app/reports/pdf_generator.py — Agent E

Renders a downloadable clinical PDF report for one scan. Pure function: takes a
Scan ORM row plus optional heatmap bytes, returns the finished PDF as bytes. No
DB or disk access happens here — app/api/reports.py fetches the scan and heatmap
and calls build_scan_report_pdf().
"""
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DISCLAIMER_TEXT = (
    "This is an automated screening aid, not a diagnosis. Please consult an "
    "ophthalmologist for clinical evaluation, particularly for any positive or "
    "medium/high-risk finding."
)

# green / amber / red — matches the low/medium/high risk_level values in app/db/models.py
_RISK_COLORS = {
    "low": colors.HexColor("#2e7d32"),
    "medium": colors.HexColor("#e6a100"),
    "high": colors.HexColor("#c62828"),
}

_MAX_HEATMAP_DIM = 3.2 * inch


def _condition_row(label: str, probability: float, positive: bool) -> list:
    return [label, f"{probability:.1%}", "Positive" if positive else "Negative"]


def _results_table() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])


def _scaled_heatmap_size(heatmap_bytes: bytes) -> tuple[float, float]:
    """Fit the heatmap inside a _MAX_HEATMAP_DIM square box, preserving aspect ratio."""
    orig_w, orig_h = ImageReader(io.BytesIO(heatmap_bytes)).getSize()
    aspect = (orig_h / orig_w) if orig_w else 1.0
    width, height = _MAX_HEATMAP_DIM, _MAX_HEATMAP_DIM * aspect
    if height > _MAX_HEATMAP_DIM:
        width, height = _MAX_HEATMAP_DIM / aspect, _MAX_HEATMAP_DIM
    return width, height


def build_scan_report_pdf(scan, heatmap_bytes: bytes | None) -> bytes:
    """
    scan: a Scan ORM row (has .id, .patient_name, .created_at, .dr_probability,
          .dr_positive, .cataract_probability, .cataract_positive, .risk_level,
          .model_version).
    heatmap_bytes: raw PNG bytes, or None if no heatmap was saved for this scan.
    Returns: the PDF file as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        title=f"Diabetic Eye Screening Report — {scan.id}",
    )
    styles = getSampleStyleSheet()
    story = []

    # 1. Title
    story.append(Paragraph("Diabetic Eye Screening Report", styles["Title"]))
    story.append(Spacer(1, 10))

    # 2. Scan ID, patient name, date/time
    created_at = scan.created_at.strftime("%Y-%m-%d %H:%M:%S") if scan.created_at else "Unknown"
    story.append(Paragraph(f"<b>Scan ID:</b> {scan.id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Patient:</b> {scan.patient_name or 'Not provided'}", styles["Normal"]))
    story.append(Paragraph(f"<b>Date/Time:</b> {created_at}", styles["Normal"]))
    story.append(Spacer(1, 16))

    # 3. Results table
    story.append(Paragraph("Results", styles["Heading2"]))
    story.append(Spacer(1, 4))
    table_data = [
        ["Condition", "Probability", "Result"],
        _condition_row("Diabetic Retinopathy", scan.dr_probability, scan.dr_positive),
        _condition_row("Cataract", scan.cataract_probability, scan.cataract_positive),
    ]
    results_table = Table(table_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch])
    results_table.setStyle(_results_table())
    story.append(results_table)
    story.append(Spacer(1, 16))

    # 4. Risk level, called out visually (green/amber/red)
    risk_level = (scan.risk_level or "").lower()
    risk_table = Table(
        [[f"Overall Risk Level: {risk_level.upper() or 'UNKNOWN'}"]],
        colWidths=[5.5 * inch],
    )
    risk_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _RISK_COLORS.get(risk_level, colors.grey)),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 13),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 20))

    # 5. Heatmap image — skipped cleanly if this scan has none
    if heatmap_bytes is not None:
        story.append(Paragraph("Explainability Heatmap", styles["Heading2"]))
        story.append(Spacer(1, 6))
        width, height = _scaled_heatmap_size(heatmap_bytes)
        story.append(Image(io.BytesIO(heatmap_bytes), width=width, height=height))
        story.append(Spacer(1, 16))

    # 6. Model version
    story.append(Paragraph(f"<b>Model Version:</b> {scan.model_version}", styles["Normal"]))
    story.append(Spacer(1, 20))

    # 7. Disclaimer
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=colors.HexColor("#444444"),
    )
    disclaimer_box = Table([[Paragraph(DISCLAIMER_TEXT, disclaimer_style)]], colWidths=[5.5 * inch])
    disclaimer_box.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#999999")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f0f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(disclaimer_box)

    doc.build(story)
    return buffer.getvalue()
