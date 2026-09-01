"""
app/reports/referral_letter.py — Agent O (Round 3).

Builds the referral-letter PDF for a referral once it's been created.
Intended to visually match the existing clinical-report PDF in
app/reports/pdf_generator.py.

ASSUMPTION — I could not read the real app/reports/pdf_generator.py in this
session (see chat), so the reportlab layout below — a Platypus
SimpleDocTemplate with a title/heading style and a two-column table — is a
reasonable guess for a report-style PDF, not a byte-for-byte match to your
existing fonts/margins/helpers. Diff this against the real
pdf_generator.py and adjust before treating it as final. See
ASSUMPTIONS_AND_TODO.md items 3 and 5.
"""

from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

POSITIONING_LINE = (
    "This is an AI-assisted screening result, not a diagnosis. "
    "Please conduct a full clinical examination."
)


def _get_first_attr(obj, *names, default="N/A"):
    """
    ASSUMPTION: the real Scan attribute names for the two prediction
    probabilities aren't confirmed (app/db/models.py wasn't readable in
    this session). This tries a few plausible names in order and falls
    back to `default` instead of crashing — replace the candidate names
    below with the real field name once you've checked the model.
    """
    for name in names:
        if obj is not None and hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def build_referral_letter_pdf(scan, referral) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReferralLetterTitle", parent=styles["Heading1"], spaceAfter=12
    )
    notice_style = ParagraphStyle(
        "ReferralLetterNotice",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#B00020"),
        spaceBefore=4,
        spaceAfter=16,
    )
    body_style = styles["Normal"]

    scan_id = getattr(scan, "id", "N/A") if scan is not None else "N/A"
    scan_date = _get_first_attr(
        scan, "created_at", "uploaded_at", "upload_date", "timestamp"
    )
    risk_level = _get_first_attr(scan, "risk_level")
    dr_probability = _get_first_attr(
        scan, "dr_probability", "diabetic_retinopathy_probability", "dr_prob"
    )
    cataract_probability = _get_first_attr(
        scan, "cataract_probability", "cataract_prob"
    )

    story = [
        Paragraph("Clinical Referral Letter", title_style),
        Paragraph(POSITIONING_LINE, notice_style),
    ]

    rows = [
        ["Scan ID", str(scan_id)],
        ["Scan date", str(scan_date)],
        ["Risk level", str(risk_level).upper()],
        ["Diabetic retinopathy probability", str(dr_probability)],
        ["Cataract probability", str(cataract_probability)],
        ["Referring facility", referral.facility_name],
        ["Facility contact", referral.facility_contact or "N/A"],
        ["Referral status", referral.status],
        ["Referral notes", referral.notes or "—"],
    ]
    table = Table(rows, colWidths=[6 * cm, 10 * cm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#DDDDDD")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            f"Letter generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}.",
            body_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()
