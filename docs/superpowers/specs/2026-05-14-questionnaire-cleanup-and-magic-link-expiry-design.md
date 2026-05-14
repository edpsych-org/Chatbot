# Questionnaire Cleanup + Magic Link Expiry — Design

**Date:** 2026-05-14
**Branch:** `akshay`
**Trigger:** Two practitioner-reported issues:
1. Several parent-flow questions describe classroom-only behaviour that a parent cannot directly observe (e.g. "during class", "with classmates"). These belong in the school questionnaire.
2. Magic-link invitations expire in 48h. Parents typically open weekend-sent emails on Saturday/Sunday but invitations sent Mon/Tue have already expired by then.

## Issues addressed

1. **Misplaced parent questions.** 6 nodes in `parent_assessment_v1.json` ask about behaviour observable only at school. Remove them; trust school flow's existing analogues for 5 of them and add 1 new node to the school flow to cover the remaining gap (split-attention).
2. **Magic-link too short.** Bump invite-link expiry from 48h → 168h (7 days) so a Monday-sent invitation survives the weekend it'll likely be opened on. Email body text is templated dynamically and needs a small format helper so "168 hours" displays as "7 days".

## Out of scope

- No node renumbering of remaining parent-flow nodes. Stale historical `node_id` values stored in past `chat_messages.message_metadata` rows must keep working; renumbering would break analytics and historical reports.
- No split between invite-flavoured expiry and login-flavoured expiry (only one `MAGIC_LINK_EXPIRY_HOURS` setting). The generic login `create_magic_link` defaults to 24h independently in code and is unaffected.
- No re-categorisation of "borderline" parent questions (`school_motivation`, `homework_independence`, `homework_habits`, etc.). User confirmed these stay in parent flow — parents observe them at home.
- No `final_reports.generated_by_user_id` / `approved_by_user_id` `ondelete` fix (open issue in [LAPTOP_MIGRATION.md §8](../../../LAPTOP_MIGRATION.md)).

---

## Section 1 — Magic link expiry: 48h → 168h

### Problem

`MAGIC_LINK_EXPIRY_HOURS` at [backend/app/core/config.py:103](../../../backend/app/core/config.py#L103) is set to 48. All invite-flavoured callers use it:

- `admin.py` 4 sites — invite parent/school/psychologist user, manual link generation
- `assignments.py` 1 site — assignment creation
- `psychologist.py` 2 sites — psychologist account setup + re-invite
- `student_guardians.py` 2 sites — guardian welcome + re-invite

Email templates in `backend/app/utils/email.py` hard-code the unit: `"expires in {expiry_hours} hours"`. At 168h that string reads `"168 hours"` — awkward.

### Change

**Config bump.** Set default to 168 in [backend/app/core/config.py:103](../../../backend/app/core/config.py#L103):

```python
MAGIC_LINK_EXPIRY_HOURS: int = 168
```

If a `.env` overrides it, deployment environments should be updated to `168` too. (Not blocking — the default catches anything unset.)

**Email format helper.** Add to [backend/app/utils/email.py](../../../backend/app/utils/email.py):

```python
def _format_expiry(hours: int) -> str:
    """Human-friendly expiry string. '7 days' if a clean day count, else 'N hours'."""
    if hours > 0 and hours % 24 == 0:
        days = hours // 24
        return f"{days} day" if days == 1 else f"{days} days"
    return f"{hours} hour" if hours == 1 else f"{hours} hours"
```

Replace each `{expiry_hours} hours` occurrence in templates with `{expiry_label}`, where each template-rendering function computes `expiry_label = _format_expiry(expiry_hours)` once and substitutes. Five sites in `email.py`:

| Line | Template |
|---|---|
| 212 | Assessment invite (HTML) |
| 250 | Assessment invite (text) |
| 328 | Parent invitation (HTML, body) |
| 359 | Parent invitation (HTML, footer) |
| 377, 399 | Parent invitation (text) |

Note: line 212 reads `"expires in {expiry_hours} hours. If it expires, ask whoever invited you…"`. The "If it expires" wording is fine to keep — implies but does not contradict the expiry copy.

### Why a single setting suffices

The user-suggested option of "remove validity altogether" was explicitly rejected in favour of 7 days. Future re-bumps remain a one-line config change.

The generic `create_magic_link` (in [magic_link.py:23](../../../backend/app/utils/magic_link.py#L23)) defaults to `expiry_hours=24` and is called by the login fallback path — not from `settings.MAGIC_LINK_EXPIRY_HOURS`. So the login-link expiry stays short (24h) without further changes.

### Verification

- Send a fresh invite from admin UI on staging. Email body should read "expires in 7 days".
- `select expires_at from magic_link_tokens order by created_at desc limit 1;` should be ~168h after `created_at`.

---

## Section 2 — Parent flow: remove 6 classroom-only nodes

### Problem

Six nodes in [backend/flows/parent_assessment_v1.json](../../../backend/flows/parent_assessment_v1.json) ask about behaviour a parent cannot directly observe:

| Node | Approx. line | Question text |
|---|---|---|
| `attention_12` | 230 | "Can {student_name} do two things at once, such as listening to a teacher while taking notes?" |
| `attention_16` | 298 | "Does {student_name} seem to daydream or zone out during class or conversations?" |
| `academic_14` | 1311 | "Does {student_name} participate actively in classroom discussions and activities?" |
| `academic_15` | 1328 | "Does {student_name} learn at the same pace as their classmates?" |
| `academic_17` | 1362 | "Does {student_name} show creativity and original thinking in schoolwork?" |
| `academic_18` | 1379 | "How well does {student_name} organise school materials, assignments, and projects?" |

### Change

Delete each of the 6 node objects from the `nodes` map.

**Rewire `next` chain** so the deleted nodes are bypassed cleanly. Note: `academic_14`+`academic_15` and `academic_17`+`academic_18` are adjacent deletions, so their predecessors must skip over BOTH:

| Predecessor (option `next` values) | Was | Becomes |
|---|---|---|
| `attention_11` options | `attention_12` | `attention_13` |
| `attention_15` options | `attention_16` | `attention_17` |
| `academic_13` options | `academic_14` | `academic_16` (skips deleted `academic_15`) |
| `academic_16` options | `academic_17` | `academic_19` (skips deleted `academic_18`) |

Only 4 predecessor rewires are needed (not 6) because adjacent deletions consolidate. The internal pointers between adjacent deleted nodes (e.g. `academic_14` → `academic_15`) disappear with the deletion.

Predecessor option *labels* and *severity* metadata are unchanged. Only the `next` string changes.

### Why no renumbering

Renumbering remaining nodes (e.g. `attention_6` → `attention_5`) would:

- Bloat the diff (~50+ line changes for cosmetic gain).
- Break analytic queries that group on historical `node_id` strings.
- Break any existing chat sessions mid-flow if a backend-restart picks up the new flow file mid-conversation.

The "gap" in numbering (4, 6, 7, …) is internal-only and never user-visible.

### Verification

- `python -c "import json; json.load(open('backend/flows/parent_assessment_v1.json')); print('OK')"`
- Run reachability check (see Section 4).
- Start a fresh parent assessment from staging. Confirm questions about "in class", "with classmates", "creativity in schoolwork", "organising school materials" no longer appear.

---

## Section 3 — School flow: add `multitask` node

### Problem

5 of the 6 parent-flow deletions have a direct or close school-flow analogue (`attention_class`, `group_work`, `reading_level`/`writing_level`/`maths_level`, `subject_strength`, `task_completion`). The exception is split-attention / multitasking. The school flow has `attention_class` (sustained attention) and `instructions` (multi-step instructions) but nothing on doing two things simultaneously.

### Change

Insert one new node `multitask` between `attention_class` and `task_completion` in [backend/flows/school_assessment_v1.json](../../../backend/flows/school_assessment_v1.json). Wire:

```
attention_class (line 65) → multitask → task_completion (line 78) → instructions → academic_intro
```

Node body:

```json
"multitask": {
  "type": "mcq",
  "question": "Can {student_name} sustain attention to two things at once (e.g. listening to you while taking notes)?",
  "category": "attention",
  "options": [
    {"value": "comfortably", "label": "Comfortably — does both well", "next": "task_completion", "metadata": {"severity": "none"}},
    {"value": "with_effort", "label": "Manages with effort", "next": "task_completion", "metadata": {"severity": "low"}},
    {"value": "loses_one", "label": "Loses one thread quickly", "next": "task_completion", "metadata": {"severity": "medium"}},
    {"value": "cannot", "label": "Cannot — one task only", "next": "task_completion", "metadata": {"severity": "high"}}
  ],
  "allow_text": true,
  "text_prompt": "Classroom examples if helpful:"
}
```

Mutation: `attention_class` options' `next` change from `task_completion` to `multitask` (4 option lines).

### Why not also add `creativity` and `organisation` nodes

Per user decision in brainstorming: trust existing school nodes. `subject_strength` (free-text "shines in") gives space for creativity comments; `task_completion` covers organised work delivery. Adding more MCQs lengthens the school flow without strong evidence of need. Practitioners can revisit if reports show gaps.

### Verification

- JSON validate (as Section 2).
- Reachability check (Section 4) on school flow.
- Start a fresh school assessment from staging. Confirm `multitask` appears between attention and task-completion questions.

---

## Section 4 — Flow reachability validator script

### Problem

Hand-editing `next` pointers across a 1800-line JSON is error-prone. A typo (`attention_6` → `attention6`) leaves a dangling pointer; the chat would crash mid-conversation.

### Change

Add [backend/validate_flow.py](../../../backend/validate_flow.py):

- Loads a flow JSON.
- BFS from `start_node` following every `next` reference (top-level `next`, option `next`, message `next`).
- Asserts every `next` target exists in `nodes`.
- Reports orphaned nodes (defined but unreachable) and dangling references (referenced but undefined).
- Exit 0 on success, 1 on any failure.
- CLI: `python validate_flow.py flows/parent_assessment_v1.json`.

Reusable for all future flow edits.

### Verification

- Run against both flows after edits — both must exit 0 with no dangling refs.
- Deliberately introduce a typo locally, confirm script catches it, revert.

---

## Section 5 — Rollout

### Order

1. Branch is `akshay` (already current).
2. Edit `config.py` (1 line).
3. Edit `email.py` (helper + 5 template-site swaps).
4. Edit `parent_assessment_v1.json` (delete 6 nodes + rewire 6 predecessor option-`next` sets).
5. Edit `school_assessment_v1.json` (insert `multitask`, rewire `attention_class` options).
6. Add `backend/validate_flow.py`.
7. Run validator on both flows; run JSON validator on both flows.
8. Local smoke (per [LAPTOP_MIGRATION.md §12](../../../LAPTOP_MIGRATION.md)) — admin → invite → magic link → answer 2-3 questions → reach end → no missing-node errors.
9. Single commit. Single PR `akshay → staging`.
10. After staging deploy (~5 min), repeat smoke on `https://stage-cb.theedpsych.co.uk` with a real invite email — confirm "expires in 7 days" body text and the new question ordering.

### Commit message shape

Single bundled commit. No AI attribution. Subject under 70 chars:

```
flow: drop classroom-only parent qs, add school multitask, 7-day magic link
```

Body lists the 6 removals, the school addition, the config/email change, and the new validator script.

### PR strategy

One PR to staging. Per workflow convention (pragmatic bundle for related changes touching the assessment flow), reviewer sees the full restructure at once.

---

## Risks

- **Stale in-flight conversations.** A parent who started but hasn't finished an assessment when the flow file changes could land on a now-deleted `node_id` from `chat_messages.message_metadata`. Orchestrator already has a "skip without node_id" branch (commit `4b84daf`); same behaviour should kick in for unknown node_ids. Worth verifying before merge — if a fallback is needed, add to orchestrator separately.
- **Email "7 days" rendering.** If any email template caches the string at import time instead of per-call, the bump won't show. All current templates compute per-call from `expiry_hours` param; safe.
- **Severity-tag distribution shifts.** Removing 6 nodes (mostly low/medium severity) tilts the final-report severity histogram very slightly. The clinical assessor agent's aggregation is robust to count changes; no expected impact on report content.
