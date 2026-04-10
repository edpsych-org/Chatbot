"""
Generate a "run it locally from scratch" setup guide PDF.

Shares styling with generate_devops_handoff.py but is laser-focused on
getting a brand-new developer from "git clone" to "logged in as admin
on localhost:3000" with zero cloud dependencies.

Run from backend/ with the venv active:
    python generate_local_setup_guide.py

Output: ../EdPsych_Local_Setup_Guide.pdf
"""
from __future__ import annotations

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
)


# ─────────────────────────────────────────────────────────────────────
# Ed Psych brand colors
# ─────────────────────────────────────────────────────────────────────
BRAND_TEAL = colors.HexColor("#00acb6")
BRAND_TEAL_DARK = colors.HexColor("#0c888e")
BRAND_RED = colors.HexColor("#e61844")
INK = colors.HexColor("#333333")
MUTED = colors.HexColor("#737373")
LINE = colors.HexColor("#dedede")
CARD_BG = colors.HexColor("#f4f4f4")
TEAL_TINT = colors.HexColor("#e6f7f8")
RED_TINT = colors.HexColor("#fdecec")

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PDF = BASE_DIR / "EdPsych_Local_Setup_Guide.pdf"


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
    s["note"] = ParagraphStyle(
        "Note",
        parent=_styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=BRAND_TEAL_DARK,
        backColor=TEAL_TINT,
        borderColor=BRAND_TEAL,
        borderWidth=0.5,
        borderPadding=6,
        leftIndent=4,
        rightIndent=4,
        spaceAfter=6,
    )
    s["warn"] = ParagraphStyle(
        "Warn",
        parent=_styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=BRAND_RED,
        backColor=RED_TINT,
        borderColor=BRAND_RED,
        borderWidth=0.5,
        borderPadding=6,
        leftIndent=4,
        rightIndent=4,
        spaceAfter=6,
    )
    s["cover_meta"] = ParagraphStyle(
        "CoverMeta",
        parent=s["body"],
        fontSize=10,
        textColor=MUTED,
        alignment=1,
        leading=14,
    )
    return s


STYLES = _make_styles()


def _p(text, style="body"):
    return Paragraph(text, STYLES[style])


def _h(text, level):
    return Paragraph(text, STYLES[f"h{level}"])


def _bullets(items: Iterable[str]):
    return [Paragraph(f"• {t}", STYLES["bullet"]) for t in items]


def _code(text: str):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\n", "<br/>")
    return Paragraph(text, STYLES["code"])


def _note(text: str):
    return Paragraph(f"<b>NOTE:</b> {text}", STYLES["note"])


def _warn(text: str):
    return Paragraph(f"<b>WARNING:</b> {text}", STYLES["warn"])


def _header_table(header, rows, col_widths):
    data = [[Paragraph(f"<b>{h}</b>", STYLES["body"]) for h in header]] + [
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
# Page template
# ─────────────────────────────────────────────────────────────────────
class SetupDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=22 * mm,
            bottomMargin=20 * mm,
            title="EdPsych Local Setup Guide",
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
            A4[0] - 20 * mm, A4[1] - 11 * mm, "Local Setup Guide"
        )
        canvas.setFillColor(BRAND_RED)
        canvas.rect(0, 0, A4[0], 6 * mm, fill=1, stroke=0)
        canvas.restoreState()

    def _page_chrome(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(BRAND_TEAL)
        canvas.rect(0, A4[1] - 12 * mm, A4[0], 12 * mm, fill=1, stroke=0)
        canvas.setFont("Times-Roman", 10)
        canvas.setFillColor(colors.white)
        canvas.drawString(20 * mm, A4[1] - 8 * mm, "The Ed Psych Practice")
        canvas.drawRightString(
            A4[0] - 20 * mm, A4[1] - 8 * mm, "Local Setup Guide"
        )
        canvas.setStrokeColor(BRAND_RED)
        canvas.setLineWidth(0.8)
        canvas.line(20 * mm, 12 * mm, A4[0] - 20 * mm, 12 * mm)
        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(20 * mm, 7 * mm, "Run on your machine — no cloud required")
        canvas.drawRightString(A4[0] - 20 * mm, 7 * mm, f"Page {doc.page}")
        canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────
# Cover
# ─────────────────────────────────────────────────────────────────────
def cover_page():
    return [
        Spacer(1, 60 * mm),
        _p("EdPsych AI Prototype", "title"),
        _p(
            "Local development setup — zero to running on your own machine",
            "subtitle",
        ),
        Spacer(1, 8 * mm),
        _p("A step-by-step guide for developers", "cover_meta"),
        Spacer(1, 6 * mm),
        _p(
            "Runs entirely on your laptop: no Railway, no Vercel, no Neon.",
            "cover_meta",
        ),
        _p(
            "PostgreSQL local + Python venv + Node dev server.",
            "cover_meta",
        ),
        Spacer(1, 40 * mm),
        _p(
            "Backend: http://localhost:8000 &nbsp;|&nbsp; Frontend: http://localhost:3000",
            "cover_meta",
        ),
        _p(
            "Target audience: engineers onboarding onto the project",
            "cover_meta",
        ),
        PageBreak(),
    ]


# ─────────────────────────────────────────────────────────────────────
# Sections
# ─────────────────────────────────────────────────────────────────────
def section_what_youll_run():
    return [
        _h("1. What You Will Run", 1),
        _p(
            "This guide gets the whole stack running on one machine with nothing "
            "in the cloud. When you're done, you'll have:"
        ),
        *_bullets(
            [
                "<b>PostgreSQL 18</b> on localhost:5432 holding the <font face='Courier'>edpsych_db</font> database",
                "<b>FastAPI backend</b> via uvicorn on <font face='Courier'>http://localhost:8000</font>",
                "<b>Next.js 14 frontend</b> via <font face='Courier'>next dev</font> on <font face='Courier'>http://localhost:3000</font>",
                "<b>Groq</b> as the LLM provider (small cloud API call, no local GPU needed) OR Ollama if you prefer fully offline",
                "<b>Seeded test users</b> — admin, psychologists, parents — ready to log in",
            ]
        ),
        _h("Architecture on a single machine", 2),
        _code(
            "+-------------------+\n"
            "|   Chrome browser  |\n"
            "+--------+----------+\n"
            "         |\n"
            "         | http://localhost:3000\n"
            "         v\n"
            "+-------------------+      http://localhost:8000/api/v1\n"
            "| Next.js dev server| ----------------------------------+\n"
            "| (next dev, 3000)  |                                    |\n"
            "+-------------------+                                    v\n"
            "                                          +-------------------------+\n"
            "                                          |  FastAPI / uvicorn 8000 |\n"
            "                                          |  python main.py         |\n"
            "                                          +------------+------------+\n"
            "                                                       |\n"
            "                   +-----------------------------------+-------------+\n"
            "                   |                                   |             |\n"
            "                   v                                   v             v\n"
            "          +-----------------+                   +-------------+  +---------+\n"
            "          | PostgreSQL 5432 |                   | Groq cloud  |  | Brevo   |\n"
            "          | edpsych_db      |                   | LLM API     |  | (email, |\n"
            "          +-----------------+                   +-------------+  | optional)|\n"
            "                                                                 +---------+"
        ),
        _note(
            "Email sending is optional in local dev. If <font face='Courier'>BREVO_API_KEY</font> is "
            "missing, the backend logs magic-link emails to the terminal instead "
            "of sending them. You can copy the URL from the log and open it in your "
            "browser to simulate being a parent."
        ),
    ]


def section_prerequisites():
    return [
        PageBreak(),
        _h("2. Prerequisites", 1),
        _p("Install these once. Versions are minimums."),
        _header_table(
            ["Tool", "Version", "Why", "Where to get it"],
            [
                ["Python", "3.10+", "Backend runtime", "python.org/downloads"],
                ["Node.js", "20+", "Frontend dev server + build", "nodejs.org"],
                ["PostgreSQL", "16 or 18", "Database", "postgresql.org/download"],
                ["Git", "any", "Clone the repo", "git-scm.com"],
                [
                    "Tesseract OCR",
                    "5+",
                    "IQ PDF extraction (optional if you won't upload PDFs locally)",
                    "github.com/UB-Mannheim/tesseract (Windows)",
                ],
                ["Ollama", "any", "Optional: fully offline LLM", "ollama.com"],
            ],
            col_widths=[28 * mm, 20 * mm, 62 * mm, 60 * mm],
        ),
        _h("Check your installs", 2),
        _code(
            "python --version       # should print 3.10.x or newer\n"
            "node --version         # should print v20.x or newer\n"
            "npm --version\n"
            "psql --version         # on Windows: 'C:/Program Files/PostgreSQL/18/bin/psql.exe' --version\n"
            "git --version"
        ),
        _warn(
            "On Windows, the PostgreSQL installer does not add psql to your PATH "
            "by default. Either add <font face='Courier'>C:\\Program Files\\PostgreSQL\\18\\bin</font> "
            "to PATH, or run psql using the full path shown above."
        ),
    ]


def section_clone():
    return [
        PageBreak(),
        _h("3. Clone the Repository", 1),
        _p("Pick a working directory and clone:"),
        _code(
            "cd d:/\n"
            "mkdir \"GEN AI\"\n"
            "cd \"GEN AI\"\n"
            "git clone https://github.com/akshaytoni99/edpsych-chatbot.git edpsych-production-prototype\n"
            "cd edpsych-production-prototype"
        ),
        _p(
            "From here on, <b>all paths in this guide are relative to "
            "<font face='Courier'>edpsych-production-prototype/</font></b> unless stated otherwise."
        ),
    ]


def section_postgres():
    return [
        PageBreak(),
        _h("4. PostgreSQL Database", 1),
        _p(
            "You need a Postgres database named <font face='Courier'>edpsych_db</font> with a "
            "dedicated user the backend can connect as."
        ),
        _h("4.1 Install PostgreSQL", 2),
        *_bullets(
            [
                "<b>Windows:</b> Download PostgreSQL 18 from postgresql.org → run installer → remember the password you set for the <font face='Courier'>postgres</font> superuser. Close the 'Stack Builder' popup at the end (you don't need it).",
                "<b>macOS (Homebrew):</b> <font face='Courier'>brew install postgresql@16 &amp;&amp; brew services start postgresql@16</font>",
                "<b>Linux (Ubuntu):</b> <font face='Courier'>sudo apt-get install -y postgresql-16 &amp;&amp; sudo systemctl start postgresql</font>",
            ]
        ),
        _h("4.2 Create the database + user", 2),
        _p(
            "Open <font face='Courier'>psql</font> as the superuser and run three SQL statements. "
            "The backend already expects these exact credentials."
        ),
        _code(
            "# Windows (using full path to psql):\n"
            "# \"C:/Program Files/PostgreSQL/18/bin/psql.exe\" -U postgres -h localhost\n"
            "\n"
            "# macOS / Linux:\n"
            "# psql -U postgres -h localhost\n"
            "\n"
            "# Inside psql, run these three commands:\n"
            "CREATE USER edpsych WITH PASSWORD 'edpsych_secure_password';\n"
            "CREATE DATABASE edpsych_db OWNER edpsych;\n"
            "GRANT ALL PRIVILEGES ON DATABASE edpsych_db TO edpsych;\n"
            "\\q"
        ),
        _h("4.3 Verify you can connect as edpsych", 2),
        _code(
            "# Windows:\n"
            "PGPASSWORD=edpsych_secure_password \\\n"
            "  \"C:/Program Files/PostgreSQL/18/bin/psql.exe\" \\\n"
            "  -U edpsych -h localhost -d edpsych_db -c \"SELECT version();\"\n"
            "\n"
            "# macOS/Linux:\n"
            "PGPASSWORD=edpsych_secure_password psql -U edpsych -h localhost -d edpsych_db -c \"SELECT version();\""
        ),
        _note(
            "If you see <i>'PostgreSQL 18.x on x86_64'</i> printed back, the database "
            "is ready. If you see a connection refused error, Postgres may not be "
            "running — start it through Services (Windows) or "
            "<font face='Courier'>brew services list</font> / "
            "<font face='Courier'>systemctl status postgresql</font>."
        ),
    ]


def section_env():
    return [
        PageBreak(),
        _h("5. Root .env File", 1),
        _p(
            "The backend reads <font face='Courier'>../.env</font> (project root) via "
            "Pydantic Settings. Copy the example and tweak the few fields that matter "
            "for local dev."
        ),
        _code(
            "# From the project root:\n"
            "cp .env.example .env\n"
            "\n"
            "# Then open .env in your editor and make sure these are set:"
        ),
        _code(
            "# ==================== DATABASE ====================\n"
            "DATABASE_URL=postgresql://edpsych:edpsych_secure_password@localhost:5432/edpsych_db\n"
            "\n"
            "# ==================== JWT ====================\n"
            "SECRET_KEY=replace-this-with-a-random-32-char-hex-string\n"
            "ACCESS_TOKEN_EXPIRE_MINUTES=1440\n"
            "MAGIC_LINK_EXPIRY_HOURS=48\n"
            "\n"
            "# ==================== CORS + FRONTEND URL ====================\n"
            "CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000\n"
            "FRONTEND_URL=http://localhost:3000\n"
            "\n"
            "# ==================== LLM (pick one) ====================\n"
            "# Option A — Groq (recommended, small API call):\n"
            "USE_GROQ=true\n"
            "GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n"
            "GROQ_MODEL=llama-3.1-8b-instant\n"
            "\n"
            "# Option B — Ollama (fully offline):\n"
            "# USE_GROQ=false\n"
            "# USE_LOCAL_LLM=true\n"
            "# OLLAMA_BASE_URL=http://localhost:11434\n"
            "# OLLAMA_MODEL=qwen2.5:3b\n"
            "\n"
            "# ==================== EMAIL (optional) ====================\n"
            "# Leave blank to log magic links to terminal instead of sending:\n"
            "BREVO_API_KEY=\n"
            "EMAIL_FROM_NAME=The Ed Psych Practice\n"
            "EMAIL_FROM_ADDRESS=akshaytoni99@gmail.com\n"
            "\n"
            "# ==================== DEV ====================\n"
            "DEBUG_MODE=true"
        ),
        _h("Generating a good SECRET_KEY", 2),
        _code(
            "# macOS/Linux:\n"
            "openssl rand -hex 32\n"
            "\n"
            "# Windows (PowerShell):\n"
            "[Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))\n"
            "\n"
            "# Or any 32+ character random string will work in dev"
        ),
        _warn(
            "Never commit your .env file. It's already in <font face='Courier'>.gitignore</font>. "
            "If you don't have a Groq key, Option B (Ollama) works offline — just run "
            "<font face='Courier'>ollama pull qwen2.5:3b</font> first."
        ),
    ]


def section_backend():
    return [
        PageBreak(),
        _h("6. Backend Setup", 1),
        _h("6.1 Create a Python virtual environment", 2),
        _code(
            "cd backend\n"
            "python -m venv venv\n"
            "\n"
            "# Activate it:\n"
            "# Windows (bash / git-bash):\n"
            "source venv/Scripts/activate\n"
            "# Windows (PowerShell):\n"
            "# venv\\Scripts\\Activate.ps1\n"
            "# macOS/Linux:\n"
            "# source venv/bin/activate"
        ),
        _h("6.2 Install Python dependencies", 2),
        _code(
            "pip install --upgrade pip\n"
            "pip install -r requirements.txt"
        ),
        _note(
            "First install takes 3-5 minutes. It pulls asyncpg, reportlab, "
            "PyMuPDF, and a handful of other wheels. On Windows, PyMuPDF ships as "
            "a prebuilt wheel so you don't need a C++ compiler."
        ),
        _h("6.3 Seed test users and sample data", 2),
        _p(
            "These scripts are <b>idempotent</b> — re-running them is safe, existing "
            "rows are skipped."
        ),
        _code(
            "python seed_test_users.py      # creates admin, psychologist, parent accounts\n"
            "# Tables are created automatically on first backend start."
        ),
        _h("6.4 Start the backend", 2),
        _code(
            "python main.py"
        ),
        _p("You should see logs like:"),
        _code(
            "INFO:     Started server process [12345]\n"
            "INFO:     Waiting for application startup.\n"
            "2026-04-10 10:59:18,...  Starting EdPsych AI Backend...\n"
            "2026-04-10 10:59:18,...  Database: localhost:5432\n"
            "2026-04-10 10:59:18,...  LLM: Groq (llama-3.1-8b-instant)\n"
            "2026-04-10 10:59:18,...  Database tables created/verified\n"
            "INFO:     Application startup complete.\n"
            "INFO:     Uvicorn running on http://0.0.0.0:8000"
        ),
        _h("6.5 Verify it's alive", 2),
        _code(
            "# In another terminal:\n"
            "curl http://localhost:8000/health\n"
            "\n"
            "# Expected:\n"
            "# {\"status\":\"healthy\",\"database\":\"connected\",\"llm\":\"groq\",\"timestamp\":1712810000.123}\n"
            "\n"
            "# Swagger UI (interactive API docs):\n"
            "# http://localhost:8000/api/docs"
        ),
        _warn(
            "Keep this terminal open — the backend must stay running. Use a second "
            "terminal for the frontend in the next step."
        ),
    ]


def section_frontend():
    return [
        PageBreak(),
        _h("7. Frontend Setup", 1),
        _p("Open a <b>new terminal</b>. Leave the backend running in the other one."),
        _h("7.1 Create frontend/.env.local", 2),
        _code(
            "cd frontend\n"
            "echo 'NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1' > .env.local"
        ),
        _note(
            "This file is <b>not</b> committed to git. It tells Next.js where to "
            "reach the backend. On Vercel this same variable is set in the dashboard "
            "to point at the Railway URL."
        ),
        _h("7.2 Install Node dependencies", 2),
        _code(
            "npm install"
        ),
        _p(
            "Takes 2-4 minutes first time — pulls Next.js, React, Tailwind, axios, "
            "react-hook-form, zod, zustand and their transitive deps."
        ),
        _h("7.3 Start the dev server", 2),
        _code(
            "npm run dev"
        ),
        _p("You should see:"),
        _code(
            "> edpsych-ai-frontend@0.1.0 dev\n"
            "> next dev\n"
            "\n"
            "  ▲ Next.js 14.2.0\n"
            "  - Local:        http://localhost:3000\n"
            "  - Environments: .env.local\n"
            "\n"
            " ✓ Starting...\n"
            " ✓ Ready in 14.3s\n"
            " ✓ Compiled / in 1.7s"
        ),
        _h("7.4 Open the app", 2),
        _p(
            "Navigate to <b>http://localhost:3000</b> in your browser. "
            "You should see the teal Ed Psych navigation bar, the cherry-blossom "
            "hero on the left, and the sign-in form on the right."
        ),
    ]


def section_test_accounts():
    return [
        PageBreak(),
        _h("8. Test Accounts", 1),
        _p(
            "<font face='Courier'>seed_test_users.py</font> creates these accounts. "
            "All passwords are listed below. Change them on any real deployment."
        ),
        _header_table(
            ["Email", "Password", "Role", "Use for"],
            [
                [
                    "admin1@test.com",
                    "Admin@123",
                    "ADMIN",
                    "Full control — create users, students, assignments, resend magic links",
                ],
                [
                    "admin2@test.com",
                    "Admin@123",
                    "ADMIN",
                    "Secondary admin",
                ],
                [
                    "dr.smith@test.com",
                    "Doctor@123",
                    "PSYCHOLOGIST",
                    "Read-only student list, report workspace, report generation",
                ],
                [
                    "dr.patel@test.com",
                    "Doctor@123",
                    "PSYCHOLOGIST",
                    "Secondary psychologist",
                ],
                [
                    "dr.williams@test.com",
                    "Doctor@123",
                    "PSYCHOLOGIST",
                    "Tertiary psychologist",
                ],
                [
                    "parent1@test.com … parent4@test.com",
                    "Parent@123",
                    "PARENT",
                    "Simulate a parent filling out a child's assessment",
                ],
            ],
            col_widths=[56 * mm, 28 * mm, 26 * mm, 56 * mm],
        ),
        _note(
            "The canonical dev admin is <b>admin1@test.com / Admin@123</b>. "
            "After logging in, you'll land on <font face='Courier'>/admin/dashboard</font> "
            "with the full teal/red Ed Psych theme."
        ),
    ]


def section_local_workflows():
    return [
        PageBreak(),
        _h("9. Try the Workflows Locally", 1),
        _p(
            "Once both servers are running and you're logged in as admin, try these "
            "end-to-end flows to verify everything works."
        ),
        _h("9.1 Create a student and assign an assessment", 2),
        *_bullets(
            [
                "Log in as admin1@test.com / Admin@123 → lands on /admin/dashboard",
                "Click the <b>Students</b> tab → <b>Create Student</b>",
                "Fill in the form (first/last name, year group, parent email + name) → Save",
                "Click the <b>Assignments</b> tab → <b>New Assignment</b>",
                "Pick the student and assigned-to parent → Save",
                "A magic link is created in the database. If BREVO_API_KEY is set, an email is sent; otherwise watch the backend terminal for a log line like <font face='Courier'>[EMAIL MODE: DEV] Would send email to ...</font> with the link URL.",
            ]
        ),
        _h("9.2 Simulate the parent journey", 2),
        *_bullets(
            [
                "Copy the magic link URL from the backend log (or use the admin dashboard's <b>Resend Link</b> button which copies it to your clipboard)",
                "Open a <b>private / incognito window</b> so you are not using the admin session",
                "Paste the magic link URL — you should see the welcome + password setup screen",
                "Set a password → you'll be redirected to /chat/[assignmentId]",
                "Work through the chatbot questions (MCQs and free-text)",
                "At the end you'll see 'Thank you so much for completing this assessment!'",
            ]
        ),
        _h("9.3 Review as a psychologist", 2),
        *_bullets(
            [
                "Log out, or open another incognito window",
                "Log in as dr.smith@test.com / Doctor@123 → /psychologist/dashboard",
                "<b>Students</b> tab — you should see the student with status <b>COMPLETED</b> and 100% progress",
                "Click <b>Reports Workspace</b> on that student row → /student/[id]/workspace",
                "Use the Generate buttons on each card (background summary, cognitive report, unified insights) to run the LLM pipeline",
                "Edit any section with the MarkdownEditor and save",
            ]
        ),
        _h("9.4 Accessibility text size", 2),
        *_bullets(
            [
                "On any page, click the <b>Aa Text size</b> button in the bottom-right corner",
                "Try 100% / 115% / 130% / 150% — entire layout should scale proportionally",
                "Your choice is persisted in localStorage and survives reloads",
            ]
        ),
    ]


def section_directory():
    return [
        PageBreak(),
        _h("10. Directory Quick Reference", 1),
        _p("Only the files you'll actually touch."),
        _h("Backend files", 2),
        _code(
            "backend/\n"
            "├── main.py                     # FastAPI app + lifespan (auto-creates tables)\n"
            "├── requirements.txt            # Python deps — pip install -r\n"
            "├── seed_test_users.py          # Creates admin + psych + parent accounts\n"
            "├── seed_questions.py           # Populates chatbot question bank\n"
            "├── reset_database.py           # DROP + CREATE everything (dev only!)\n"
            "├── app/\n"
            "│   ├── core/\n"
            "│   │   ├── config.py           # Pydantic Settings — reads ../.env\n"
            "│   │   ├── database.py         # Async SQLAlchemy engine\n"
            "│   │   └── security.py         # JWT create/verify, password hashing\n"
            "│   ├── api/                    # One file per router (auth, admin, ...)\n"
            "│   ├── models/                 # SQLAlchemy models (one per table)\n"
            "│   ├── services/\n"
            "│   │   ├── local_llm.py        # Groq/OpenAI/Ollama abstraction\n"
            "│   │   └── pdf_extractor.py    # Tesseract OCR for IQ PDFs\n"
            "│   └── utils/\n"
            "│       ├── email.py            # Brevo sender + dev log fallback\n"
            "│       └── magic_link.py       # Magic link create/verify\n"
            "└── flows/\n"
            "    └── parent_assessment_v1.json   # Hybrid chat flow definition"
        ),
        _h("Frontend files", 2),
        _code(
            "frontend/\n"
            "├── package.json                # npm scripts: dev / build / start / lint\n"
            "├── tailwind.config.js          # Ed Psych teal/red palette + Average/Nunito fonts\n"
            "├── .env.local                  # NEXT_PUBLIC_API_URL (git-ignored)\n"
            "├── lib/api.ts                  # API_BASE resolver\n"
            "├── public/\n"
            "│   ├── font-scale-boot.js      # Hydrates text size before React\n"
            "│   └── images/cherry-tree.png  # Decorative hero asset\n"
            "├── components/\n"
            "│   ├── AccessibilityMenu.tsx   # Floating Aa button\n"
            "│   └── ConfirmModal.tsx        # Reusable confirm dialog\n"
            "├── app/                        # App Router pages\n"
            "│   ├── layout.tsx              # Fonts, global chrome, menu mount\n"
            "│   ├── globals.css             # Theme + accessibility scale rules\n"
            "│   ├── login/                  # /login\n"
            "│   ├── admin/dashboard/        # /admin/dashboard\n"
            "│   ├── psychologist/dashboard/ # /psychologist/dashboard\n"
            "│   ├── chat/[assignmentId]/    # /chat/...\n"
            "│   ├── auth/magic/[token]/     # Magic link landing\n"
            "│   └── student/[id]/workspace/ # Psychologist report workspace\n"
            "└── src/components/\n"
            "    ├── chat/*.tsx              # HybridChat, MessageBubble, ChatInput...\n"
            "    ├── workspace/*.tsx         # Report card editors\n"
            "    └── admin/*.tsx             # Data Explorer, tables"
        ),
    ]


def section_commands():
    return [
        PageBreak(),
        _h("11. Command Cheat Sheet", 1),
        _h("Daily dev", 2),
        _code(
            "# Backend (terminal 1):\n"
            "cd backend\n"
            "source venv/Scripts/activate     # Windows bash\n"
            "python main.py                    # reload on file save\n"
            "\n"
            "# Frontend (terminal 2):\n"
            "cd frontend\n"
            "npm run dev\n"
            "\n"
            "# Database (terminal 3):\n"
            "PGPASSWORD=edpsych_secure_password psql -U edpsych -h localhost -d edpsych_db"
        ),
        _h("Common psql queries", 2),
        _code(
            "\\dt                                        -- list tables\n"
            "SELECT id, email, role FROM users;          -- all users\n"
            "SELECT * FROM assessment_assignments;       -- all assignments\n"
            "SELECT token, expires_at, used_at, purpose  -- check magic links\n"
            "  FROM magic_link_tokens ORDER BY created_at DESC LIMIT 5;\n"
            "SELECT id, status, completed_at FROM chat_sessions;"
        ),
        _h("Reset database (nuclear, dev only)", 2),
        _code(
            "cd backend\n"
            "python reset_database.py          # drops everything\n"
            "python main.py                     # recreates tables on startup\n"
            "python seed_test_users.py          # re-seed accounts"
        ),
        _h("Stop servers", 2),
        *_bullets(
            [
                "Terminal with backend: Ctrl+C",
                "Terminal with frontend: Ctrl+C",
                "Windows: if a port is stuck, find the PID with <font face='Courier'>netstat -ano | findstr :8000</font> then <font face='Courier'>taskkill //F //PID &lt;pid&gt;</font>",
            ]
        ),
        _h("Rebuild frontend for prod test", 2),
        _code(
            "cd frontend\n"
            "npm run build\n"
            "npm run start                     # prod-mode server on :3000\n"
            "                                   # useful before deploying"
        ),
    ]


def section_troubleshooting():
    return [
        PageBreak(),
        _h("12. Troubleshooting", 1),
        _h("Symptom: backend exits with 'ValidationError SECRET_KEY'", 2),
        _p(
            "You haven't set <font face='Courier'>SECRET_KEY</font> in <font face='Courier'>.env</font>. "
            "Generate one with the command in section 5 and try again."
        ),
        _h("Symptom: 'connection refused' or 'password authentication failed'", 2),
        *_bullets(
            [
                "PostgreSQL isn't running — start it",
                "Wrong password — re-verify <font face='Courier'>DATABASE_URL</font> in .env matches what you set in step 4.2",
                "User not created — re-run the CREATE USER / CREATE DATABASE statements",
            ]
        ),
        _h("Symptom: Next.js dev server on port 3000 already in use", 2),
        _code(
            "# Windows — find the PID on port 3000:\n"
            "netstat -ano | findstr :3000\n"
            "taskkill //F //PID <pid>\n"
            "\n"
            "# macOS/Linux:\n"
            "lsof -i :3000\n"
            "kill -9 <pid>"
        ),
        _h("Symptom: 'CORS error' in browser devtools", 2),
        *_bullets(
            [
                "Your <font face='Courier'>CORS_ORIGINS</font> env var must include the exact frontend URL, e.g. <font face='Courier'>http://localhost:3000</font>",
                "Restart the backend after editing .env — config is loaded at startup only",
            ]
        ),
        _h("Symptom: 'Module not found' on backend import", 2),
        _p(
            "Your venv isn't activated, or you installed requirements into the wrong "
            "interpreter. Run <font face='Courier'>pip show fastapi</font> — it should point "
            "into <font face='Courier'>backend/venv/...</font>. If not, reactivate the venv."
        ),
        _h("Symptom: Magic link email never arrives", 2),
        *_bullets(
            [
                "This is the default in local dev. Without BREVO_API_KEY, the backend logs the email instead of sending.",
                "Check the backend terminal for a line starting with <font face='Courier'>[EMAIL MODE: DEV] Would send email to ...</font> — the magic link URL is in the body.",
                "Or use the admin dashboard's <b>Resend Link</b> button — it copies the URL to your clipboard automatically.",
            ]
        ),
        _h("Symptom: 'ModuleNotFoundError: app.utils.flow_engine'", 2),
        _p(
            "Already patched. If you still see it after pulling the latest main, "
            "clear any stale <font face='Courier'>__pycache__</font> folders under backend/app/ "
            "and restart the backend."
        ),
        _h("Symptom: assessment completes but assignment stays ASSIGNED", 2),
        _p(
            "Already patched (the /hybrid-chat/sessions/{id}/complete endpoint is "
            "now idempotent). Restart the backend and complete the assessment again."
        ),
        _h("Symptom: 'data-font-scale' text still at same size", 2),
        *_bullets(
            [
                "Hard refresh the browser (Ctrl+Shift+R) — the boot script is cached",
                "Check that your components use rem-based Tailwind classes; hardcoded <font face='Courier'>text-[16px]</font> won't scale (all of them have been converted)",
            ]
        ),
        _h("Symptom: 'ECONNREFUSED' from frontend to backend", 2),
        *_bullets(
            [
                "Backend not running → start it in another terminal",
                "<font face='Courier'>NEXT_PUBLIC_API_URL</font> in frontend/.env.local is wrong — must include <font face='Courier'>/api/v1</font> or the resolver auto-appends it",
                "Restart <font face='Courier'>npm run dev</font> after editing .env.local — Next.js reads env vars only on start",
            ]
        ),
    ]


def section_next_steps():
    return [
        PageBreak(),
        _h("13. Next Steps", 1),
        *_bullets(
            [
                "Read the API docs interactively at <font face='Courier'>http://localhost:8000/api/docs</font> — Swagger UI lets you hit every endpoint with a valid JWT",
                "Open <font face='Courier'>backend/flows/parent_assessment_v1.json</font> to see the chatbot's node graph — that's the source of truth for what parents get asked",
                "Open <font face='Courier'>frontend/app/admin/dashboard/page.tsx</font> to see how the admin UI is structured",
                "Open <font face='Courier'>backend/app/api/admin.py</font> to see how admin endpoints are implemented",
                "Use the Data Explorer tab (admin dashboard) to poke at the live database — click a row to see the raw JSON",
                "When you're ready to deploy, see the separate <b>EdPsych_DevOps_Handoff.pdf</b> document for Railway + Vercel setup",
            ]
        ),
        Spacer(1, 12 * mm),
        _h("Done!", 2),
        _p(
            "You now have the full Ed Psych stack running on your machine with "
            "seeded test users. Log in, explore, and report any issues you run into."
        ),
    ]


# ─────────────────────────────────────────────────────────────────────
# Build doc
# ─────────────────────────────────────────────────────────────────────
def build():
    doc = SetupDoc(str(OUTPUT_PDF))

    story = []
    story.extend(cover_page())
    story.extend(section_what_youll_run())
    story.extend(section_prerequisites())
    story.extend(section_clone())
    story.extend(section_postgres())
    story.extend(section_env())
    story.extend(section_backend())
    story.extend(section_frontend())
    story.extend(section_test_accounts())
    story.extend(section_local_workflows())
    story.extend(section_directory())
    story.extend(section_commands())
    story.extend(section_troubleshooting())
    story.extend(section_next_steps())

    story.extend(
        [
            PageBreak(),
            Spacer(1, 60 * mm),
            _p("End of setup guide", "title"),
            Spacer(1, 8 * mm),
            _p(
                "Companion document: EdPsych_DevOps_Handoff.pdf (production deployment)",
                "cover_meta",
            ),
        ]
    )

    doc.build(story)
    print(f"[OK] Wrote {OUTPUT_PDF}")


if __name__ == "__main__":
    build()
