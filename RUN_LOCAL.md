# How to Run the Project in Terminal

Quick reference for starting / stopping the EdPsych project on your machine.
For first-time setup (database creation, .env, dependency install) see
[`README.md`](README.md) or `EdPsych_Local_Setup_Guide.pdf`.

---

## Check if it's already running

```bash
curl http://localhost:8000/health
curl -s -o /dev/null -w "frontend=%{http_code}\n" http://localhost:3000
```

Expected:

```
{"status":"healthy","database":"connected","llm":"groq","timestamp":...}
frontend=200
```

If both respond, open the app:

- Backend health: http://localhost:8000/health
- Backend API docs: http://localhost:8000/api/docs
- Frontend: http://localhost:3000/login → log in with `admin1@test.com` / `Admin@123`

---

## Start the servers (two terminals)

You need **two terminal windows** — one for the backend, one for the frontend.
Leave both open while you use the app.

### Terminal 1 — backend

```bash
cd "d:/GEN AI/edpsych-production-prototype/backend"

# Activate the Python virtual environment
source venv/Scripts/activate        # Windows bash / git-bash
# venv\Scripts\Activate.ps1         # Windows PowerShell
# source venv/bin/activate          # macOS / Linux

python main.py
```

Wait for:

```
INFO: Starting EdPsych AI Backend...
INFO: Database: localhost:5432
INFO: LLM: Groq (llama-3.1-8b-instant)
INFO: Database tables created/verified
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 — frontend

```bash
cd "d:/GEN AI/edpsych-production-prototype/frontend"
npm run dev
```

Wait for:

```
▲ Next.js 14.2.0
- Local: http://localhost:3000
✓ Ready in X.Xs
```

### Open the app

http://localhost:3000/login

| Email | Password | Role |
|---|---|---|
| `admin1@test.com` | `Admin@123` | Admin |
| `dr.smith@test.com` | `Doctor@123` | Psychologist |
| `parent1@test.com` | `Parent@123` | Parent |

---

## Stop the servers

In each terminal window, press `Ctrl+C`.

---

## Port conflicts

If a server fails to start because the port is already in use:

### Windows

```bash
# Find the process on port 8000 (or 3000)
netstat -ano | findstr :8000
# e.g. output:  TCP  0.0.0.0:8000  LISTENING  37212

# Kill it (replace 37212 with your PID)
taskkill //F //PID 37212
```

### macOS / Linux

```bash
lsof -i :8000
kill -9 <pid>
```

Then re-run the start command.

---

## Useful quick commands

```bash
# Query the database
PGPASSWORD=edpsych_secure_password psql -U edpsych -h localhost -d edpsych_db

# Inside psql:
\dt                                       # list tables
SELECT id, email, role FROM users;
SELECT token, expires_at FROM magic_link_tokens ORDER BY created_at DESC LIMIT 5;
\q                                        # quit

# Restart backend from scratch (dev only — drops all data)
cd backend
python reset_database.py
python seed_test_users.py
python main.py

# Re-seed test users without wiping the database
cd backend && python seed_test_users.py

# Regenerate the handoff PDFs
cd backend && python generate_devops_handoff.py
cd backend && python generate_local_setup_guide.py
```

---

## Default URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API base | http://localhost:8000/api/v1 |
| Backend health | http://localhost:8000/health |
| Swagger UI | http://localhost:8000/api/docs |
| ReDoc | http://localhost:8000/api/redoc |
| PostgreSQL | `postgresql://edpsych:edpsych_secure_password@localhost:5432/edpsych_db` |

---

## Troubleshooting

See [`README.md`](README.md) for the quick troubleshooting table and
`EdPsych_Local_Setup_Guide.pdf` (section 12) for the full list with
symptoms and fixes.
