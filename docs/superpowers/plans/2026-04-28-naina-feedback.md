# Naina Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix three Naina-feedback issues — short-answer rejection, single-questionnaire-per-student lock, and missing skip option on free-text questions.

**Architecture:** All changes are surgical. Backend: delete one heuristic in the validator, change one WHERE clause in two assignment endpoints, add one new branch to the `/message` handler. Frontend: add a Skip pill to the answer panel and wire it through `HybridChat`. Reuses existing JSONB columns; no DB migration.

**Tech Stack:** FastAPI · SQLAlchemy async · Pydantic v2 · Next.js 14 (App Router) · TypeScript · Tailwind. No test framework installed in this repo — verification is manual via curl + browser smoke test.

**Spec:** [docs/superpowers/specs/2026-04-28-naina-feedback-design.md](../specs/2026-04-28-naina-feedback-design.md)

---

## File map

| File | Responsibility | Tasks |
|---|---|---|
| `backend/app/agents/validator.py` | Short-answer relevance via LLM only; drop gibberish heuristic. | 1 |
| `backend/app/api/assignments.py` | Per-role-bucket lock on single-recipient assignment. | 2 |
| `backend/app/api/admin.py` | Per-role-bucket lock + drop multi-guardian rejection in batch path. | 3 |
| `backend/app/api/hybrid_chat.py` | New `skip` message_type branch + `_handle_skip` helper. | 4 |
| `backend/app/agents/report_agents.py` | Skip skipped node ids when summarising. | 5 |
| `backend/app/services/pdf_builder.py` | Skip skipped node ids in `_iter_qa_pairs`. | 5 |
| `frontend/src/types/chat.ts` | Add `skipped?: boolean` to `ChatMessage`. | 6 |
| `frontend/src/components/chat/MessageBubble.tsx` | Render "(skipped)" italic; hide Edit pill when `message.skipped`. | 6 |
| `frontend/src/components/chat/McqOptions.tsx` | Optional Skip pill on free-text questions. | 7 |
| `frontend/src/components/chat/HybridChat.tsx` | `handleSkip` POST + render skipped user bubble + advance. | 8 |

---

## Task 1: Validator — drop `_is_gibberish`

**Files:**
- Modify: `backend/app/agents/validator.py`

**Goal:** Remove `_is_gibberish` heuristic and `COMMON_WORDS` set. Short-answer relevance becomes the LLM's sole judgement (already wired via `_llm_relevance_check`). `VAGUE_FILLERS` stays.

- [ ] **Step 1: Remove the gibberish call site (lines 245-251).**

In `backend/app/agents/validator.py`, delete this block:

```python
        # Gibberish / nonsense detection
        if self._is_gibberish(text):
            return {
                "is_sufficient": False,
                "feedback": "I didn't quite understand that. Could you describe your thoughts in a sentence or two?",
                "confidence": 0.9,
            }
```

So that line 244 (blank) is followed directly by line 252 (`# ── Strict relevance checks ──`). Long-answer relevance (line 278's LLM gate) remains the catch-all for gibberish — `_llm_relevance_check` distinguishes "ghvvl;k sd jkj c dghj" from a real answer.

- [ ] **Step 2: Delete the `_is_gibberish` method.**

Remove the entire `@staticmethod` block starting at line 304:

```python
    @staticmethod
    def _is_gibberish(text: str) -> bool:
        """Detect gibberish/random keyboard mashing."""
        words = re.findall(r"[a-zA-Z']+", text.lower())
        if not words:
            return True
        # ... (entire method body through the trailing `return False`)
```

Run `grep -n "_is_gibberish" backend/app/agents/validator.py` after the delete — must return nothing.

- [ ] **Step 3: Delete the `COMMON_WORDS` set (lines 102-123).**

Remove the whole `COMMON_WORDS = { ... }` block including the comment header at line 102-103. `_is_gibberish` was the only consumer (verify with `grep -n "COMMON_WORDS" backend/app/agents/validator.py` → nothing).

- [ ] **Step 4: Manual verify.**

Restart backend (`python main.py` from `backend/`). In the chatbot UI, answer a social-interactions question with "Minimal contact" → must accept and advance. Answer with "ghvvl;k sd jkj" → must reject via the existing LLM relevance gate (returns one of the `RELEVANCE_PROMPTS`).

If both work: proceed. If "Minimal contact" still rejected, check that `OPENAI_API_KEY` is set and `_llm_relevance_check` is reachable; the short-answer branch (line 217-243) must be running.

- [ ] **Step 5: Commit.**

```bash
git add backend/app/agents/validator.py
git -c user.name="Edpsych" -c user.email="administrator@theedpsych.com" \
    commit -m "Validator: drop gibberish heuristic; LLM judges short answers"
```

---

## Task 2: Assignments — per-role-bucket lock (single-recipient)

**Files:**
- Modify: `backend/app/api/assignments.py:118-138`

**Goal:** Replace the per-student lock in `POST /assignments/` with a per-`(student_id, recipient.role)` lock. One PARENT and one SCHOOL assignment can run concurrently for the same student.

- [ ] **Step 1: Replace the existing block.**

In `backend/app/api/assignments.py`, replace lines 118-138 with:

```python
    # One active assignment per (student, recipient role) bucket. Parent and
    # School are independent buckets so home + school questionnaires can run
    # concurrently. A second mom (or second school) for the same student is
    # blocked until the active one completes or is cancelled.
    result = await db.execute(
        select(AssessmentAssignment)
        .join(User, AssessmentAssignment.assigned_to_user_id == User.id)
        .where(
            and_(
                AssessmentAssignment.student_id == assignment_data.student_id,
                AssessmentAssignment.status.in_([
                    AssignmentStatus.ASSIGNED,
                    AssignmentStatus.IN_PROGRESS,
                ]),
                User.role == assigned_to.role,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"This student already has an active "
                f"{assigned_to.role.value.lower()} assignment. "
                f"Cancel or complete the existing one first."
            )
        )
```

`assigned_to` is the User row already loaded at line 87. No extra DB roundtrip.

- [ ] **Step 2: Confirm `User` import already in scope.**

Run `grep -n "from app.models.user import" backend/app/api/assignments.py`. The line at the top must include `User`. (Already does — line 17 imports `User, UserRole`.)

- [ ] **Step 3: Manual verify.**

Restart backend. Through the admin UI:

1. Assign a Parent recipient to student X. Confirm 201.
2. Assign a School recipient to the same student X. Confirm 201 (was failing before).
3. Try to assign a second Parent (e.g. dad while mom active) to student X. Confirm 400 with body `"This student already has an active parent assignment. Cancel or complete the existing one first."`
4. Cancel mom's assignment (or mark it COMPLETED). Re-assign dad. Confirm 201.

- [ ] **Step 4: Commit.**

```bash
git add backend/app/api/assignments.py
git -c user.name="Edpsych" -c user.email="administrator@theedpsych.com" \
    commit -m "Assignments: per-role-bucket lock (parent + school can run together)"
```

---

## Task 3: Admin batch — per-role-bucket lock; drop multi-guardian reject

**Files:**
- Modify: `backend/app/api/admin.py:1191-1224`

**Goal:** In the multi-guardian batch endpoint, allow batches with mixed PARENT + SCHOOL recipients. Block only batches that would violate the per-role-bucket lock.

- [ ] **Step 1: Delete the blanket multi-guardian reject (lines 1191-1201).**

Remove this block:

```python
    # 3b. One-active-assignment-per-student policy covers batch size too:
    #     admin can only send to a single recipient at a time for a given
    #     student. Multi-guardian batches are rejected up front.
    if len(assignment.guardian_ids) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only one recipient can be assigned per student at a time. "
                "Pick a single parent/guardian or school."
            ),
        )
```

- [ ] **Step 2: Replace the per-student blocker (lines 1203-1224) with role-bucket check.**

Replace:

```python
    # 4. One-active-assignment-per-student policy. If ANY recipient already
    #    has an active assignment for this student, block the whole request
    #    — admin must cancel or complete the existing one before creating
    #    new ones (even for a different guardian).
    active_states = [AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS]
    blocker_result = await db.execute(
        select(AssessmentAssignment).where(
            and_(
                AssessmentAssignment.student_id == assignment.student_id,
                AssessmentAssignment.status.in_(active_states),
            )
        )
    )
    blocker = blocker_result.scalars().first()
    if blocker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "This student already has an active assignment. "
                "Cancel or complete the existing one first."
            ),
        )
```

With:

```python
    # 4. Per-role-bucket policy: one active PARENT and one active SCHOOL
    #    assignment per student. Reject if any incoming recipient (or two
    #    incoming recipients of the same role) would violate this.
    active_states = [AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS]

    # Collect the role of each incoming recipient.
    incoming_roles = {gid: users_by_id[gid].role for gid in assignment.guardian_ids}

    # 4a. Reject same-role duplicates within the incoming batch
    #     (e.g. mom + dad both PARENT in one batch).
    seen_roles: set = set()
    for gid in assignment.guardian_ids:
        role = incoming_roles[gid]
        if role in seen_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot assign two {role.value.lower()} recipients "
                    f"in the same batch — only one of each role per student."
                ),
            )
        seen_roles.add(role)

    # 4b. Look up active assignments for this student grouped by recipient role.
    blocker_result = await db.execute(
        select(AssessmentAssignment, User.role)
        .join(User, AssessmentAssignment.assigned_to_user_id == User.id)
        .where(
            and_(
                AssessmentAssignment.student_id == assignment.student_id,
                AssessmentAssignment.status.in_(active_states),
            )
        )
    )
    active_role_set = {row_role for _, row_role in blocker_result.all()}

    # 4c. Build skipped[] for incoming recipients whose role bucket is full.
    existing_by_user_id = {}
    for gid in list(assignment.guardian_ids):
        if incoming_roles[gid] in active_role_set:
            existing_by_user_id[gid] = True
```

`existing_by_user_id` is consumed at line 1232 — code there reports each blocked guardian into `skipped[]`. Keep dict shape compatible (truthy presence is what the original code checked — verify by reading lines 1232-1239).

- [ ] **Step 3: Update the existing skipped[] block (lines 1232-1239) so it does not crash.**

Original:

```python
        if gid in existing_by_user_id:
            existing = existing_by_user_id[gid]
            skipped.append({
                "guardian_id": str(gid),
                "reason": "already_has_active_assignment",
                "existing_assignment_id": str(existing.id),
            })
            continue
```

Replace with:

```python
        if gid in existing_by_user_id:
            skipped.append({
                "guardian_id": str(gid),
                "reason": "already_has_active_assignment",
                "existing_assignment_role": users_by_id[gid].role.value,
            })
            continue
```

(Reason: our new `existing_by_user_id` holds `True`, not an assignment row. We surface the role bucket that's full instead of an assignment id, which is more useful for the admin UI message.)

- [ ] **Step 4: Manual verify.**

Restart backend. Through admin UI:

1. Send a batch `{guardian_ids: [<mom_id>, <school_id>]}` → both created, none skipped.
2. Send `{guardian_ids: [<mom_id>, <dad_id>]}` → 400 with `"Cannot assign two parent recipients in the same batch — only one of each role per student."`
3. With mom's assignment still active, send `{guardian_ids: [<dad_id>]}` → 200 with dad in `skipped[]` (`reason: already_has_active_assignment`, `existing_assignment_role: PARENT`).

- [ ] **Step 5: Commit.**

```bash
git add backend/app/api/admin.py
git -c user.name="Edpsych" -c user.email="administrator@theedpsych.com" \
    commit -m "Admin batch: per-role-bucket lock; allow parent + school in one batch"
```

---

## Task 4: Backend — `skip` action on `/message`

**Files:**
- Modify: `backend/app/api/hybrid_chat.py` (lines 41-53, 599-680, plus new helper)

**Goal:** Accept `message_type: "skip"` from the frontend. Validate the current node is free-text (`type: "text"`), append the node id to `assessment_data.skipped_nodes`, advance the flow, return the next bot message.

- [ ] **Step 1: Loosen `ChatMessageInput` type to allow `skip`.**

`ChatMessageInput.message_type` is plain `str` (line 43) so no schema change needed — but add a comment:

```python
class ChatMessageInput(BaseModel):
    """User message input"""
    message_type: str  # "mcq_choice" | "free_text" | "skip"
    content: str
    question_id: Optional[str] = None
    selected_option: Optional[str] = None
    choice_value: Optional[str] = None
```

- [ ] **Step 2: Add a `_handle_skip` helper.**

Add this function below `_handle_free_text` (somewhere after line 940). Read the surrounding helpers first so the imports + flow_engine global are reused:

```python
async def _handle_skip(
    session: ChatSession,
    message_input: ChatMessageInput,
    student_name: str,
) -> dict:
    """Skip a free-text question. Records the node id in assessment_data
    and advances to the next node. Rejected for MCQ nodes."""
    flow_id = session.flow_id
    node_id = message_input.question_id or session.current_node_id
    node = flow_engine.get_node(flow_id, node_id)
    if not node:
        raise HTTPException(status_code=400, detail="Question not found")

    # Skip is only valid on free-text questions. MCQ scales drive severity
    # scoring — skipping them would corrupt the report.
    if node.get("type") != "text":
        raise HTTPException(
            status_code=400,
            detail="Cannot skip a multiple-choice question",
        )

    # Stale request guard: client-supplied node_id must match the session's
    # current node — if a race causes drift, we reject.
    if node_id != session.current_node_id:
        raise HTTPException(status_code=400, detail="Question is no longer active")

    # Record the skip in assessment_data per category.
    category = (node.get("metadata") or {}).get("category") or "general"
    assessment_data = session.context_data.setdefault("assessment_data", {})
    cat_bucket = assessment_data.setdefault(category, {})
    skipped_list = cat_bucket.setdefault("skipped_nodes", [])
    if node_id not in skipped_list:
        skipped_list.append(node_id)
    flag_modified(session, "context_data")

    # Advance to the next node.
    next_id = flow_engine.get_next_node_id(flow_id, node_id, user_choice=None)
    if not next_id:
        # End of flow — let _handle_mcq_choice's completion path do the work
        # by returning a sentinel the caller will interpret.
        session.current_node_id = None
        return {
            "message_type": "system",
            "content": "(skipped)",
            "metadata": {"completed": True},
        }

    session.current_node_id = next_id
    next_node = flow_engine.get_node(flow_id, next_id)
    return flow_engine.format_bot_message(next_node, student_name, node_id=next_id)
```

`flag_modified` is already imported at the top of `hybrid_chat.py` (used by the edit endpoint). If it's not, add `from sqlalchemy.orm.attributes import flag_modified` next to the other SQLAlchemy imports.

- [ ] **Step 3: Add a routing branch in `send_message`.**

In `send_message` (line 599), add a new branch in the routing block at line 651-668. Insert before the `elif message_input.message_type == "free_text":` branch:

```python
        elif message_input.message_type == "skip":
            # --- SKIP: only allowed on free-text questions ---
            bot_response_data = await _handle_skip(session, message_input, student_name)
```

- [ ] **Step 4: Mark the user bubble as skipped in DB.**

In `send_message`, the user message is built at lines 626-635. Extend `message_metadata` with a `skipped` flag when the action is skip. Replace lines 626-636 with:

```python
    is_skip = message_input.message_type == "skip"
    user_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER.value,
        message_type=message_input.message_type,
        content="(skipped)" if is_skip else message_input.content,
        message_metadata={
            "question_id": message_input.question_id,
            "selected_option": message_input.resolved_option,
            "skipped": is_skip,
        }
    )
    db.add(user_message)
```

- [ ] **Step 5: Manual verify (curl).**

Restart backend. Start a school assessment session, advance to the `what_helps` node (or use the chat UI to reach it). Then:

```bash
TOKEN="<paste your Bearer JWT>"
SID="<paste session id>"

curl -X POST "http://localhost:8000/api/v1/hybrid-chat/sessions/$SID/message" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message_type":"skip","content":"","question_id":"what_helps"}'
```

Expected: 200, body contains `bot_message` for the next node. Inspect DB:

```sql
SELECT context_data->'assessment_data' FROM chat_sessions WHERE id = '<SID>';
```

Must show `"skipped_nodes": ["what_helps"]` in the relevant category bucket.

Now try to skip an MCQ node:

```bash
curl -X POST ".../message" -d '{"message_type":"skip","content":"","question_id":"<some MCQ node>"}' ...
```

Expected: 400 `{"detail":"Cannot skip a multiple-choice question"}`.

- [ ] **Step 6: Commit.**

```bash
git add backend/app/api/hybrid_chat.py
git -c user.name="Edpsych" -c user.email="administrator@theedpsych.com" \
    commit -m "Chat: skip action for free-text questions"
```

---

## Task 5: Reports + PDF — exclude skipped nodes

**Files:**
- Modify: `backend/app/agents/report_agents.py`
- Modify: `backend/app/services/pdf_builder.py`

**Goal:** Make sure skipped questions don't render in the school-share PDF or appear in the LLM summary input.

- [ ] **Step 1: Find the QA-pair iterator(s).**

Run:

```bash
grep -n "completed_qa_pairs\|qa_pairs\|skipped_nodes" backend/app/agents/report_agents.py backend/app/services/pdf_builder.py
```

Expect hits in `_iter_qa_pairs` (pdf_builder) and `SchoolResponseSummaryAgent.summarise` (report_agents).

- [ ] **Step 2: In `pdf_builder._iter_qa_pairs`, drop skipped nodes.**

Inside the function, after extracting `assessment_data`, build a set of skipped ids:

```python
skipped_ids: set[str] = set()
for cat_bucket in (assessment_data or {}).values():
    if isinstance(cat_bucket, dict):
        skipped_ids.update(cat_bucket.get("skipped_nodes", []) or [])
```

Then in the loop that yields `(question, answer)` tuples, add a guard:

```python
for qa in completed_qa_pairs:
    if qa.get("node_id") in skipped_ids:
        continue
    yield (qa["question"], qa["answer"], qa.get("elaboration"))
```

(Adapt to the function's actual yield shape — read the existing code first; this is the schematic.)

- [ ] **Step 3: In `report_agents.SchoolResponseSummaryAgent.summarise`, drop skipped nodes from the prompt.**

Same pattern: read `assessment_data`, build `skipped_ids`, skip those entries when constructing the LLM prompt's QA list.

- [ ] **Step 4: Manual verify.**

Trigger a school-share send for a session that contains at least one skipped node:

```bash
curl -X POST "http://localhost:8000/api/v1/admin/students/<student_id>/school-share/send" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recipient_user_id":"<parent_user_id>","note":"manual test"}'
```

Open the resulting PDF (DEV mode logs the bytes; or pull from Brevo). The skipped question must NOT appear in the "Full responses" list. The "Summary" paragraph must not reference it.

- [ ] **Step 5: Commit.**

```bash
git add backend/app/agents/report_agents.py backend/app/services/pdf_builder.py
git -c user.name="Edpsych" -c user.email="administrator@theedpsych.com" \
    commit -m "Reports: exclude skipped nodes from summary + PDF"
```

---

## Task 6: Frontend types + bubble rendering

**Files:**
- Modify: `frontend/src/types/chat.ts`
- Modify: `frontend/src/components/chat/MessageBubble.tsx`

**Goal:** Type-safe `skipped` flag on `ChatMessage` and render greyed italic "(skipped)" instead of normal content.

- [ ] **Step 1: Extend `ChatMessage`.**

In `frontend/src/types/chat.ts`, add `skipped?: boolean` to the `ChatMessage` interface alongside `editedAt`. Also add to `ChatMessageMetadata` if a separate type is used to deserialise from backend `message_metadata`.

- [ ] **Step 2: Render skipped bubbles.**

In `frontend/src/components/chat/MessageBubble.tsx`, the user-message render branch (the `else` of `editing ?` at line 201-239) currently shows `{message.content}` in a `<p>`. Wrap with a check:

```tsx
<p className={`whitespace-pre-wrap text-[0.875rem] sm:text-[0.9375rem] leading-relaxed ${
  isUser ? 'text-white/95' : ''
} ${message.skipped ? 'italic opacity-70' : ''}`}>
  {message.skipped ? '(skipped)' : message.content}
</p>
```

In the timestamp row (line 209-237), hide the `Edit` pill when `message.skipped`:

```tsx
{isUser && canEdit && !message.skipped && (
  <button ...>Edit</button>
)}
```

- [ ] **Step 3: Manual verify (visual).**

Run `npm run dev` from `frontend/`. Open a chat session and trigger a skip from the next task — for now, just verify the type compiles: `npm run build` or rely on `next dev`'s type errors. Skipped bubbles will render once Task 8 wires the call.

- [ ] **Step 4: Commit.**

```bash
git add frontend/src/types/chat.ts frontend/src/components/chat/MessageBubble.tsx
git -c user.name="Edpsych" -c user.email="administrator@theedpsych.com" \
    commit -m "Chat: type + bubble for skipped messages"
```

---

## Task 7: Skip pill in answer panel

**Files:**
- Modify: `frontend/src/components/chat/McqOptions.tsx`

**Goal:** A subdued "Skip this question" pill rendered ONLY on free-text questions (no `options` provided), placed left of the Send button.

- [ ] **Step 1: Add `onSkip` prop to McqOptions.**

Open `frontend/src/components/chat/McqOptions.tsx` and find the props interface. Add:

```tsx
onSkip?: () => void;
```

- [ ] **Step 2: Render the pill conditionally.**

Locate the bottom row of the panel that holds the Send button. Add the Skip pill to its left:

```tsx
{onSkip && (!options || options.length === 0) && (
  <button
    type="button"
    onClick={() => {
      if (busy) return;
      onSkip();
    }}
    disabled={busy}
    aria-label="Skip this question"
    className="px-3 py-1.5 text-[0.75rem] font-medium rounded-full bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200 disabled:opacity-50"
  >
    Skip this question
  </button>
)}
```

`busy` is the existing local sending-state flag. The condition `(!options || options.length === 0)` ensures MCQ panels never render the pill.

- [ ] **Step 3: Verify alignment.**

Open chat in browser, reach a free-text question (`what_helps`, `hopes`, or `anything_else`). The Skip pill must appear left of the Send arrow. On an MCQ question, no Skip pill.

- [ ] **Step 4: Commit.**

```bash
git add frontend/src/components/chat/McqOptions.tsx
git -c user.name="Edpsych" -c user.email="administrator@theedpsych.com" \
    commit -m "Chat: skip pill on free-text questions"
```

---

## Task 8: Wire `handleSkip` in HybridChat

**Files:**
- Modify: `frontend/src/components/chat/HybridChat.tsx`

**Goal:** Implement the `handleSkip` callback that POSTs `{message_type: "skip", question_id}` to `/message`, appends a "(skipped)" user bubble locally, then appends the bot's next message.

- [ ] **Step 1: Add `handleSkip`.**

Near `handleCombinedSend` (the existing send path), add:

```tsx
const handleSkip = useCallback(async () => {
  if (!sessionId || loading || isCompleted) return;
  const nodeId = currentQuestion?.node_id ?? null;
  if (!nodeId) return;

  setLoading(true);
  try {
    // Local user bubble first for snappy UX
    const localUser: ChatMessage = {
      id: `local-${Date.now()}`,
      role: 'user',
      content: '(skipped)',
      timestamp: new Date().toISOString(),
      skipped: true,
      questionId: nodeId,
    };
    setMessages((m) => [...m, localUser]);

    const res = await axios.post(
      `${API_URL}/api/v1/hybrid-chat/sessions/${sessionId}/message`,
      {
        message_type: 'skip',
        content: '',
        question_id: nodeId,
      },
      { headers: { Authorization: `Bearer ${token}` } },
    );

    const bot = res.data.bot_message;
    const botMsg: ChatMessage = {
      id: `bot-${Date.now()}`,
      role: 'assistant',
      content: bot.content,
      timestamp: new Date().toISOString(),
      questionOptions: bot.metadata?.options,
      questionId: bot.metadata?.node_id,
    };
    setMessages((m) => [...m, botMsg]);
    setProgress(res.data.progress_percentage ?? progress);
    if (res.data.is_complete) setIsCompleted(true);
    // Update currentQuestion from response metadata so the next render
    // shows the correct chips / Skip pill.
    setCurrentQuestion(bot.metadata ?? null);
  } catch (err: unknown) {
    setMessages((m) => m.filter((x) => x.id !== `local-${Date.now()}`));
    showToast('Could not skip. Try again.');
  } finally {
    setLoading(false);
  }
}, [sessionId, loading, isCompleted, currentQuestion, token, progress]);
```

(Names `setMessages`, `setLoading`, `setIsCompleted`, `setProgress`, `setCurrentQuestion`, `showToast`, `API_URL`, `token` are placeholders for whatever the file already calls them — read the surrounding code and substitute.)

- [ ] **Step 2: Pass `onSkip={handleSkip}` to McqOptions.**

Find the JSX where `<McqOptions ... />` is rendered and add the prop:

```tsx
<McqOptions
  ...existing props...
  onSkip={handleSkip}
/>
```

- [ ] **Step 3: Manual verify (end-to-end).**

`npm run dev` (frontend) + backend running. Log in as a test parent who has a school assignment. Advance the chat to `what_helps`. Click "Skip this question":

- A `(skipped)` italic bubble appears for the user.
- The bot's next message appears below.
- Progress bar advances.
- Click Skip on an MCQ question (only possible if you bypass the conditional render) — backend rejects with 400; toast appears.

- [ ] **Step 4: Commit.**

```bash
git add frontend/src/components/chat/HybridChat.tsx
git -c user.name="Edpsych" -c user.email="administrator@theedpsych.com" \
    commit -m "Chat: wire handleSkip POST + render skipped bubble"
```

---

## Task 9: Final smoke test

- [ ] **Step 1: Full UI walkthrough.**

1. Log in as admin. Create a fresh test student with a parent + school guardian.
2. Assign Parent assessment AND School assessment to the same student in one batch (Task 3 fix). Both succeed.
3. Log in as the parent (magic link). Run through the parent assessment, answering `Minimal contact` to a social question (Task 1 fix). Skip `anything_else` (Task 4-8). Complete the assessment.
4. Log in as the school user. Same drill — answer `Group work` to a free-text question, skip `hopes`. Complete.
5. Back as admin. Hit "Email school answers to parent" → PDF generated, neither skipped question visible. (Task 5 fix.)
6. Re-open the parent chat history → `(skipped)` bubble renders italic, no Edit pill on it.

- [ ] **Step 2: Push to akshay.**

```bash
git status   # should be clean
git log --oneline -10  # confirm 8 new commits
```

**STOP — ask the user before pushing.** Memory rule: "Always ask before git push." Wait for "push" / "push to akshay" before running `git push origin akshay`.

---

## Self-review

**Spec coverage:**
- Issue (a) gibberish + last-3-questions → Task 1.
- Issue (b) parent + school concurrent → Tasks 2, 3.
- Skip button → Tasks 4 (backend), 5 (reports), 6-8 (frontend).
- Issue (c) email already registered → out of scope (covered in spec; no work).

**Placeholder scan:** No "TBD"/"TODO"/"appropriate handling". Each step shows the actual code or an explicit "read the file first to substitute names" instruction (Task 8 step 1, 5 step 2-3) where the surrounding code shape isn't fixed. These note exactly what to substitute.

**Type consistency:**
- `assessment_data[<category>].skipped_nodes: list[str]` — used in Task 4, Task 5.
- `message_metadata.skipped: bool` — Task 4 step 4 sets, Task 6 reads (`message.skipped` after deserialisation).
- `ChatMessage.skipped?: boolean` — Task 6 adds, Tasks 7-8 reference.
- New `message_type: "skip"` value — Task 4 step 1 documents, Task 4 step 3 routes, Task 8 step 1 sends.

Names are consistent across tasks.
