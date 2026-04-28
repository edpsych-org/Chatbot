# Naina Feedback — Validator + Assignment Policy + Skip — Design

**Date:** 2026-04-28
**Branch:** `akshay`
**Trigger:** End-user feedback after filling Naina's school questionnaire — short answers
("Minimal contact") were rejected with "describe your thoughts in a sentence or two", and admin
could not run a parent + school questionnaire concurrently for the same student.

## Issues addressed

1. **Short answers wrongly rejected.** Validator's `_is_gibberish` heuristic flagged real
   two-word answers ("Minimal contact", "Group work") as gibberish because the answer's words
   weren't in the small `COMMON_WORDS` set (~120 entries). Affects parent flow and school
   flow's last 3 free-text questions (`what_helps`, `hopes`, `anything_else`) most visibly.
2. **One questionnaire at a time per student.** Commit `3dc9df1` made the per-student lock
   total — blocks parent + school running concurrently. Naina's admin needed both
   simultaneously.
3. **No skip option.** Teaching assistants and short-handed respondents have no way to
   acknowledge "I don't know" on optional follow-up questions; they're forced to type
   placeholder text.

## Out of scope

- Issue (c) "office email already registered" was a user hypothesis about *why* (b) blocked
  them. The backend already links existing parent users on
  [admin.py:1064-1071](../../backend/app/api/admin.py#L1064). No change needed unless a
  separate failure path surfaces after (b) is fixed.
- No DB migration. Reuses existing JSONB `assessment_data` and
  `chat_messages.message_metadata`.

---

## Section 1 — Validator simplification

### Problem

`InputValidatorAgent._is_gibberish` ([validator.py:303-330](../../backend/app/agents/validator.py#L303))
counts only words present in `COMMON_WORDS` (line 104) as English. Two-word real answers
where neither word is on the list (e.g. "Minimal contact") trip the
"`real_word_count == 0 and len(words) >= 2` → True" branch and produce the message
*"I didn't quite understand that. Could you describe your thoughts in a sentence or two?"*

### Change

- Delete `_is_gibberish` method and `COMMON_WORDS` set.
- Remove the call site at [validator.py:246-251](../../backend/app/agents/validator.py#L246).
- Keep `VAGUE_FILLERS` set (`idk`, `dunno`, `nothing`, `none`, `na`, `n/a`, `i don't know`,
  `not sure`) as a fast literal block before LLM relevance check.
- Short-answer branch (`word_count < 4`) keeps existing flow:
  vague filler → reject; otherwise → `_llm_relevance_check(text, question_context, …)`.
- `_llm_relevance_check` is the sole authority on "is this a real, on-topic short answer".

### Why this works

OpenAI gpt-4o-mini reliably distinguishes *"Minimal contact"* (relevant to *"describe their
social interactions"*) from *"ghvvl;k sd jkj c dghj"* (unintelligible). Cost per short-answer
call is fractional cents. The Groq fallback already added in commit `3e4747b` covers OpenAI
outages.

### Failure modes

- **OpenAI + Groq both down:** validator's `_llm_relevance_check` returns `None` → caller
  treats as "fail open" / accept. Better than fail-closed because the alternative is locking
  legitimate users out.
- **LLM judges valid short answer irrelevant:** rare; user can edit answer (already supported
  via PATCH `/sessions/{sid}/messages/{mid}`).

---

## Section 2 — Per-role-bucket assignment policy

### Problem

[assignments.py:118-138](../../backend/app/api/assignments.py#L118) blocks any active
assignment regardless of recipient role. Admin can't have a Parent answering the home form
while the School answers the school form for the same student.

### Change

Lock by `(student_id, recipient.role)` instead of `student_id` alone. Two role buckets exist:
`UserRole.PARENT` and `UserRole.SCHOOL`. One active assignment per bucket per student.

#### `POST /assignments` (single-recipient path)

```python
# Resolve recipient's role from User row
recipient = await db.get(User, assignment_data.assigned_to)
existing = await db.execute(
    select(AssessmentAssignment)
    .join(User, AssessmentAssignment.assigned_to == User.id)
    .where(
        AssessmentAssignment.student_id == assignment_data.student_id,
        AssessmentAssignment.status.in_([
            AssignmentStatus.ASSIGNED,
            AssignmentStatus.IN_PROGRESS,
        ]),
        User.role == recipient.role,
    )
)
if existing.scalar_one_or_none():
    raise HTTPException(
        status_code=400,
        detail=(
            f"This student already has an active "
            f"{recipient.role.value.lower()} assignment. "
            f"Cancel or complete the existing one first."
        ),
    )
```

#### `POST /admin/students/.../assign` (multi-guardian batch path,
[admin.py:1230-1250](../../backend/app/api/admin.py#L1230))

- **Drop** the `len(guardian_ids) > 1` 400 reject added in commit `3dc9df1`.
- For each guardian in the batch, group by `User.role`. Within a single batch:
  - Multiple PARENT recipients (mom + dad) → still rejected (would violate per-bucket lock).
  - One PARENT + one SCHOOL → both created.
- Per-recipient existing-assignment check uses the role-bucket query above. Skipped
  recipients land in the existing `skipped[]` response array with reason
  `"already_has_active_assignment"`.

### Why this matches user intent

Mental model is "the home form" and "the school form" — two distinct artifacts. The
per-student lock conflated the two. Per-role-bucket preserves the original "one mom can't
fight one dad over the same form" guarantee while letting parent + school run in parallel.

### Failure modes

- **Existing data with two PARENT assignments active:** none should exist (the previous
  per-student lock prevented it). New code does not retroactively fail; only blocks new
  creation.
- **Role added later (e.g. PSYCHOLOGIST as recipient):** lives in its own bucket
  automatically. No code change required.

---

## Section 3 — Skip button (free-text questions only)

### UX

- A "Skip" pill appears in the answer panel **only** when the current node's `type === 'text'`
  (or `mcq` with no `options` array — pure free-text). Hidden on scored MCQ.
- Pill style: small, subdued grey ("Skip this question"), placed left of the Send button.
- Click → fires the skip action; the user's bubble renders italic greyed *"(skipped)"*.

### Backend

New `/message` action `skip`:

```jsonc
// POST /api/v1/hybrid-chat/sessions/{sid}/message
{ "action": "skip", "node_id": "<current node id>" }
```

Handler ([hybrid_chat.py](../../backend/app/api/hybrid_chat.py)):

1. Row-lock session (`select … with_for_update()`).
2. Reject if session COMPLETED → 400.
3. Reject if `node.type != 'text'` and node has any `options` → 400 with
   `"Cannot skip a multiple-choice question"`.
4. Reject if `node_id != current_node_id` → 400 (same staleness guard as edit endpoint).
5. Append node id to `assessment_data[category].skipped_nodes` (new list field; default `[]`).
6. Insert `ChatMessage`:
   - `role = 'user'`, `content = '(skipped)'`,
   - `message_metadata = {"skipped": True, "node_id": node_id}`.
7. Skip validator entirely.
8. Advance to next node via existing `_advance_to_next_node` helper.

### Report + PDF generation

- [report_agents.py](../../backend/app/agents/report_agents.py) `SchoolResponseSummaryAgent`
  and any other QA-pair iterator: filter out node ids present in `skipped_nodes` before
  feeding the LLM or rendering.
- [pdf_builder.py](../../backend/app/services/pdf_builder.py) `_iter_qa_pairs`: same filter.
- Severity calc unaffected — only MCQ contribute to severity, and MCQ cannot be skipped.

### Frontend

- [McqOptions.tsx](../../frontend/src/components/chat/McqOptions.tsx): accept new prop
  `onSkip?: () => void`. If `props.options?.length === 0 || props.options == null` and
  `onSkip` provided, render Skip pill in the same row as Send.
- [HybridChat.tsx](../../frontend/src/components/chat/HybridChat.tsx):
  - New `handleSkip` callback. POSTs `{action: "skip", node_id: currentQuestion.node_id}`.
  - On success, append local user bubble `{content: "(skipped)", skipped: true}` and bot's
    next message from response.
  - On 400, surface error inline (same toast as edit error).
- [MessageBubble.tsx](../../frontend/src/components/chat/MessageBubble.tsx): when
  `message.skipped`, render `<em className="text-white/70 italic">(skipped)</em>` instead of
  content text. Hide Edit pill for skipped bubbles.
- [types/chat.ts](../../frontend/src/types/chat.ts): add `skipped?: boolean` to
  `ChatMessage`.

---

## Files touched

| Action | File | Change |
|---|---|---|
| EDIT | `backend/app/agents/validator.py` | Delete `_is_gibberish`, `COMMON_WORDS`. Remove call site lines 246-251. |
| EDIT | `backend/app/api/assignments.py` | Per-role-bucket uniqueness in `POST /assignments`. |
| EDIT | `backend/app/api/admin.py` | Drop multi-guardian rejection; per-role-bucket dedupe in batch path. |
| EDIT | `backend/app/api/hybrid_chat.py` | New `skip` action handler. Validate type. Append to `skipped_nodes`. Insert "(skipped)" message. |
| EDIT | `backend/app/agents/report_agents.py` | Filter `skipped_nodes` from QA pairs. |
| EDIT | `backend/app/services/pdf_builder.py` | Filter `skipped_nodes` from QA pairs. |
| EDIT | `frontend/src/components/chat/McqOptions.tsx` | Skip pill on free-text questions only. |
| EDIT | `frontend/src/components/chat/HybridChat.tsx` | `handleSkip` POST. Render skipped bubble. |
| EDIT | `frontend/src/components/chat/MessageBubble.tsx` | Render "(skipped)" italic; hide Edit pill. |
| EDIT | `frontend/src/types/chat.ts` | Add `skipped?: boolean` to `ChatMessage`. |

No DB migration. No new endpoint surface area beyond a new action value on existing
`/message` route. No backend dependency additions.

## Verification

1. `python main.py` (backend) + `npm run dev` (frontend).
2. Validator: send "Minimal contact" as answer to social-interactions question → accepted.
   Send "ghvvl;k sd jkj c dghj" → rejected via LLM relevance check.
3. Validator: send "k", "x" → still rejected (vague filler / single-char).
4. Assignments: assign Parent + School to same student → both rows created. Try to assign
   second Parent (e.g. dad while mom active) → 400 with role-specific error message.
5. Assignments: cancel mom's assignment → can now assign dad.
6. Skip: in school flow, reach `what_helps` question → Skip pill visible. Click →
   "(skipped)" bubble appears, flow advances. Try to skip on an MCQ scoring question → no
   pill rendered; if request forced via curl → 400.
7. Generate PDF for a session containing skipped nodes → those questions absent from QA
   list. Severity unchanged.
8. Backfill check: existing reports unaffected (no `skipped_nodes` key → defaults to
   empty list).
