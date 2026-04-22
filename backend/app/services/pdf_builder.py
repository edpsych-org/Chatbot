"""
PDF builders that serialise chatbot session data into PDF bytes.
Uses reportlab, already pinned in requirements.txt.
"""

from io import BytesIO
from typing import Iterable, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    PageBreak,
)


_TEAL = colors.HexColor("#00acb6")
_INK = colors.HexColor("#333333")
_MUTED = colors.HexColor("#737373")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], textColor=_TEAL, fontSize=20, spaceAfter=6
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            textColor=_MUTED,
            fontSize=10,
            spaceAfter=18,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            textColor=_TEAL,
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            textColor=_INK,
            fontSize=10.5,
            leading=14.5,
            spaceAfter=6,
        ),
        "question": ParagraphStyle(
            "question",
            parent=base["BodyText"],
            textColor=_INK,
            fontSize=10.5,
            leading=14,
            spaceBefore=6,
            spaceAfter=2,
            fontName="Helvetica-Bold",
        ),
        "answer": ParagraphStyle(
            "answer",
            parent=base["BodyText"],
            textColor=_INK,
            fontSize=10.5,
            leading=14,
            spaceAfter=4,
            leftIndent=12,
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=base["BodyText"],
            textColor=_MUTED,
            fontSize=9.5,
            leading=13,
        ),
    }


def _escape(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _iter_qa_pairs(session) -> Iterable[dict]:
    """Prefer the pre-built completed_qa_pairs list. If missing,
    fall back to assessment_data mcq_answers keyed by node id."""
    ctx = session.context_data or {}
    pairs = ctx.get("completed_qa_pairs") or []
    if pairs:
        return pairs
    rebuilt: list[dict] = []
    for category, data in (ctx.get("assessment_data") or {}).items():
        if not isinstance(data, dict):
            continue
        mcq_answers = data.get("mcq_answers") or {}
        elaborations = data.get("elaborations") or {}
        for node_id, value in mcq_answers.items():
            rebuilt.append(
                {
                    "question_text": node_id,
                    "answer_text": value,
                    "elaboration": elaborations.get(node_id) if isinstance(elaborations, dict) else None,
                    "category": category,
                }
            )
    return rebuilt


def build_school_share_pdf(
    student,
    session,
    summary_text: str,
    school_name: Optional[str] = None,
    completed_at_display: Optional[str] = None,
) -> bytes:
    """Render a school-share PDF and return the raw bytes.

    student: ORM Student row (uses first_name, last_name, date_of_birth, school_name)
    session: ORM ChatSession row (uses context_data)
    summary_text: narrative string produced by the summariser agent
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="School input",
    )
    s = _styles()
    full_name = f"{student.first_name} {student.last_name}".strip() or "Student"
    dob_str = student.date_of_birth.isoformat() if student.date_of_birth else "—"
    sch = school_name or getattr(student, "school_name", None) or "—"
    completed_str = completed_at_display or "—"

    story = []
    story.append(Paragraph(_escape(full_name), s["title"]))
    story.append(
        Paragraph(
            f"DOB: {_escape(dob_str)} &nbsp;&middot;&nbsp; School: {_escape(sch)} &nbsp;&middot;&nbsp; Completed: {_escape(completed_str)}",
            s["subtitle"],
        )
    )

    # Summary
    story.append(Paragraph("Summary", s["h2"]))
    for para in (summary_text or "").split("\n\n"):
        para = para.strip()
        if not para:
            continue
        story.append(Paragraph(_escape(para).replace("\n", "<br/>"), s["body"]))
    if not (summary_text or "").strip():
        story.append(
            Paragraph(
                "The school has completed the questionnaire. Full responses follow.",
                s["muted"],
            )
        )

    story.append(Spacer(1, 8))
    story.append(Paragraph("Full responses", s["h2"]))

    for idx, pair in enumerate(_iter_qa_pairs(session), start=1):
        q = pair.get("question_text") or pair.get("question") or f"Question {idx}"
        a = pair.get("answer_text") or pair.get("selected_option") or ""
        elab = pair.get("elaboration")
        story.append(Paragraph(f"Q{idx}. {_escape(q)}", s["question"]))
        answer_html = _escape(a)
        if elab:
            answer_html += f"<br/><i>{_escape(elab)}</i>"
        story.append(Paragraph(answer_html, s["answer"]))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
