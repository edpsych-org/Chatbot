# Email School Chatbot Answers to Parent — Design

**Date:** 2026-04-22
**Status:** Approved for implementation planning

## Problem

Parents sometimes ask admins to share what the school said in its
chatbot session about their child. Today there is no in-product way
to do that — admins would have to copy answers manually. We want a
one-click flow that emails a PDF with the school's answers to a
linked parent guardian.

## Goal

From a student's detail drawer, an admin can pick a linked parent
guardian, optionally add a short note, and send them a PDF
containing:

1. A short narrative summary of the school's input.
2. The full Q&A transcript from the school's chatbot session.

Also persist a lightweight audit trail of who shared what with whom.

## Non-goals

- Sharing parent chatbot answers back to the school (not asked for).
- Giving psychologists or non-admins this capability.
- Sending to external (non-guardian) email addresses.
- Sharing partial / in-progress school sessions.
- Building a new audit-log table — reuse chat session context.

## UX

### Trigger surface

In the admin student detail drawer (not the row), add a new panel:

```
┌──────────────────────────────────────────────┐
│ School input                                 │
│  Completed 2026-04-21 · 28 answers           │
│  [ Email to parent ]                         │
│                                              │
│  Previously shared:                          │
│   · 2026-04-22 14:32 → vishnu@...  (Mother)  │
└──────────────────────────────────────────────┘
```

Panel is visible only when a SCHOOL assignment for the student has a
session in `COMPLETED` status. If there is none, the whole panel is
hidden.

### Confirmation modal

Click "Email to parent" → modal:

```
Email school input for {student_name}

Recipient
  [ Mother — vishnu@example.com ▼ ]      (dropdown)

Optional note (shown in email body, 500 char max)
  ┌──────────────────────────────────────┐
  │                                      │
  └──────────────────────────────────────┘

Attachment: {SafeName}_school_input.pdf (generated on send)

[ Cancel ]                    [ Send email ]
```

Rules:

- Dropdown lists every linked parent/guardian user (role=PARENT) for
  this student.
- Default selection: first entry in the list (generally the primary
  guardian).
- Note field optional; character counter under the textarea.
- Send button disabled while the request is in flight.
- Success → toast "Sent to <email>" + modal closes + audit row
  appears under the button.
- Brevo failure → inline red error under the Send button; modal
  stays open; no audit row written.

## Backend

### Endpoints

Both gated by `require_admin`, under the existing admin router.

#### `GET /api/v1/admin/students/{student_id}/school-share/preview`

Response:

```json
{
  "school_session": {
    "session_id": "uuid",
    "completed_at": "2026-04-21T11:57:12Z",
    "answers_count": 28
  } | null,
  "recipients": [
    {
      "user_id": "uuid",
      "name": "Vishnu V",
      "email": "vishnu@example.com",
      "relationship": "Mother"
    }
  ],
  "previously_shared": [
    {
      "sent_at": "2026-04-22T14:32:04Z",
      "recipient_email": "vishnu@example.com",
      "recipient_name": "Vishnu V",
      "relationship": "Mother"
    }
  ]
}
```

- `school_session` is the most recent SCHOOL assignment's session in
  `COMPLETED` status. If no such session exists for the student, the
  field is `null` and `recipients` / `previously_shared` are both
  empty arrays. Frontend hides the panel when `school_session` is
  null.
- `recipients` excludes users with role SCHOOL.
- `previously_shared` is pulled from the school session's
  `context_data["shared_with_parents"]`.

#### `POST /api/v1/admin/students/{student_id}/school-share/send`

Request body:

```json
{ "recipient_user_id": "uuid", "note": "optional text (<= 500 chars)" }
```

Response on success (202 Accepted):

```json
{ "status": "sent", "recipient_email": "vishnu@example.com" }
```

Logic:

1. Re-fetch the student and the completed school session. 404 if
   either is missing.
2. Validate that `recipient_user_id` is a linked parent guardian for
   the student AND has role PARENT. 400 if not.
3. Build the PDF (see `build_school_share_pdf` below).
4. Call `send_school_share_email(recipient_email, recipient_name,
   student_name, note, pdf_bytes, filename)`.
5. On Brevo success (2xx + a delivery-tracking id if present):
   append an entry to `session.context_data["shared_with_parents"]`:
   ```json
   {
     "sent_at": "ISO-8601",
     "sent_by_admin_id": "uuid",
     "recipient_user_id": "uuid",
     "recipient_email": "...",
     "recipient_name": "...",
     "relationship": "Mother",
     "note": "text or ''",
     "brevo_message_id": "id or null"
   }
   ```
   Commit.
6. Return 202.

Error handling:
- Brevo non-2xx → return 502 with `{"detail": "Email delivery
  failed", "provider_error": "..."}`; do NOT append the audit entry.
- PDF generation exception → 500, log stack, no audit entry.

### PDF builder

New file `backend/app/services/pdf_builder.py`:

- Function signature:
  `build_school_share_pdf(student, session, summary_text: str) -> bytes`
- Uses `reportlab` (already in `requirements.txt`).
- Layout:
  - **Header block**: student name, DOB, school, completed date.
  - **Summary section**: title "Summary" + `summary_text` rendered as
    paragraphs.
  - **Transcript section**: title "Full responses" + every Q&A pair
    from `session.context_data["completed_qa_pairs"]` rendered as:
    ```
    Q1. <question text>
    A.  <option label> (elaboration if present)
    ```
    If `completed_qa_pairs` is missing, fall back to scanning the
    session's messages.
- Returns raw PDF bytes. Caller handles attachment and transmission.

### Summary agent

Add `generate_school_response_summary(session_context) -> str` to
`app/agents/report_agents.py` (not a new agent class — a single
function using existing LLM infra):

- Input: the school session's `assessment_data` + student first name.
- Prompt: "Summarise the school's observations about {name} across
  classroom attention, peer interactions, academics, playground
  behaviour, and any concerns. 3-5 paragraphs, formal tone. Do NOT
  add recommendations. Use only the provided data."
- Max 600 tokens. Timeout 10s. On failure, return a one-line fallback
  ("The school has completed the questionnaire. Full responses
  follow.") so the PDF can still ship.

### Email helper

Extend `backend/app/utils/email.py`:

```
def send_school_share_email(
    recipient_email: str,
    recipient_name: str,
    student_name: str,
    admin_note: str | None,
    pdf_bytes: bytes,
    filename: str,
    email_service: EmailService,
) -> tuple[bool, str | None]:
```

- Subject: `School input for {student_name}`
- Body template: short message acknowledging the admin forwarded the
  school's feedback, the admin's note (if provided) rendered inside a
  quote block, and a line pointing to the attached PDF.
- Attaches the PDF using Brevo's `attachment: [{name, content}]`
  schema where `content` is base64 of `pdf_bytes`.
- Returns `(ok, message_id_or_error)`.

## Frontend

| File | Change |
|---|---|
| `frontend/src/components/admin/DetailDrawer.tsx` | Add "School input" panel below existing content; fetch `preview` on drawer open |
| `frontend/src/components/admin/SchoolShareModal.tsx` | New — recipient dropdown, note textarea, send handler |
| `frontend/src/components/admin/tables/StudentsTable.tsx` | No change if drawer already receives student id; otherwise pass it |
| `frontend/lib/api.ts` | No change (fetch from `API_BASE` with bearer auth inline, matching existing admin code) |

State flow:

1. Drawer opens for a student → fire `GET /school-share/preview`.
2. If `school_session == null` → don't render the panel at all.
3. Else render panel with `recipients.length` + the `previously_shared`
   list.
4. Click "Email to parent" → open modal with `recipients` + empty
   note.
5. Submit → `POST /school-share/send` → on 202 toast + refetch
   preview (so audit list refreshes) + close modal.

## Data model

No schema changes. Everything audit-related lives in
`chat_sessions.context_data["shared_with_parents"]` (JSON). Existing
`ChatSession.context_data` is already a JSONB column.

## Testing

1. Student with COMPLETED school session + 1 parent guardian:
   - Open drawer → panel visible with expected metadata.
   - Send → toast + audit row appears + Brevo test event shows
     `delivered`.
   - Inspect received PDF: header, summary paragraphs, full Q&A.
2. Same student, re-send to same parent → second audit row appears;
   PDF regenerated.
3. Student with COMPLETED school session + 0 parent guardians:
   panel visible, dropdown empty, Send disabled with inline notice.
4. Student with no school assignment at all: panel hidden.
5. Student with school session still IN_PROGRESS: panel hidden.
6. Psychologist-role user hitting `/school-share/send` directly:
   403.
7. Admin hitting `/school-share/send` with a `recipient_user_id`
   that is not linked to this student: 400.
8. Brevo intentionally offline (invalid API key for a test run):
   endpoint returns 502, no audit row written, UI shows inline
   error.

## Out of scope (future considerations)

- Sharing parent chatbot answers with the school (symmetric flow).
- A dedicated admin audit table for all shares (not just school
  ones).
- In-product "parent view" of the shared PDF without email.
- Re-delivery if the parent's mailbox bounces (manual retry for
  now).
