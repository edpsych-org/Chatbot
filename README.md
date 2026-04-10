# EdPsych AI Prototype — Running Locally

An educational-psychology assessment and report-generation platform.
FastAPI backend + Next.js 14 frontend + PostgreSQL.

> Full reference PDFs live at the repo root:
> - **`EdPsych_Local_Setup_Guide.pdf`** — 16-page developer onboarding
> - **`EdPsych_DevOps_Handoff.pdf`** — 29-page production deployment reference

---

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend runtime |
| Node.js | 20+ | Frontend dev server |
| PostgreSQL | 16 or 18 | Database |
| Git | any | Clone the repo |

Optional: Tesseract OCR (for IQ PDF extraction), Ollama (for offline LLM).

---

## 1. Clone the repo

```bash
git clone https://github.com/akshaytoni99/edpsych-chatbot.git edpsych-production-prototype
cd edpsych-production-prototype
```

## 2. Create the database

Open `psql` as the `postgres` superuser:

```bash
# Windows:
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -h localhost

# macOS / Linux:
psql -U postgres -h localhost
```

Run:

```sql
CREATE USER edpsych WITH PASSWORD 'edpsych_secure_password';
CREATE DATABASE edpsych_db OWNER edpsych;
GRANT ALL PRIVILEGES ON DATABASE edpsych_db TO edpsych;
\q
```

## 3. Root `.env`

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```env
DATABASE_URL=postgresql://edpsych:edpsych_secure_password@localhost:5432/edpsych_db
SECRET_KEY=<generate with: openssl rand -hex 32>
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
FRONTEND_URL=http://localhost:3000

# LLM — pick one
USE_GROQ=true
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Optional — leave BREVO_API_KEY blank to log magic-link emails to terminal
BREVO_API_KEY=

DEBUG_MODE=true
```

## 4. Backend — terminal 1

```bash
cd backend
python -m venv venv

# Activate
source venv/Scripts/activate            # Windows bash / git-bash
# venv\Scripts\Activate.ps1             # Windows PowerShell
# source venv/bin/activate              # macOS / Linux

pip install -r requirements.txt
python seed_test_users.py               # creates admin + psychologist + parent accounts
python main.py                          # http://localhost:8000
```

Expected output:

```
INFO: Starting EdPsych AI Backend...
INFO: Database: localhost:5432
INFO: LLM: Groq (llama-3.1-8b-instant)
INFO: Database tables created/verified
INFO: Uvicorn running on http://0.0.0.0:8000
```

Verify: `curl http://localhost:8000/health`
Interactive API docs: http://localhost:8000/api/docs

## 5. Frontend — terminal 2 (leave backend running)

```bash
cd frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm install
npm run dev                             # http://localhost:3000
```

## 6. Log in

Open http://localhost:3000/login

| Email | Password | Role |
|---|---|---|
| `admin1@test.com` | `Admin@123` | Admin — full control |
| `dr.smith@test.com` | `Doctor@123` | Psychologist — reports + workspace |
| `parent1@test.com` | `Parent@123` | Parent — assessment chat |

---

## Try the workflow end-to-end

1. **As admin** → Students tab → Create Student → fill in child + parent details
2. **As admin** → Assignments tab → New Assignment → select student & parent → Save
3. Copy the magic-link URL from the backend terminal log (look for `[EMAIL MODE: DEV] Would send email to...`)
   _or_ click **Resend Link** on the assignment row — it copies the URL to your clipboard
4. Paste the URL in an **incognito window** → set a password → complete the chatbot assessment
5. **As `dr.smith@test.com`** → Students tab → click **Reports Workspace** → generate sections via LLM, edit, finalize

Try the accessibility menu (bottom-right Aa button) at 100 / 115 / 130 / 150% — layout stays stable, only text scales.

---

## Common issues

| Symptom | Fix |
|---|---|
| `ValidationError SECRET_KEY` at backend startup | Set `SECRET_KEY` in `.env` (any 32+ char string) |
| `connection refused` to postgres | PostgreSQL isn't running — start it via Services (Windows) / `brew services start postgresql@16` / `systemctl start postgresql` |
| `password authentication failed` | Re-run the `CREATE USER` / `GRANT` SQL in step 2 |
| Port 3000 already in use | `netstat -ano \| findstr :3000` then `taskkill //F //PID <pid>` |
| CORS error in devtools | Make sure `CORS_ORIGINS` in `.env` includes `http://localhost:3000` and restart the backend |
| Magic link email never arrives | Expected without `BREVO_API_KEY`. Check backend terminal for the logged URL, or use the admin dashboard's **Resend Link** button |
| `ModuleNotFoundError` on `pip install` complete | Venv isn't activated — re-activate and verify `pip show fastapi` points into `backend/venv` |

Full troubleshooting table is in section 12 of `EdPsych_Local_Setup_Guide.pdf`.

---

## Directory quick reference

```
edpsych-production-prototype/
├── .env                          # Root env file (git-ignored)
├── .env.example                  # Template
├── README.md                     # this file
├── EdPsych_DevOps_Handoff.pdf    # Production deployment doc
├── EdPsych_Local_Setup_Guide.pdf # Full developer onboarding doc
├── backend/
│   ├── main.py                   # FastAPI entrypoint
│   ├── requirements.txt          # Python deps
│   ├── seed_test_users.py        # Test accounts
│   ├── app/core/                 # config, database, security
│   ├── app/api/                  # Route handlers
│   ├── app/models/               # SQLAlchemy models
│   ├── app/services/             # LLM + OCR
│   └── app/utils/                # email, magic_link
└── frontend/
    ├── package.json
    ├── app/                      # Next.js App Router pages
    │   ├── login/
    │   ├── admin/dashboard/
    │   ├── psychologist/dashboard/
    │   ├── chat/[assignmentId]/
    │   └── auth/magic/[token]/
    ├── components/               # AccessibilityMenu, ConfirmModal
    └── src/components/           # chat, workspace, admin
```

---

## Commands cheat sheet

```bash
# Start backend
cd backend && source venv/Scripts/activate && python main.py

# Start frontend
cd frontend && npm run dev

# Query the database
PGPASSWORD=edpsych_secure_password psql -U edpsych -h localhost -d edpsych_db
\dt                                        -- list tables
SELECT id, email, role FROM users;
SELECT token, expires_at FROM magic_link_tokens ORDER BY created_at DESC LIMIT 5;

# Reset everything (dev only — drops all data)
cd backend && python reset_database.py && python seed_test_users.py

# Regenerate the handoff PDFs
cd backend && python generate_devops_handoff.py
cd backend && python generate_local_setup_guide.py
```

---

## Stack at a glance

- **Backend**: FastAPI 0.109 + SQLAlchemy 2.0 (async) + asyncpg + Uvicorn
- **Frontend**: Next.js 14 App Router + React 18 + TypeScript + Tailwind 3.4
- **Database**: PostgreSQL 16/18
- **LLM**: Groq (prod) / OpenAI / Ollama — runtime switchable
- **Email**: Brevo API (falls back to terminal log in dev)
- **Auth**: JWT (HS256) + invite-based magic links (48h expiry)
- **Fonts**: Average (serif) + Nunito (sans) via `next/font`
- **Theme**: Ed Psych Practice palette — teal `#00acb6`, red `#e61844`
- **Accessibility**: 4-level text-size scaling (100 / 115 / 130 / 150%)

---

## Production deployment

See `EdPsych_DevOps_Handoff.pdf` (Railway for backend, Vercel for frontend, Neon for database).
