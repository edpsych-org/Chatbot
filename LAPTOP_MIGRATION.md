# Laptop Migration — EdPsych Chatbot

Continue work on a new machine. Everything needed to clone, run, debug, and deploy.

---

## 1. Repo

| Field | Value |
|---|---|
| Clone URL | `https://github.com/edpsych-org/Chatbot.git` (old `edpsych/Chatbot` redirects 308) |
| Working branch | `akshay` |
| Deploy branch | `staging` (push to `staging` triggers GH Actions → ECS) |
| Default branch on remote | `master` |
| Local path (this laptop) | `d:\GEN AI\edpsych-akshay-fresh\` |

```bash
git clone https://github.com/edpsych-org/Chatbot.git edpsych-akshay-fresh
cd edpsych-akshay-fresh
git fetch --all
git checkout akshay
```

**Auth.** Old `origin` URL has embedded GitHub PAT — rotate before reuse. Either:
- Use `gh auth login` (HTTPS + GitHub credential helper), or
- Re-embed a fresh PAT: `git remote set-url origin https://<USER>:<NEW_PAT>@github.com/edpsych-org/Chatbot.git`

Commit author config (matches existing history):
```bash
git config user.name "Edpsych"
git config user.email "administrator@theedpsych.com"
```

---

## 2. Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI · SQLAlchemy 2 async · Pydantic v2 · Python 3.11+ |
| Frontend | Next.js 14 App Router · TypeScript · Tailwind |
| DB | PostgreSQL (AWS RDS prod; local Postgres optional for dev) |
| LLM | OpenAI `gpt-4o-mini` primary · Groq fallback |
| Email | Brevo (transactional) — sender `administrator@theedpsych.com` |
| Storage | Wasabi S3 (eu-west-1) — uploads/reports |
| Reports | reportlab (PDF) · python-docx (Word) |

---

## 3. Project layout

```
edpsych-akshay-fresh/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routers (admin, hybrid_chat, students, ...)
│   │   ├── agents/        # validator, empathy, assessor, orchestrator, background
│   │   ├── models/        # SQLAlchemy ORM
│   │   ├── schemas/       # Pydantic
│   │   ├── core/          # database, security, config
│   │   └── utils/         # magic_link, email, pdf
│   ├── flows/
│   │   ├── parent_assessment_v1.json    # 70+ MCQ + free-text questions
│   │   └── school_assessment_v1.json
│   ├── main.py            # uvicorn entry
│   ├── requirements.txt
│   └── requirements-deploy.txt
├── frontend/
│   ├── app/               # Next.js App Router pages
│   ├── src/components/    # chat/HybridChat.tsx is the heart
│   ├── src/types/         # chat.ts has BotResponse, ChatMessage
│   └── package.json
├── docker-compose.yml
├── README.md
├── HANDOFF.md             # earlier session handoff (partly stale)
└── LAPTOP_MIGRATION.md    # this file
```

---

## 4. Local environment

### 4.1 Backend `.env` (place at `backend/.env`)

```bash
# DB
DATABASE_URL=postgresql+asyncpg://USER:PASS@HOST:5432/DBNAME
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">

# CORS / FE
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
FRONTEND_URL=http://localhost:3001

# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
USE_OPENAI=true
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-8b-instant

# Magic link
MAGIC_LINK_EXPIRY_HOURS=48

# Email (Brevo)
BREVO_API_KEY=xkeysib-...
BREVO_SENDER_EMAIL=administrator@theedpsych.com
BREVO_SENDER_NAME=The EdPsych Practice

# S3 (optional for local)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=eu-west-1
S3_BUCKET=...
S3_ENDPOINT_URL=https://s3.eu-west-1.wasabisys.com
```

Pull current values from existing laptop's `backend/.env` or 1Password / shared vault.

### 4.2 Frontend `.env.local`

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
```

### 4.3 Install + run

```bash
# Backend
cd backend
python -m venv .venv
source .venv/Scripts/activate     # Windows bash
pip install -r requirements.txt
python main.py                     # → http://localhost:8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev                        # → http://localhost:3001
```

Default ports: backend `8000`, frontend `3001`. Swagger at `http://localhost:8000/docs`.

---

## 5. Database

Prod uses AWS RDS Postgres (creds in `.env`). For local dev:

```bash
# Option A — point local backend at RDS (read-only? careful)
DATABASE_URL=postgresql+asyncpg://...rds.amazonaws.com:5432/...

# Option B — local Postgres via docker-compose
docker compose up -d postgres
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/edpsych
```

Schema bootstrap: `backend/main.py` calls `Base.metadata.create_all` on startup. No Alembic migrations in repo — schema lives in SQLAlchemy models under `backend/app/models/`.

Useful one-shot scripts in `backend/`:
- `seed_test_users.py` — create admin + parent + school + psychologist users
- `reset_password.py`, `reset_database.py`, `check_table.py`
- `get_users.py`, `get_assignment_id.py`

---

## 6. Deploy pipeline

```
push to akshay   →  nothing automatic (working branch)
PR akshay → staging, merge  →  GH Actions builds → ECR `prod-chatbot-fe` / `prod-chatbot-be`
                              →  ECS service `prod-chatbot-fe-service` / `prod-chatbot-be-service`
                              →  https://stage-cb.theedpsych.co.uk
push to master   →  prod (only when staging signed off)
```

- Region: `eu-west-2`
- GH Actions secrets needed: `GH_ACCESS_KEY_ID`, `GH_SECRET_ACCESS_KEY` (already configured on repo)
- Task definitions: `chatbot-be-revision.json`, `prod-chatbot-fe-revision.json` in repo root

**To live-test changes:** open PR `akshay → staging` and merge. ECS rollover ≈ 5 min.

---

## 7. Recent work shipped (today, all on `akshay`)

| Commit | Summary |
|---|---|
| `859eb48` | Admin update_user: surface real error, pre-check email collision (409 instead of blank 500) |
| `fca8cc6` | Validator rotates re-prompt phrasing per attempt; empathy bans "good choice", skips LLM for ≤2-word MCQ acks |
| `e52f6f9` | Parent flow JSON: grammar fixes, UK spelling (Maths/organised), drop "language arts", "they"→`{name}` for verb agreement |
| `91c0c3d` | Student delete cascade fix: `passive_deletes=True` on StudentGuardian relationships + raw DELETE in endpoint |
| `5abe66b` | Flow wording bulk pass (he/she pronouns, UK spelling, ban transition phrases) |
| `0af775e` | Chat returns real `user_message_id` UUID; FE swaps optimistic id so edit/skip work |
| `f3c47f7` | Magic link: invalidate prior unused invite tokens before issuing new one (fixes "expired" on email reuse) |
| `7454de3` | Admin create-student: rebind existing user role/name/phone for email reuse |
| `62c811a` | Admin delete student + cascade fix for AssessmentAssignment FK |
| `43387fb` | delete_user FK pre-purge, neutral pronouns, edit UUID guard, British English in LLM prompts |
| `4b84daf` | Validator lenient + auto-accept after 2 rejects + skip without node_id |
| `ec28be1` / `8863878` / `e097185` | Skip-question feature: button + bubble + type |
| `0980ab7` | Reports exclude skipped nodes from summary + PDF |

PR `akshay → staging` (#31) **unmerged**. Live test on stage requires merge.

---

## 8. Pending / known issues

- PR `akshay → staging` open — needs admin merge to deploy today's fixes.
- "Back to edit at end of questionnaire" (Naina image 14) — deferred, bigger feature.
- `final_reports.generated_by_user_id` / `approved_by_user_id` lack `ondelete` — deleting a user who finalised a report would still 500. Rare; not in current test flow.

---

## 9. Workflow conventions (memory rules)

| Rule | Source |
|---|---|
| **No Claude / AI attribution in commits or PRs.** No `Co-Authored-By` trailer. | `~/.claude/projects/d--/memory/feedback_commits_no_claude.md` |
| **Always ask before `git push`.** Commit locally first; user often pre-approves "push to akshay". | `feedback_ask_before_push.md` |
| Default to `superpowers:*` plugin skills (brainstorming, debugging, TDD, plans, code review). | `feedback_superpowers_default.md` |
| Don't offer Visual Companion / local-browser dashboards. | `feedback_no_web_companions.md` |
| Pragmatic A/B/C decisions; OK to bundle small tasks. | `feedback_pragmatic_workflow.md` |
| Caveman mode active — terse fragments outside code/commits. Toggle: `stop caveman` / `/caveman lite|full|ultra`. | hook |

User's email: `aihub@absolutedata.ai`. Today's date in this session: `2026-05-14` (UTC). Local time IST.

---

## 10. Common dev commands

```bash
# Status
git status && git log --oneline -10

# Run a backend script (with venv active)
cd backend && python check_table.py

# Tail backend logs
tail -f backend/logs/app.log

# Lint / typecheck FE
cd frontend && npm run lint && npx tsc --noEmit

# Open PR akshay → staging
gh pr create --base staging --head akshay --title "..." --body "..."

# Validate flow JSON
python -c "import json; json.load(open('backend/flows/parent_assessment_v1.json')); print('OK')"
```

---

## 11. Key files to know

| Purpose | Path |
|---|---|
| Chat orchestration entry | `backend/app/api/hybrid_chat.py` |
| Multi-agent pipeline | `backend/app/agents/orchestrator.py` |
| Validator (re-prompt rotation) | `backend/app/agents/validator.py` |
| Empathy ack (banned phrases) | `backend/app/agents/empathy.py` |
| Admin endpoints (user, student CRUD) | `backend/app/api/admin.py` |
| Pronoun substitution | `backend/app/api/hybrid_chat.py:295-336` |
| Question flow source | `backend/flows/parent_assessment_v1.json`, `school_assessment_v1.json` |
| Magic link issuance + invalidation | `backend/app/utils/magic_link.py` |
| Chat UI | `frontend/src/components/chat/HybridChat.tsx` |
| Message bubble + edit pill | `frontend/src/components/chat/MessageBubble.tsx` |
| Admin dashboard | `frontend/app/admin/dashboard/page.tsx` |
| Type defs (BotResponse, ChatMessage) | `frontend/src/types/chat.ts` |

---

## 12. Quick smoke test after fresh setup

1. `python main.py` — backend starts, no SQLAlchemy errors.
2. `npm run dev` — FE on `:3001`.
3. Visit `http://localhost:3001/login`, log in as admin (seed via `python backend/seed_test_users.py` if needed).
4. Admin dashboard renders user list.
5. Create test student + parent + school. Assign assessment. Receive magic link in console / email.
6. Open magic link → chat loads → answer 2-3 questions → skip pill works → edit pill works on last bubble.
7. Delete the test student → succeeds (no FK NOT NULL violation).

If all pass, environment is ready.
