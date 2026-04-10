"""
Generate a comprehensive DevOps handoff PDF for the EdPsych project.

Run from backend/ with the venv active:
    python generate_devops_handoff.py

Output: ../EdPsych_DevOps_Handoff.pdf
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.platypus.tableofcontents import TableOfContents


# ─────────────────────────────────────────────────────────────────────
# Ed Psych colors
# ─────────────────────────────────────────────────────────────────────
BRAND_TEAL = colors.HexColor("#00acb6")
BRAND_TEAL_DARK = colors.HexColor("#0c888e")
BRAND_RED = colors.HexColor("#e61844")
INK = colors.HexColor("#333333")
MUTED = colors.HexColor("#737373")
LINE = colors.HexColor("#dedede")
SECTION_BG = colors.HexColor("#eeeeee")
CARD_BG = colors.HexColor("#f4f4f4")
TEAL_TINT = colors.HexColor("#e6f7f8")

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PDF = BASE_DIR / "EdPsych_DevOps_Handoff.pdf"


# ─────────────────────────────────────────────────────────────────────
# Styles
# ─────────────────────────────────────────────────────────────────────
_styles = getSampleStyleSheet()


def _make_styles():
    s = {}
    s["title"] = ParagraphStyle(
        "Title",
        parent=_styles["Title"],
        fontName="Times-Roman",
        fontSize=28,
        leading=34,
        textColor=BRAND_TEAL_DARK,
        alignment=1,
        spaceAfter=6,
    )
    s["subtitle"] = ParagraphStyle(
        "Subtitle",
        parent=_styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=13,
        leading=16,
        textColor=MUTED,
        alignment=1,
        spaceAfter=18,
    )
    s["h1"] = ParagraphStyle(
        "H1",
        parent=_styles["Heading1"],
        fontName="Times-Bold",
        fontSize=20,
        leading=24,
        textColor=BRAND_TEAL_DARK,
        spaceBefore=16,
        spaceAfter=8,
        borderPadding=4,
    )
    s["h2"] = ParagraphStyle(
        "H2",
        parent=_styles["Heading2"],
        fontName="Times-Bold",
        fontSize=15,
        leading=19,
        textColor=INK,
        spaceBefore=12,
        spaceAfter=6,
    )
    s["h3"] = ParagraphStyle(
        "H3",
        parent=_styles["Heading3"],
        fontName="Times-Bold",
        fontSize=12,
        leading=15,
        textColor=BRAND_RED,
        spaceBefore=10,
        spaceAfter=4,
    )
    s["body"] = ParagraphStyle(
        "Body",
        parent=_styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=INK,
        spaceAfter=4,
        alignment=0,
    )
    s["bullet"] = ParagraphStyle(
        "Bullet",
        parent=s["body"],
        leftIndent=14,
        bulletIndent=4,
        spaceAfter=2,
    )
    s["code"] = ParagraphStyle(
        "Code",
        parent=_styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=INK,
        backColor=CARD_BG,
        borderColor=LINE,
        borderWidth=0.5,
        borderPadding=6,
        leftIndent=4,
        rightIndent=4,
        spaceAfter=6,
    )
    s["muted"] = ParagraphStyle(
        "Muted",
        parent=s["body"],
        fontSize=8.5,
        textColor=MUTED,
    )
    s["cover_meta"] = ParagraphStyle(
        "CoverMeta",
        parent=s["body"],
        fontSize=10,
        textColor=MUTED,
        alignment=1,
        leading=14,
    )
    s["toc_entry"] = ParagraphStyle(
        "TOCEntry",
        parent=s["body"],
        fontSize=10,
        leading=14,
        leftIndent=0,
    )
    return s


STYLES = _make_styles()


# ─────────────────────────────────────────────────────────────────────
# Page template with header + footer
# ─────────────────────────────────────────────────────────────────────
class HandoffDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=22 * mm,
            bottomMargin=20 * mm,
            title="EdPsych DevOps Handoff",
            author="The Ed Psych Practice",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal",
        )
        self.addPageTemplates(
            [
                PageTemplate(id="cover", frames=frame, onPage=self._cover_chrome),
                PageTemplate(id="content", frames=frame, onPage=self._page_chrome),
            ]
        )

    def _cover_chrome(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(BRAND_TEAL)
        canvas.rect(0, A4[1] - 16 * mm, A4[0], 16 * mm, fill=1, stroke=0)
        canvas.setFont("Times-Roman", 11)
        canvas.setFillColor(colors.white)
        canvas.drawString(20 * mm, A4[1] - 11 * mm, "The Ed Psych Practice")
        canvas.drawRightString(
            A4[0] - 20 * mm, A4[1] - 11 * mm, "DevOps Handoff Document"
        )
        # Bottom bar
        canvas.setFillColor(BRAND_RED)
        canvas.rect(0, 0, A4[0], 6 * mm, fill=1, stroke=0)
        canvas.restoreState()

    def _page_chrome(self, canvas, doc):
        canvas.saveState()
        # Top teal bar
        canvas.setFillColor(BRAND_TEAL)
        canvas.rect(0, A4[1] - 12 * mm, A4[0], 12 * mm, fill=1, stroke=0)
        canvas.setFont("Times-Roman", 10)
        canvas.setFillColor(colors.white)
        canvas.drawString(20 * mm, A4[1] - 8 * mm, "The Ed Psych Practice")
        canvas.drawRightString(
            A4[0] - 20 * mm, A4[1] - 8 * mm, "DevOps Handoff Document"
        )
        # Bottom red rule + page number
        canvas.setStrokeColor(BRAND_RED)
        canvas.setLineWidth(0.8)
        canvas.line(20 * mm, 12 * mm, A4[0] - 20 * mm, 12 * mm)
        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(20 * mm, 7 * mm, "EdPsych Production Prototype")
        canvas.drawRightString(A4[0] - 20 * mm, 7 * mm, f"Page {doc.page}")
        canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────
# Document content — authored from the three research agents' output
# ─────────────────────────────────────────────────────────────────────
def _p(text: str, style: str = "body"):
    return Paragraph(text, STYLES[style])


def _h(text: str, level: int):
    return Paragraph(text, STYLES[f"h{level}"])


def _bullets(items: Iterable[str]):
    return [
        Paragraph(f"• {t}", STYLES["bullet"]) for t in items
    ]


def _code(text: str):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\n", "<br/>")
    return Paragraph(text, STYLES["code"])


def _kv_table(rows, col_widths=None):
    if col_widths is None:
        col_widths = [55 * mm, 110 * mm]
    data = [
        [Paragraph(f"<b>{k}</b>", STYLES["body"]), Paragraph(v, STYLES["body"])]
        for k, v in rows
    ]
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), TEAL_TINT),
                ("TEXTCOLOR", (0, 0), (0, -1), BRAND_TEAL_DARK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def _header_table(header, rows, col_widths):
    data = [
        [Paragraph(f"<b>{h}</b>", STYLES["body"]) for h in header]
    ] + [
        [Paragraph(c, STYLES["body"]) for c in row] for row in rows
    ]
    t = Table(data, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_TEAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD_BG]),
                ("GRID", (0, 0), (-1, -1), 0.3, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return t


# ─────────────────────────────────────────────────────────────────────
# Cover page
# ─────────────────────────────────────────────────────────────────────
def cover_page():
    story = [
        Spacer(1, 60 * mm),
        _p(
            "EdPsych AI Production Prototype",
            "title",
        ),
        _p(
            "A deployment, architecture &amp; operations reference for the DevOps team",
            "subtitle",
        ),
        Spacer(1, 8 * mm),
        _p(
            "Educational Psychology Assessment &amp; Report Generation Platform",
            "cover_meta",
        ),
        Spacer(1, 8 * mm),
        _p(
            "Backend: FastAPI + PostgreSQL &nbsp;|&nbsp; Frontend: Next.js 14",
            "cover_meta",
        ),
        _p(
            "Deployed on Railway (backend) and Vercel (frontend)",
            "cover_meta",
        ),
        Spacer(1, 40 * mm),
        _p(
            "Target audience: DevOps / Infrastructure / Site Reliability",
            "cover_meta",
        ),
        _p(
            "Scope: architecture, endpoints, workflows, deployment, operations",
            "cover_meta",
        ),
        PageBreak(),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Section 1 — Project overview
# ─────────────────────────────────────────────────────────────────────
def section_overview():
    story = [
        _h("1. Project Overview", 1),
        _p(
            "The Ed Psych Practice is an educational-psychology assessment and "
            "report-generation platform. Psychologists administer standardised "
            "assessments to students (via parent-driven interviews) and generate "
            "clinical reports using a multi-agent LLM pipeline. Four user roles "
            "share the platform: <b>Admin</b>, <b>Psychologist</b>, "
            "<b>Parent</b>, and <b>School</b>."
        ),
        _h("Key capabilities", 2),
        *_bullets(
            [
                "Admin: user / student / assignment management, data explorer, magic-link resends",
                "Psychologist: read-only student lists, report workspace, multi-agent generation, approval/rejection",
                "Parent: invite-based entry via magic link, conversational assessment, completion tracking",
                "School: similar to parent — invite-based with roster-scoped access",
                "Invite-based authentication via 48-hour MagicLinkTokens (no self-registration)",
                "Hybrid chat engine with flow_engine (MCQ + adaptive text + free-text)",
                "OCR pipeline for IQ test PDFs (tesseract + pdf2image + PyMuPDF)",
                "Structured report generation (profile, impact, recommendations, unified insights)",
                "Accessibility: 4-level text-size scaling (100/115/130/150) for older users",
            ]
        ),
        _h("High-level architecture", 2),
        _p(
            "<b>Frontend</b> (Vercel) → <b>Backend</b> (Railway, Docker) → "
            "<b>Database</b> (Neon PostgreSQL) + <b>LLM provider</b> "
            "(Groq default; Ollama local; OpenAI optional) + <b>Email</b> (Brevo API) + "
            "<b>Storage</b> (MinIO local, S3-ready)."
        ),
        _code(
            "[Browser]\n"
            "   |\n"
            "   v  HTTPS\n"
            "[Vercel — Next.js 14 App Router]  (NEXT_PUBLIC_API_URL)\n"
            "   |\n"
            "   v  HTTPS + Bearer JWT\n"
            "[Railway — FastAPI / Uvicorn in Docker]\n"
            "   |               |                |               |\n"
            "   v               v                v               v\n"
            "[Neon PG]   [Groq LLM API]   [Brevo API]      [MinIO / S3]\n"
            "(asyncpg)   (OpenAI-compat)  (magic links)    (optional)"
        ),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Section 2 — Tech stack
# ─────────────────────────────────────────────────────────────────────
def section_tech_stack():
    story = [
        PageBreak(),
        _h("2. Tech Stack", 1),
        _h("Backend", 2),
        _kv_table(
            [
                ("Language", "Python 3.10 (Dockerfile pins <b>python:3.10-slim</b>)"),
                ("Framework", "FastAPI 0.109.0 + Uvicorn 0.27.0 (standard extras)"),
                ("Database driver", "asyncpg 0.29.0 (async) + psycopg2-binary 2.9.9 (fallback)"),
                ("ORM", "SQLAlchemy 2.0.25 (async), Alembic 1.13.1 (available, not active)"),
                ("Auth", "python-jose 3.3.0 (JWT HS256), passlib 1.7.4 (bcrypt)"),
                ("LLM providers", "Groq (production), OpenAI (optional), Ollama (local dev)"),
                ("Email", "Brevo HTTP API v3 via requests; falls back to stdout log mode"),
                ("Storage", "MinIO 7.2.3 / boto3 1.34.34 (S3-compatible)"),
                ("OCR", "pytesseract 0.3.10 + pdf2image 1.17.0 + PyMuPDF 1.23.26 + Pillow 10.2.0"),
                ("Reports", "reportlab 4.0.9 (PDF), python-docx 1.1.0 (DOCX), jinja2 3.1.3"),
                ("Settings", "pydantic 2.5.3 + pydantic-settings 2.1.0 (env-file driven)"),
            ]
        ),
        _h("Frontend", 2),
        _kv_table(
            [
                ("Framework", "Next.js 14.2.0 App Router (no Pages Router)"),
                ("UI library", "React 18.2.0"),
                ("Language", "TypeScript 5 strict"),
                ("Styling", "Tailwind CSS 3.4.0 + PostCSS 8 + Autoprefixer"),
                ("Fonts", "next/font/google — Average (serif) + Nunito (sans)"),
                ("Data/API", "axios 1.6.0, fetch, custom API_BASE in lib/api.ts"),
                ("Forms", "react-hook-form 7.51.0 + @hookform/resolvers 3.3.0 + zod 3.22.0"),
                ("State", "zustand 4.5.0 (light usage); mostly local useState"),
                ("Markdown", "react-markdown for report rendering"),
                ("Hosting", "Vercel (git-push auto deploy)"),
            ]
        ),
        _h("Infrastructure", 2),
        _kv_table(
            [
                ("Backend hosting", "Railway (Docker, auto-deploy from GitHub)"),
                ("Frontend hosting", "Vercel (auto-deploy from GitHub)"),
                ("Database", "Neon serverless PostgreSQL (production); PostgreSQL 16+ (local)"),
                ("Container runtime", "Docker 24+ (Dockerfile in backend/)"),
                ("Local stack", "docker-compose: Postgres 16, Redis 7, MinIO"),
                ("Email provider", "Brevo transactional (API key required for real sends)"),
                ("LLM provider (prod)", "Groq llama-3.1-8b-instant"),
                ("OCR runtime", "Tesseract-OCR system binary (apt in Docker)"),
            ]
        ),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Section 3 — Directory structure (no md)
# ─────────────────────────────────────────────────────────────────────
def section_directory():
    story = [
        PageBreak(),
        _h("3. Directory Structure", 1),
        _p(
            "Code files only — <i>markdown, lock files, IDE metadata, "
            "__pycache__, venv, node_modules, .next are excluded.</i>"
        ),
        _h("Backend (d:/GEN AI/edpsych-production-prototype/backend/)", 2),
        _code(
            "backend/\n"
            "├── Dockerfile\n"
            "├── railway.json\n"
            "├── main.py                     # FastAPI entrypoint + lifespan\n"
            "├── requirements.txt            # Full dev dependencies\n"
            "├── requirements-deploy.txt     # Slim production deps (used in Docker)\n"
            "├── requirements-core.txt\n"
            "├── seed_test_users.py          # Creates admin/parent/psych accounts\n"
            "├── seed_questions.py           # Populates chatbot questions\n"
            "├── create_chat_tables.py       # Chat session tables + ENUMs\n"
            "├── create_magic_link_table.py  # Magic link + verification tables\n"
            "├── reset_database.py           # DROP/CREATE all (dev only)\n"
            "├── run_migration.py            # Execute *.sql migrations\n"
            "├── test_api.py  test_chatbot.sh\n"
            "├── app/\n"
            "│   ├── core/\n"
            "│   │   ├── config.py           # Pydantic Settings → env vars\n"
            "│   │   ├── database.py         # Async engine + get_db dependency\n"
            "│   │   └── security.py         # JWT, password hashing, current user\n"
            "│   ├── models/\n"
            "│   │   ├── user.py  student.py  student_guardian.py\n"
            "│   │   ├── assessment.py  assignment.py  chat.py\n"
            "│   │   ├── magic_link.py  verification_token.py\n"
            "│   │   ├── report.py  psychologist_report.py  upload.py\n"
            "│   ├── api/\n"
            "│   │   ├── auth.py              # /auth/login, /magic-login, /setup-password\n"
            "│   │   ├── students.py\n"
            "│   │   ├── student_guardians.py\n"
            "│   │   ├── assignments.py       # /assignments/*\n"
            "│   │   ├── chatbot.py  hybrid_chat.py\n"
            "│   │   ├── psychologist.py      # Read-only student list + workspace\n"
            "│   │   ├── psychologist_reports.py\n"
            "│   │   ├── admin.py             # User + student + assignment management\n"
            "│   │   ├── uploads.py  reports.py  verification.py\n"
            "│   ├── services/\n"
            "│   │   ├── local_llm.py         # Ollama/Groq/OpenAI abstraction\n"
            "│   │   └── pdf_extractor.py     # Tesseract + PyMuPDF OCR pipeline\n"
            "│   └── utils/\n"
            "│       ├── email.py             # Brevo send + DEV log fallback\n"
            "│       └── magic_link.py        # create/verify magic link tokens\n"
            "├── flows/\n"
            "│   └── parent_assessment_v1.json  # Hybrid chat flow definition\n"
            "└── migrations/\n"
            "    └── add_verification_tokens_table.sql"
        ),
        _h("Frontend (d:/GEN AI/edpsych-production-prototype/frontend/)", 2),
        _code(
            "frontend/\n"
            "├── package.json  tsconfig.json\n"
            "├── tailwind.config.js  next.config.js  postcss.config.js\n"
            "├── lib/api.ts                     # API_BASE + NEXT_PUBLIC_API_URL resolution\n"
            "├── public/\n"
            "│   ├── font-scale-boot.js         # Inline boot for text-size scaling\n"
            "│   └── images/cherry-tree.png     # Ed Psych hero accent\n"
            "├── components/\n"
            "│   ├── AccessibilityMenu.tsx      # Floating Aa button, 100/115/130/150%\n"
            "│   └── ConfirmModal.tsx           # Reusable confirm dialog\n"
            "├── app/\n"
            "│   ├── layout.tsx  globals.css    # Fonts + theme tokens + menu mount\n"
            "│   ├── page.tsx                   # Role-based redirect\n"
            "│   ├── login/page.tsx\n"
            "│   ├── register/page.tsx          # Invite-only info page\n"
            "│   ├── auth/magic/[token]/page.tsx # Magic link landing\n"
            "│   ├── dashboard/page.tsx         # Parent dashboard\n"
            "│   ├── chat/[assignmentId]/page.tsx # Assessment chat\n"
            "│   ├── admin/dashboard/page.tsx\n"
            "│   ├── psychologist/dashboard/page.tsx\n"
            "│   ├── psychologist/students/create/page.tsx\n"
            "│   ├── psychologist/reports/[reportId]/page.tsx\n"
            "│   ├── school/dashboard/page.tsx\n"
            "│   ├── student/[id]/workspace/page.tsx  # Report generation workspace\n"
            "│   ├── student/[id]/reports/page.tsx\n"
            "│   ├── parent/reports/[reportId]/page.tsx\n"
            "│   └── verify-access/[token]/page.tsx   # Legacy, redirects to /login\n"
            "└── src/\n"
            "    ├── types/chat.ts\n"
            "    ├── components/admin/\n"
            "    │   ├── DataExplorer.tsx  DetailDrawer.tsx  JsonViewer.tsx\n"
            "    │   └── tables/*.tsx  (Students, Assessments, Reports, Cognitive, IqUploads)\n"
            "    ├── components/chat/\n"
            "    │   ├── HybridChat.tsx         # Session orchestration\n"
            "    │   ├── MessageList.tsx  MessageBubble.tsx  ChatInput.tsx\n"
            "    │   ├── McqOptions.tsx  ProgressBar.tsx  TypingIndicator.tsx\n"
            "    │   └── CompletionBanner.tsx  ChatSkeleton.tsx\n"
            "    └── components/workspace/\n"
            "        ├── BackgroundSummaryCard.tsx  CognitiveReportCard.tsx\n"
            "        ├── UnifiedInsightsCard.tsx  MarkdownEditor.tsx\n"
            "        └── PdfUploadZone.tsx  ScoresTable.tsx"
        ),
        _h("Infrastructure (repo root)", 2),
        _code(
            "edpsych-production-prototype/\n"
            "├── docker-compose.yml       # Postgres + Redis + MinIO local stack\n"
            "├── .env.example             # Root env template\n"
            "├── vercel.json              # Vercel experimental services config\n"
            "├── backend/...\n"
            "└── frontend/..."
        ),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Section 4 — Environment variables
# ─────────────────────────────────────────────────────────────────────
def section_env_vars():
    rows = [
        ("DATABASE_URL", "BE", "PostgreSQL connection string (asyncpg)", "localhost dev", "Y"),
        ("SECRET_KEY", "BE", "JWT signing key (>=32 chars, random)", "placeholder", "Y"),
        ("ALGORITHM", "BE", "JWT algorithm", "HS256", "N"),
        ("ACCESS_TOKEN_EXPIRE_MINUTES", "BE", "JWT expiry in minutes", "1440 (24h)", "N"),
        ("MAGIC_LINK_EXPIRY_HOURS", "BE", "Magic link validity", "48", "N"),
        ("CORS_ORIGINS", "BE", "Comma-separated allowed origins", "localhost list", "Y"),
        ("FRONTEND_URL", "BE", "Used in magic-link email URLs", "localhost:3002", "Y"),
        ("USE_GROQ", "BE", "Enable Groq LLM provider", "false", "Y in prod"),
        ("GROQ_API_KEY", "BE", "Groq API key", "&lt;empty&gt;", "Y if USE_GROQ"),
        ("GROQ_MODEL", "BE", "Groq model id", "llama-3.1-8b-instant", "N"),
        ("GROQ_BASE_URL", "BE", "Groq OpenAI-compat endpoint", "api.groq.com/openai/v1", "N"),
        ("USE_OPENAI", "BE", "Enable OpenAI provider", "false", "N"),
        ("OPENAI_API_KEY", "BE", "OpenAI API key", "&lt;empty&gt;", "Y if USE_OPENAI"),
        ("OPENAI_MODEL", "BE", "OpenAI model id", "gpt-4o-mini", "N"),
        ("USE_LOCAL_LLM", "BE", "Enable Ollama local LLM", "true", "N"),
        ("OLLAMA_BASE_URL", "BE", "Ollama host", "localhost:11434", "N"),
        ("OLLAMA_MODEL", "BE", "Ollama model id", "qwen2.5:3b", "N"),
        ("BREVO_API_KEY", "BE", "Brevo transactional email key", "&lt;empty&gt;", "Y for real emails"),
        ("EMAIL_FROM_NAME", "BE", "From name on emails", "The EdPsych Practice", "N"),
        ("EMAIL_FROM_ADDRESS", "BE", "From address on emails", "noreply@...", "N"),
        ("MINIO_ENDPOINT", "BE", "S3-compatible endpoint", "localhost:9000", "N"),
        ("MINIO_ACCESS_KEY", "BE", "MinIO root user", "minioadmin", "N"),
        ("MINIO_SECRET_KEY", "BE", "MinIO root password", "minioadmin123", "N"),
        ("MINIO_BUCKET_IQ_TESTS", "BE", "Bucket name for IQ uploads", "iq-tests", "N"),
        ("MINIO_BUCKET_REPORTS", "BE", "Bucket name for generated reports", "reports", "N"),
        ("TESSERACT_PATH", "BE", "Windows path to tesseract.exe", "C:/Program Files/...", "N (Docker)"),
        ("TESSERACT_LANG", "BE", "OCR language", "eng", "N"),
        ("BACKEND_HOST", "BE", "Uvicorn bind address", "0.0.0.0", "N"),
        ("BACKEND_PORT", "BE", "Overridden by Railway PORT", "8000", "N"),
        ("DEBUG_MODE", "BE", "Verbose errors + echo SQL", "false", "N"),
        ("REDIS_URL", "BE", "Redis connection (unused today)", "localhost:6379", "N"),
        ("AI_TEMPERATURE", "BE", "LLM creativity (0..1)", "0.3", "N"),
        ("AI_MAX_TOKENS", "BE", "LLM max output tokens", "2000", "N"),
        ("AI_RETRY_ATTEMPTS", "BE", "LLM retry count", "3", "N"),
        ("MAX_FILE_SIZE_MB", "BE", "Upload ceiling", "10", "N"),
        ("ALLOWED_FILE_TYPES", "BE", "File extensions allowed", "pdf,png,jpg,jpeg", "N"),
        ("REPORT_LANGUAGE", "BE", "PDF report language", "en-GB", "N"),
        ("REPORT_FONT_SIZE", "BE", "PDF font size (pt)", "11", "N"),
        ("REPORT_PAGE_SIZE", "BE", "PDF page size", "A4", "N"),
        ("NEXT_PUBLIC_API_URL", "FE", "Backend API base URL", "localhost:8000/api/v1", "Y"),
    ]
    story = [
        PageBreak(),
        _h("4. Environment Variables (complete reference)", 1),
        _p(
            "Every variable read anywhere in the codebase. "
            "<b>BE</b> = backend, <b>FE</b> = frontend. "
            "The backend reads from <font face='Courier'>../.env</font> "
            "(project root) via Pydantic Settings. The frontend reads from "
            "<font face='Courier'>frontend/.env.local</font> plus Vercel dashboard."
        ),
        Spacer(1, 4),
        _header_table(
            ["Variable", "Scope", "Purpose", "Default", "Req?"],
            rows,
            col_widths=[40 * mm, 12 * mm, 50 * mm, 42 * mm, 16 * mm],
        ),
        Spacer(1, 6),
        _h("Minimum production secrets to set", 2),
        *_bullets(
            [
                "<b>Railway backend service:</b> DATABASE_URL, SECRET_KEY, CORS_ORIGINS, FRONTEND_URL, USE_GROQ, GROQ_API_KEY, BREVO_API_KEY, EMAIL_FROM_ADDRESS",
                "<b>Vercel frontend project:</b> NEXT_PUBLIC_API_URL",
                "<b>Neon database:</b> provisioned via dashboard, connection string copied to Railway",
                "<b>Brevo account:</b> sender email verified, API key generated",
            ]
        ),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Section 5 — Database schema
# ─────────────────────────────────────────────────────────────────────
def section_database():
    story = [
        PageBreak(),
        _h("5. Database Schema", 1),
        _p(
            "All tables live in a single PostgreSQL database. Tables are "
            "created on startup via <font face='Courier'>Base.metadata.create_all</font> "
            "in <font face='Courier'>main.py</font>'s lifespan event — no migration tool is "
            "active today. Alembic is installed but unused."
        ),
        _h("users", 2),
        _p(
            "Auth + profile. <b>password_hash is NULLABLE</b> — a null hash "
            "means the account was created by admin and still needs password "
            "setup via magic link."
        ),
        *_bullets(
            [
                "id (UUID, PK)",
                "email (VARCHAR, unique, indexed)",
                "password_hash (VARCHAR, <b>nullable</b> — set via /auth/setup-password)",
                "role (ENUM UserRole: ADMIN / PSYCHOLOGIST / PARENT / SCHOOL)",
                "full_name, phone, organization (VARCHAR)",
                "is_active (BOOL), is_verified (BOOL)",
                "created_at, updated_at (TIMESTAMP WITH TZ)",
            ]
        ),
        _h("students", 2),
        _p("A child being assessed."),
        *_bullets(
            [
                "id (UUID, PK)",
                "first_name, last_name, year_group, school_name (VARCHAR)",
                "date_of_birth (DATE)",
                "created_by_user_id (FK → users.id)",
                "created_at (TIMESTAMP)",
            ]
        ),
        _h("student_guardians", 2),
        _p("Many-to-many link between students and parent/school users."),
        *_bullets(
            [
                "id (UUID, PK)",
                "student_id (FK → students.id)",
                "guardian_user_id (FK → users.id)",
                "relationship_type (VARCHAR: Father, Mother, Guardian, ...)",
                "is_primary (VARCHAR 'true'/'false')",
                "created_by_user_id (FK → users.id)",
            ]
        ),
        _h("assessment_assignments", 2),
        _p("An assessment task assigned to a parent for a specific student."),
        *_bullets(
            [
                "id (UUID, PK)",
                "assigned_by_psychologist_id (FK → users.id)",
                "student_id (FK → students.id)",
                "assigned_to_user_id (FK → users.id — the parent)",
                "assessment_session_id (FK → chat_sessions.id, nullable)",
                "status (ENUM AssignmentStatus: ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED)",
                "notes, due_date",
                "assigned_at, started_at, completed_at, updated_at",
            ]
        ),
        _h("magic_link_tokens", 2),
        _p(
            "One-time tokens used by admins to invite parents. "
            "Each token can be tied to an assignment so parents land directly in the chat."
        ),
        *_bullets(
            [
                "id (UUID, PK)",
                "user_id (FK → users.id)",
                "token (VARCHAR, unique, indexed)",
                "expires_at (TIMESTAMP, default +48h)",
                "used_at (TIMESTAMP, nullable)",
                "assignment_id (FK → assessment_assignments.id, nullable)",
                "purpose (VARCHAR: login / assessment_invite / password_reset)",
                "created_at",
            ]
        ),
        _h("chat_sessions", 2),
        _p("One conversation session for a parent answering an assessment."),
        *_bullets(
            [
                "id (UUID, PK)",
                "assignment_id (FK → assessment_assignments.id)",
                "user_id (FK → users.id — the parent)",
                "user_type, flow_type (VARCHAR)",
                "status (ENUM ChatSessionStatus: active / paused / completed)",
                "current_step (INT), current_node_id (VARCHAR)",
                "context_data (JSONB — stores answered_node_ids, assessment_data, completed_qa_pairs)",
                "started_at, last_interaction_at, completed_at, duration_minutes",
            ]
        ),
        _h("chat_messages", 2),
        _p("Each bot/user/system message in a chat session."),
        *_bullets(
            [
                "id (UUID, PK), session_id (FK)",
                "role (bot / user / system)",
                "content (TEXT)",
                "message_type (VARCHAR)",
                "message_metadata (JSONB — node_id, category, selected_option)",
                "timestamp",
            ]
        ),
        _h("psychologist_reports + cognitive_profiles + iq_test_uploads", 2),
        _p(
            "Psychologist-facing report workspace. A report is composed of "
            "multiple editable sections (background, impact, recommendations, "
            "unified insights). OCR'd IQ scores live in cognitive_profiles "
            "and are surfaced by the workspace UI."
        ),
        _h("ai_generation_jobs", 2),
        _p(
            "Async jobs for background LLM generation — status transitions through "
            "pending → running → succeeded / failed. Keeps UI responsive while the "
            "model runs."
        ),
        _h("Supporting tables", 2),
        *_bullets(
            [
                "flow_definitions / conversation_templates — static flow data",
                "chatbot_questions / chatbot_answers — legacy question bank",
                "generated_reports / final_reports / report_reviews — older report pipeline",
                "verification_tokens — legacy email-verify / DOB flow (deprecated)",
                "assessment_sessions — legacy sessions from the pre-hybrid-chat system",
            ]
        ),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Section 6 — API endpoints
# ─────────────────────────────────────────────────────────────────────
def _endpoint_row(method: str, path: str, auth: str, purpose: str):
    return [f"<b>{method}</b>", f"<font face='Courier'>{path}</font>", auth, purpose]


def section_api_endpoints():
    col_widths = [14 * mm, 70 * mm, 22 * mm, 64 * mm]
    header = ["Method", "Path", "Auth", "Purpose"]

    auth_rows = [
        _endpoint_row("POST", "/auth/login", "Public", "Email + password → {access_token, user}"),
        _endpoint_row("POST", "/auth/magic-login", "Public (token)", "Verify magic link. Returns needs_password_setup flag or JWT."),
        _endpoint_row("POST", "/auth/setup-password", "Public (token)", "First-time password setup for invited users. Returns JWT."),
        _endpoint_row("GET", "/auth/me", "Bearer", "Return current user profile."),
    ]

    admin_rows = [
        _endpoint_row("GET", "/admin/stats", "Admin", "Users/students/assignments/reports counts + role breakdown."),
        _endpoint_row("GET", "/admin/users", "Admin", "List users with optional role filter."),
        _endpoint_row("POST", "/admin/users", "Admin", "Create a user (ADMIN/PSYCHOLOGIST/SCHOOL/PARENT)."),
        _endpoint_row("PATCH", "/admin/users/{id}", "Admin", "Update user fields / role."),
        _endpoint_row("PATCH", "/admin/users/{id}/toggle-status", "Admin", "Activate or deactivate an account."),
        _endpoint_row("POST", "/admin/users/{id}/reset-assessment", "Admin", "Clear chat session for a user (debug/dev)."),
        _endpoint_row("DELETE", "/admin/users/{id}", "Admin", "Hard delete a user and cascades."),
        _endpoint_row("GET", "/admin/students/all-with-details", "Admin", "Every student + guardians + active assignment + progress."),
        _endpoint_row("POST", "/admin/students/create-with-parents", "Admin", "Create student + parent User(s) + StudentGuardian links."),
        _endpoint_row("GET", "/admin/assignments/all", "Admin", "List every assignment with nested student + assigned_to."),
        _endpoint_row("POST", "/admin/assignments/assign", "Admin", "Create AssessmentAssignment + MagicLinkToken + send invite email."),
        _endpoint_row("POST", "/admin/assignments/{id}/resend-link", "Admin", "Invalidate old links, create new token, resend email, return link."),
        _endpoint_row("PATCH", "/admin/assignments/{id}/cancel", "Admin", "Set status to CANCELLED (not allowed if already COMPLETED)."),
        _endpoint_row("GET", "/admin/explorer/{entity}", "Admin", "Data Explorer: raw table dumps for DevOps/debug."),
    ]

    psych_rows = [
        _endpoint_row("GET", "/psychologist/students/all-students", "Psych/Admin", "Read-only student list with parent info + progress %."),
        _endpoint_row("GET", "/psychologist/assignments", "Psych", "Assignments assigned by the current psychologist."),
        _endpoint_row("POST", "/psychologist/students/create-with-parents", "Psych", "(Legacy path) create student + guardians."),
    ]

    psych_reports_rows = [
        _endpoint_row("GET", "/psychologist-reports/students/{id}/workspace", "Psych", "Full workspace snapshot: cognitive profiles + all sections."),
        _endpoint_row("POST", "/psychologist-reports/students/{id}/background-summary/generate", "Psych", "Kick off background-summary LLM generation job."),
        _endpoint_row("POST", "/psychologist-reports/students/{id}/cognitive-report/upload", "Psych", "Upload IQ test PDF → OCR → parsed scores."),
        _endpoint_row("POST", "/psychologist-reports/students/{id}/cognitive-report/generate", "Psych", "Generate cognitive report markdown via LLM."),
        _endpoint_row("POST", "/psychologist-reports/students/{id}/unified-insights/generate", "Psych", "Synthesise all sources into one insights doc."),
        _endpoint_row("POST", "/psychologist-reports/students/{id}/reports/blank", "Psych", "Create a blank report record to edit manually."),
        _endpoint_row("PATCH", "/psychologist-reports/reports/{id}", "Psych", "Update any section text of a report."),
        _endpoint_row("DELETE", "/psychologist-reports/reports/{id}", "Psych", "Delete a report."),
        _endpoint_row("POST", "/psychologist-reports/reports/{id}/finalize", "Psych", "Lock a report as final (parent can then view)."),
    ]

    chat_rows = [
        _endpoint_row("POST", "/hybrid-chat/start", "Bearer", "Start a new chat session for an assignment."),
        _endpoint_row("GET", "/hybrid-chat/sessions/{id}/resume", "Bearer", "Resume an existing session (session + message history)."),
        _endpoint_row("POST", "/hybrid-chat/sessions/{id}/message", "Bearer", "Send a user message. Returns bot reply + progress + is_complete."),
        _endpoint_row("POST", "/hybrid-chat/sessions/{id}/complete", "Bearer", "Idempotent finalize: set assignment COMPLETED, store QA pairs."),
    ]

    assignments_rows = [
        _endpoint_row("GET", "/my-assignments", "Bearer", "Parent's own assignments list."),
        _endpoint_row("GET", "/assignments/{id}", "Bearer", "Assignment detail."),
    ]

    story = [
        PageBreak(),
        _h("6. API Endpoints (full catalog)", 1),
        _p(
            "Every endpoint the backend exposes under "
            "<font face='Courier'>/api/v1</font>. Grouped by router. Auth is either "
            "Public, Bearer (any logged-in user), or role-restricted."
        ),
        _h("6.1 Authentication (app/api/auth.py)", 2),
        _header_table(header, auth_rows, col_widths),
        _h("6.2 Admin (app/api/admin.py)", 2),
        _header_table(header, admin_rows, col_widths),
        PageBreak(),
        _h("6.3 Psychologist (app/api/psychologist.py)", 2),
        _header_table(header, psych_rows, col_widths),
        _h("6.4 Psychologist reports (app/api/psychologist_reports.py)", 2),
        _header_table(header, psych_reports_rows, col_widths),
        _h("6.5 Hybrid chat (app/api/hybrid_chat.py)", 2),
        _header_table(header, chat_rows, col_widths),
        _h("6.6 Assignments (app/api/assignments.py)", 2),
        _header_table(header, assignments_rows, col_widths),
        _h("6.7 Utility", 2),
        *_bullets(
            [
                "<font face='Courier'>GET /</font> — root status JSON",
                "<font face='Courier'>GET /health</font> — {status, database, llm, timestamp}",
                "<font face='Courier'>GET /api/docs</font> — Swagger UI (FastAPI auto-generated)",
                "<font face='Courier'>GET /api/redoc</font> — ReDoc UI",
            ]
        ),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Section 7 — User workflows
# ─────────────────────────────────────────────────────────────────────
def section_workflows():
    story = [
        PageBreak(),
        _h("7. User Workflows", 1),
        _p(
            "Each workflow below lists the UI steps and the exact endpoints "
            "called. Use this section when debugging a reported issue — "
            "trace the user's story to the endpoint, then to the DB table."
        ),
        _h("7.1 Admin workflow", 2),
        _code(
            "1. /login (email + password)\n"
            "   POST /auth/login  →  {access_token, user}\n"
            "2. redirect to /admin/dashboard\n"
            "3. Overview tab\n"
            "   GET /admin/stats\n"
            "4. Create user modal\n"
            "   POST /admin/users\n"
            "5. Students tab → Create Student\n"
            "   POST /admin/students/create-with-parents\n"
            "   (creates User with password_hash=NULL + Student + StudentGuardian)\n"
            "6. Assignments tab → New Assignment\n"
            "   POST /admin/assignments/assign\n"
            "     - creates AssessmentAssignment\n"
            "     - creates MagicLinkToken (48h expiry, purpose=assessment_invite)\n"
            "     - sends Brevo email with magic link URL\n"
            "     - returns {assignment_id, magic_link}\n"
            "7. Resend Link button\n"
            "   POST /admin/assignments/{id}/resend-link\n"
            "     - invalidates existing unused magic links for this assignment\n"
            "     - creates new token, re-sends email, returns the URL\n"
            "8. Data Explorer\n"
            "   GET /admin/explorer/{entity}  (raw table dumps)"
        ),
        _h("7.2 Magic link / parent onboarding", 2),
        _code(
            "PSYCHOLOGIST                       SYSTEM                            PARENT\n"
            "     |                                |                                |\n"
            "     +-- assign assessment -----------+                                |\n"
            "     |                                +-- create AssessmentAssignment  |\n"
            "     |                                +-- create MagicLinkToken (48h)  |\n"
            "     |                                +-- send Brevo email ----------->|\n"
            "     |                                |                                |\n"
            "     |                                |         parent clicks link <---+\n"
            "     |                                |                                |\n"
            "     |                                |  GET /auth/magic/{token}       |\n"
            "     |                                |  POST /auth/magic-login        |\n"
            "     |                                |                                |\n"
            "     |                                |  password_hash is NULL?        |\n"
            "     |                                |    YES → password setup form   |\n"
            "     |                                |          POST /auth/setup-password\n"
            "     |                                |          → store hash, verify  |\n"
            "     |                                |          → consume token       |\n"
            "     |                                |          → return JWT + assignment_id\n"
            "     |                                |    NO  → consume token, return JWT\n"
            "     |                                |                                |\n"
            "     |                                |  redirect to /chat/{assignmentId}"
        ),
        _h("7.3 Parent assessment flow", 2),
        _code(
            "1. /chat/{assignmentId} — HybridChat component mounts\n"
            "2. POST /hybrid-chat/start  (or GET resume if session exists)\n"
            "   - creates ChatSession with status=active, flow_type=parent_assessment_v1\n"
            "3. bot sends first question from flows/parent_assessment_v1.json\n"
            "4. repeat for N turns:\n"
            "   POST /hybrid-chat/sessions/{id}/message  (MCQ choice or free text)\n"
            "     - flow_engine advances to next node\n"
            "     - every 5th answer triggers AI acknowledgement\n"
            "     - context_data.assessment_data accumulates category answers\n"
            "     - progress_percentage = answered_nodes / total_nodes\n"
            "5. on last node, bot returns message_type='completion'\n"
            "   - session.status = COMPLETED (automatic path)\n"
            "6. frontend calls POST /hybrid-chat/sessions/{id}/complete\n"
            "   - idempotent finalize: stores completed_qa_pairs,\n"
            "     sets assignment.status = COMPLETED, computes duration\n"
            "7. CompletionBanner renders → redirect to /dashboard"
        ),
        _h("7.4 Psychologist report generation", 2),
        _code(
            "1. /login → redirect to /psychologist/dashboard\n"
            "2. Students tab lists all students\n"
            "   GET /psychologist/students/all-students\n"
            "3. Click student → /student/{id}/workspace\n"
            "   GET /psychologist-reports/students/{id}/workspace\n"
            "     - returns cognitive_profiles, latest session,\n"
            "       all existing report sections\n"
            "4. (optional) Upload IQ test PDF\n"
            "   POST /psychologist-reports/students/{id}/cognitive-report/upload\n"
            "     - stores in MinIO iq-tests bucket\n"
            "     - Tesseract OCR → PyMuPDF text extraction\n"
            "     - parses WAIS/WISC/WJ subtest scores into cognitive_profiles\n"
            "5. Generate background summary\n"
            "   POST /psychologist-reports/students/{id}/background-summary/generate\n"
            "     - creates AIGenerationJob (pending)\n"
            "     - background task calls local_llm_service (Groq/OpenAI/Ollama)\n"
            "     - fills profile_text section of PsychologistReport\n"
            "6. Generate cognitive report (same pattern)\n"
            "7. Generate unified insights (synthesises all above)\n"
            "8. Edit any section via MarkdownEditor → PATCH /psychologist-reports/reports/{id}\n"
            "9. Finalize → POST /psychologist-reports/reports/{id}/finalize\n"
            "   - parent now sees the report in their dashboard"
        ),
        _h("7.5 School workflow", 2),
        _p(
            "Same invite-based flow as Parent — admin assigns assessment → school "
            "receives magic link → completes chat → sees completion. School "
            "role's dashboard shows their own roster scoped to their organization."
        ),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Section 8 — Frontend routing map
# ─────────────────────────────────────────────────────────────────────
def section_frontend_routing():
    rows = [
        ["/", "Public", "Role-based redirect after reading localStorage.user"],
        ["/login", "Public", "Email + password form; JWT stored in localStorage"],
        ["/register", "Public", "Invite-only info page; no self-registration"],
        ["/auth/magic/[token]", "Public", "Magic link landing: password setup or auto-login"],
        ["/dashboard", "Parent/School", "Parent's assigned assessments + approved reports"],
        ["/chat/[assignmentId]", "Parent/School", "HybridChat component — assessment conversation"],
        ["/admin/dashboard", "Admin", "Overview / Students / Assignments / Data Explorer tabs"],
        ["/psychologist/dashboard", "Psych", "Reports Review / Assignments / Students tabs"],
        ["/psychologist/students/create", "Psych", "Legacy student creation (now admin-only)"],
        ["/psychologist/reports/[reportId]", "Psych", "Full report edit view"],
        ["/school/dashboard", "School", "Roster + assignment stats scoped to the school"],
        ["/student/[id]", "Psych", "Student profile summary"],
        ["/student/[id]/workspace", "Psych", "Report generation workspace (cards + markdown editors)"],
        ["/student/[id]/reports", "Psych", "Student's report history"],
        ["/parent/reports/[reportId]", "Parent", "Read-only approved report view"],
        ["/verify-access/[token]", "Legacy", "Redirects to /login (deprecated flow)"],
        ["/verify-dob/[token]", "Legacy", "Redirects to /login (deprecated flow)"],
    ]
    story = [
        PageBreak(),
        _h("8. Frontend Routing Map", 1),
        _p(
            "Every route under <font face='Courier'>frontend/app/</font>. "
            "Role guards are client-side: pages read the JWT + user from "
            "localStorage and redirect to /login if missing."
        ),
        _header_table(
            ["Path", "Access", "Purpose"],
            rows,
            col_widths=[58 * mm, 26 * mm, 86 * mm],
        ),
        _h("Mounted global components", 2),
        *_bullets(
            [
                "<b>AccessibilityMenu</b> — floating bottom-right Aa button, four text-size presets (100/115/130/150%). Sets <font face='Courier'>data-font-scale</font> on &lt;html&gt; and persists to localStorage. Inline script <font face='Courier'>/font-scale-boot.js</font> applies the saved preference before React hydration to prevent flash.",
                "<b>ConfirmModal</b> — reusable confirm dialog with danger/default variants.",
                "<b>noise-overlay</b> — decorative SVG fractal noise at 3% opacity.",
            ]
        ),
        _h("Theme tokens", 2),
        *_bullets(
            [
                "<font color='#00acb6'><b>#00acb6</b></font> — primary teal (navigation, brand)",
                "<font color='#0c888e'><b>#0c888e</b></font> — teal dark (hover / brand wordmark)",
                "<font color='#e61844'><b>#e61844</b></font> — accent red (CTAs)",
                "<font color='#86b454'><b>#86b454</b></font> — service green",
                "<font color='#333333'><b>#333333</b></font> — body ink",
                "<font color='#eeeeee'><b>#eeeeee</b></font> — hero band / cover background",
                "Fonts: <i>Average</i> serif for headings, <i>Nunito</i> sans for body (via next/font)",
            ]
        ),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Section 9 — Deployment
# ─────────────────────────────────────────────────────────────────────
def section_deployment():
    story = [
        PageBreak(),
        _h("9. Deployment", 1),
        _h("9.1 Backend — Railway (Docker)", 2),
        _p(
            "The backend deploys via Docker on Railway. The Dockerfile is in "
            "<font face='Courier'>backend/Dockerfile</font> and <b>`railway up` must be run "
            "from the backend/ subdirectory</b> (not project root) — the "
            "<font face='Courier'>railway.json</font> dockerfilePath is relative to that directory."
        ),
        _code(
            "# backend/Dockerfile\n"
            "FROM python:3.10-slim\n"
            "RUN apt-get update && apt-get install -y --no-install-recommends \\\n"
            "    tesseract-ocr poppler-utils \\\n"
            "    && rm -rf /var/lib/apt/lists/*\n"
            "WORKDIR /app\n"
            "COPY requirements-deploy.txt .\n"
            "RUN pip install --no-cache-dir -r requirements-deploy.txt\n"
            "COPY . .\n"
            "EXPOSE 8000\n"
            "CMD [\"sh\", \"-c\", \"uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}\"]"
        ),
        _code(
            "# backend/railway.json\n"
            "{\n"
            "  \"$schema\": \"https://railway.com/railway.schema.json\",\n"
            "  \"build\": { \"builder\": \"DOCKERFILE\", \"dockerfilePath\": \"Dockerfile\" },\n"
            "  \"deploy\": {\n"
            "    \"startCommand\": \"sh -c \\\"uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}\\\"\",\n"
            "    \"restartPolicyType\": \"ON_FAILURE\",\n"
            "    \"restartPolicyMaxRetries\": 3\n"
            "  }\n"
            "}"
        ),
        _h("9.2 Frontend — Vercel", 2),
        _p(
            "Git push to main triggers an automatic Vercel build and deploy. "
            "No custom vercel.json is required; the frontend/ folder is detected "
            "as a Next.js project."
        ),
        *_bullets(
            [
                "Set <font face='Courier'>NEXT_PUBLIC_API_URL</font> in Vercel dashboard → Project → Environment Variables (points to Railway backend URL, e.g. https://edpsych.up.railway.app)",
                "API_BASE is resolved in <font face='Courier'>frontend/lib/api.ts</font>: strips trailing newlines, appends /api/v1 if missing, falls back to localhost:8000 in dev",
                "Build command: <font face='Courier'>next build</font>",
                "Output: static + serverless functions",
                "Accessibility boot script <font face='Courier'>/font-scale-boot.js</font> is served from public/",
            ]
        ),
        _h("9.3 Git push → production", 2),
        _code(
            "[developer]                        [GitHub main]\n"
            "     |                                  |\n"
            "     +-- git push --------------------->|\n"
            "     |                                  |\n"
            "     |              +-------------------+-------------------+\n"
            "     |              |                                       |\n"
            "     v              v                                       v\n"
            "[Vercel]        [Railway]                             [Neon PG]\n"
            "  |               |                                    (unchanged)\n"
            "  build           Docker build\n"
            "  deploy          deploy\n"
            "  healthcheck     healthcheck (GET /health)\n"
            "  promote         promote\n"
            "     |              |\n"
            "     v              v\n"
            "frontend.app     api.up.railway.app"
        ),
        _h("9.4 Rollback", 2),
        *_bullets(
            [
                "<b>Railway</b>: Dashboard → Deployments → pick previous → Redeploy.",
                "<b>Vercel</b>: Dashboard → Deployments → pick previous → Promote to Production.",
                "<b>Neon</b>: point-in-time recovery up to 30 days via console.",
            ]
        ),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Section 10 — Local dev
# ─────────────────────────────────────────────────────────────────────
def section_local_dev():
    story = [
        PageBreak(),
        _h("10. Local Development", 1),
        _h("Prerequisites", 2),
        *_bullets(
            [
                "Python 3.10+ (3.10 matches production Docker image)",
                "Node.js 20+",
                "PostgreSQL 16+ (native install, or docker-compose)",
                "Tesseract-OCR (Windows installer, apt, or brew)",
                "git, curl, bash",
            ]
        ),
        _h("Step 1 — Clone and create root .env", 2),
        _code(
            "git clone <repo-url> edpsych-production-prototype\n"
            "cd edpsych-production-prototype\n"
            "cp .env.example .env\n"
            "# edit .env — at minimum set:\n"
            "#   DATABASE_URL=postgresql://edpsych:edpsych_secure_password@localhost:5432/edpsych_db\n"
            "#   SECRET_KEY=$(openssl rand -hex 32)\n"
            "#   CORS_ORIGINS=http://localhost:3000\n"
            "#   FRONTEND_URL=http://localhost:3000\n"
            "#   USE_GROQ=true  (and GROQ_API_KEY=...)  OR  USE_LOCAL_LLM=true\n"
            "#   BREVO_API_KEY=...  (optional — skip for DEV log mode)"
        ),
        _h("Step 2 — PostgreSQL (option A: docker-compose)", 2),
        _code(
            "docker compose up -d postgres redis minio\n"
            "# postgres is on localhost:5432\n"
            "# minio is on localhost:9000 (console 9001)"
        ),
        _h("Step 2 — PostgreSQL (option B: native)", 2),
        _code(
            "# Windows: use PostgreSQL 18 installer from postgresql.org\n"
            "# then from psql:\n"
            "CREATE USER edpsych WITH PASSWORD 'edpsych_secure_password';\n"
            "CREATE DATABASE edpsych_db OWNER edpsych;\n"
            "GRANT ALL PRIVILEGES ON DATABASE edpsych_db TO edpsych;"
        ),
        _h("Step 3 — Backend", 2),
        _code(
            "cd backend\n"
            "python -m venv venv\n"
            "# Windows: venv\\Scripts\\activate\n"
            "# Linux/macOS: source venv/bin/activate\n"
            "pip install -r requirements.txt\n"
            "python seed_test_users.py      # creates admin1@test.com / Admin@123 and friends\n"
            "python main.py                 # uvicorn on http://localhost:8000"
        ),
        _h("Step 4 — Frontend", 2),
        _code(
            "cd frontend\n"
            "echo 'NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1' > .env.local\n"
            "npm install\n"
            "npm run dev                    # http://localhost:3000"
        ),
        _h("Step 5 — Verify", 2),
        *_bullets(
            [
                "Open http://localhost:8000/health — expect {status: healthy, database: connected}",
                "Open http://localhost:8000/api/docs — Swagger UI",
                "Open http://localhost:3000/login — login as <b>admin1@test.com / Admin@123</b>",
                "Try the Aa text-size button bottom-right",
            ]
        ),
        _h("Seeded test accounts", 2),
        _header_table(
            ["Email", "Password", "Role"],
            [
                ["admin1@test.com", "Admin@123", "ADMIN"],
                ["admin2@test.com", "Admin@123", "ADMIN"],
                ["dr.smith@test.com", "Doctor@123", "PSYCHOLOGIST"],
                ["dr.patel@test.com", "Doctor@123", "PSYCHOLOGIST"],
                ["dr.williams@test.com", "Doctor@123", "PSYCHOLOGIST"],
                ["parent1@test.com → parent4@test.com", "Parent@123", "PARENT"],
            ],
            col_widths=[66 * mm, 38 * mm, 40 * mm],
        ),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Section 11 — External services
# ─────────────────────────────────────────────────────────────────────
def section_external_services():
    story = [
        PageBreak(),
        _h("11. External Services", 1),
        _h("PostgreSQL (Neon in production, native in dev)", 2),
        *_bullets(
            [
                "Provides: primary datastore for all application state",
                "Provision: neon.tech → new project → copy connection string",
                "Env var: <font face='Courier'>DATABASE_URL</font> (asyncpg driver is derived automatically)",
                "Important: <font face='Courier'>pool_pre_ping=True, pool_recycle=300</font> are already set for Neon's idle-connection closure",
            ]
        ),
        _h("Groq (LLM provider, production)", 2),
        *_bullets(
            [
                "Provides: fast llama-3.1-8b-instant inference over OpenAI-compatible API",
                "Provision: console.groq.com → API keys",
                "Env vars: <font face='Courier'>USE_GROQ=true, GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL</font>",
                "Used by: report generation, acknowledgements, unified insights",
            ]
        ),
        _h("OpenAI (LLM provider, optional)", 2),
        *_bullets(
            [
                "Drop-in alternative to Groq (same code path). Set <font face='Courier'>USE_OPENAI=true, OPENAI_API_KEY</font>, pick model.",
                "Default model: gpt-4o-mini",
            ]
        ),
        _h("Ollama (LLM provider, local dev)", 2),
        *_bullets(
            [
                "Local-only LLM runtime. <font face='Courier'>ollama pull qwen2.5:3b</font> before first run.",
                "Env vars: <font face='Courier'>USE_LOCAL_LLM=true, OLLAMA_BASE_URL=http://localhost:11434</font>",
            ]
        ),
        _h("Brevo transactional email", 2),
        *_bullets(
            [
                "Provides: outbound email delivery for magic-link invites",
                "Provision: brevo.com → SMTP & API → API keys → verified sender email",
                "Env vars: <font face='Courier'>BREVO_API_KEY, EMAIL_FROM_NAME, EMAIL_FROM_ADDRESS</font>",
                "Fallback: if BREVO_API_KEY is missing, <font face='Courier'>app/utils/email.py</font> logs emails to stdout instead of sending",
            ]
        ),
        _h("MinIO / S3 (object storage, optional)", 2),
        *_bullets(
            [
                "Provides: IQ test PDFs, generated reports, temp files",
                "Buckets: iq-tests, reports, temp",
                "Dev: docker-compose minio service on :9000 (console :9001)",
                "Production: can be swapped for AWS S3 by pointing <font face='Courier'>MINIO_ENDPOINT</font> at S3 (boto3 handles it)",
            ]
        ),
        _h("Tesseract OCR (system binary)", 2),
        *_bullets(
            [
                "Bundled into Dockerfile via <font face='Courier'>apt-get install tesseract-ocr poppler-utils</font>",
                "On Windows dev: install from UB-Mannheim build and set <font face='Courier'>TESSERACT_PATH</font>",
                "Used by: <font face='Courier'>app/services/pdf_extractor.py</font> for IQ test parsing",
            ]
        ),
        _h("Vercel (frontend hosting)", 2),
        *_bullets(
            [
                "Provides: static Next.js build + serverless runtime",
                "One env var required: <font face='Courier'>NEXT_PUBLIC_API_URL</font>",
                "Deploy trigger: git push to main (watch branch can be changed in dashboard)",
            ]
        ),
        _h("Railway (backend hosting)", 2),
        *_bullets(
            [
                "Provides: Docker-based runtime, $PORT injection, TLS termination",
                "Deploy trigger: git push; alternatively <font face='Courier'>railway up -d</font> from backend/",
                "Logs: dashboard Logs tab (stream), or <font face='Courier'>railway logs -f</font>",
            ]
        ),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Section 12 — Security
# ─────────────────────────────────────────────────────────────────────
def section_security():
    story = [
        PageBreak(),
        _h("12. Security &amp; Operations", 1),
        _h("Authentication", 2),
        *_bullets(
            [
                "JWT <b>HS256</b> with <font face='Courier'>SECRET_KEY</font> (must be ≥32 chars, random, rotated on breach)",
                "Token expiry 24h (<font face='Courier'>ACCESS_TOKEN_EXPIRE_MINUTES=1440</font>)",
                "Passwords hashed with <b>bcrypt</b> via passlib (salt per password)",
                "<font face='Courier'>password_hash</font> nullable → invited users only set password via magic link",
                "Magic links expire after 48 hours (<font face='Courier'>MAGIC_LINK_EXPIRY_HOURS</font>)",
                "Tokens are single-use: <font face='Courier'>used_at</font> is set on redemption",
            ]
        ),
        _h("CORS", 2),
        *_bullets(
            [
                "Configured in <font face='Courier'>main.py</font> from <font face='Courier'>CORS_ORIGINS</font> (comma-separated)",
                "<font face='Courier'>allow_credentials=True</font>, all methods, all headers",
                "<b>Production must set CORS_ORIGINS to the Vercel URL only</b> — leaving localhost in CORS_ORIGINS is not a security risk but adds noise",
            ]
        ),
        _h("Database safety", 2),
        *_bullets(
            [
                "<font face='Courier'>pool_pre_ping=True</font> — required for Neon's idle closure",
                "<font face='Courier'>pool_recycle=300</font> — proactively renews connections",
                "<font face='Courier'>pool_size=5, max_overflow=2</font> — conservative to fit Neon's limits",
                "All routes wrap work in a single <font face='Courier'>get_db</font> session; failure rolls back, success commits",
            ]
        ),
        _h("Rate limiting", 2),
        _p(
            "<b>Not currently implemented.</b> For production, add "
            "<font face='Courier'>slowapi</font> or an upstream WAF limiter — especially on "
            "<font face='Courier'>/auth/login</font> and <font face='Courier'>/auth/magic-login</font>."
        ),
        _h("Logging &amp; monitoring", 2),
        *_bullets(
            [
                "Stdlib <font face='Courier'>logging</font> at INFO level, streamed to stdout (Railway collects)",
                "Global exception handler logs full traceback + returns JSON (includes error detail only if DEBUG_MODE=true)",
                "Health endpoint: <font face='Courier'>GET /health</font> → {status, database, llm, timestamp}",
                "No Prometheus/metrics today; consider adding Railway's built-in metrics dashboard",
            ]
        ),
        _h("Common gotchas", 2),
        *_bullets(
            [
                "<b>Railway</b>: run <font face='Courier'>railway up</font> from <font face='Courier'>backend/</font>, not project root — Railpack cannot find the Dockerfile otherwise.",
                "<b>Email not sending</b>: check <font face='Courier'>BREVO_API_KEY</font>. If unset, the code logs '[EMAIL MODE: DEV] Would send email…' — nothing leaves the server.",
                "<b>Magic link points to localhost in prod emails</b>: <font face='Courier'>FRONTEND_URL</font> on Railway must be set to the Vercel URL.",
                "<b>Admin creation</b>: default seeded admin is <font face='Courier'>admin1@test.com / Admin@123</font> — change on first deploy.",
                "<b>LF/CRLF</b>: git on Windows may auto-convert shell scripts — consider a .gitattributes entry for *.sh.",
                "<b>Chat session 'already completed'</b>: the /hybrid-chat/sessions/{id}/complete endpoint is now idempotent; if the chat session was auto-marked complete by the message handler and the frontend still calls /complete, finalization proceeds without error.",
                "<b>Neon connection pooling</b>: do NOT lower pool_pre_ping or pool_recycle without testing — idle drops will silently 500 routes.",
                "<b>FastAPI route ordering</b>: static routes before parameterized ones — already correct in main.py's include_router calls.",
            ]
        ),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Section 13 — Operational runbook
# ─────────────────────────────────────────────────────────────────────
def section_runbook():
    story = [
        PageBreak(),
        _h("13. Operational Runbook", 1),
        _h("13.1 Backend is down", 2),
        *_bullets(
            [
                "Check Railway dashboard → service → Deployments (any crashes?)",
                "<font face='Courier'>railway logs -f</font> — look for startup errors",
                "<font face='Courier'>curl https://backend/health</font> — expect 200 JSON",
                "Common: Neon idle killed the pool → should self-heal; if not, restart the Railway service",
                "Common: SECRET_KEY missing → Uvicorn logs 'ValidationError' on startup",
                "Common: DATABASE_URL wrong → Uvicorn exits with asyncpg InvalidAuthorization",
            ]
        ),
        _h("13.2 Frontend is down", 2),
        *_bullets(
            [
                "Check Vercel dashboard → deployments → failed build?",
                "Most common: TypeScript error after a push — Vercel build log shows the file + line",
                "Health: visit /login and inspect devtools Network tab → API calls should 200 from the Railway URL",
                "If API calls go to localhost:8000, NEXT_PUBLIC_API_URL wasn't set in Vercel → fix + redeploy",
            ]
        ),
        _h("13.3 Parent can't log in", 2),
        *_bullets(
            [
                "Ask for the magic link URL they have",
                "Admin dashboard → Assignments → find their row → <b>Resend Link</b> (copies to clipboard, re-emails)",
                "If the link is still rejected: check expires_at in magic_link_tokens; re-issue via Resend",
                "If the parent already set a password: point them to /login with email + that password",
            ]
        ),
        _h("13.4 Reports not generating", 2),
        *_bullets(
            [
                "Check backend logs for AIGenerationJob failures",
                "<b>LLM service error</b>: job.status=failed with error_message — verify GROQ_API_KEY / USE_GROQ=true and model availability",
                "Psychologist workspace retries: use the Regenerate button in the card",
                "Fallback: psychologist can edit sections manually via MarkdownEditor and POST /psychologist-reports/reports/{id}/finalize",
            ]
        ),
        _h("13.5 Database migration needed", 2),
        _p(
            "The app auto-creates tables via "
            "<font face='Courier'>Base.metadata.create_all</font> in the lifespan hook. "
            "For additive changes (new tables / columns) a restart is enough. "
            "For destructive changes (drop/alter column) run a hand-crafted SQL "
            "script via <font face='Courier'>python run_migration.py path/to/migration.sql</font> "
            "on the production DB first. Alembic is installed but no migration chain exists."
        ),
        _h("13.6 Rotating secrets", 2),
        *_bullets(
            [
                "<b>SECRET_KEY rotation</b> will invalidate all existing JWTs — every user must re-login",
                "<b>DATABASE_URL rotation</b> (password change): update in Railway dashboard → service restarts on save",
                "<b>GROQ_API_KEY rotation</b>: update in Railway dashboard",
                "<b>BREVO_API_KEY rotation</b>: update in Railway dashboard; no app restart required",
            ]
        ),
        _h("13.7 Scaling considerations", 2),
        *_bullets(
            [
                "Backend is stateless → Railway can run N replicas if plan allows",
                "Neon scales the DB tier independently",
                "LLM cost scales linearly with report volume — Groq is cheapest today",
                "Brevo free tier: 300 emails/day — monitor usage if parent volume grows",
                "MinIO: bind to persistent volume if enabled in production",
            ]
        ),
    ]
    return story


# ─────────────────────────────────────────────────────────────────────
# Build doc
# ─────────────────────────────────────────────────────────────────────
def build():
    doc = HandoffDoc(str(OUTPUT_PDF))

    story = []
    story.extend(cover_page())

    # Use content template for the rest
    story.append(Paragraph("<a name='toc'/>", STYLES["body"]))

    story.extend(section_overview())
    story.extend(section_tech_stack())
    story.extend(section_directory())
    story.extend(section_env_vars())
    story.extend(section_database())
    story.extend(section_api_endpoints())
    story.extend(section_workflows())
    story.extend(section_frontend_routing())
    story.extend(section_deployment())
    story.extend(section_local_dev())
    story.extend(section_external_services())
    story.extend(section_security())
    story.extend(section_runbook())

    # Closing page
    story.extend(
        [
            PageBreak(),
            Spacer(1, 60 * mm),
            _p("End of document", "title"),
            Spacer(1, 8 * mm),
            _p(
                "For questions, contact the engineering lead. "
                "Keep this document version-controlled alongside the repo.",
                "cover_meta",
            ),
        ]
    )

    # Switch to content template after cover
    def first_page_template(canvas, doc):
        doc.handle_pageBegin()

    doc.build(story)
    print(f"[OK] Wrote {OUTPUT_PDF}")


if __name__ == "__main__":
    build()
