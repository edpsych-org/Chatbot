# MCQ with Elaboration — Design

**Date:** 2026-04-22
**Status:** Approved for implementation planning

## Problem

Every MCQ node in the chatbot currently forces a binary UX: the user
either clicks an option OR types free text in its place. Parents and
schools routinely want to do both — pick a graded answer ("Sometimes")
AND explain ("only during maths"). Today that context is lost.

## Goal

For every MCQ node where `allow_text: true`, let the user:

1. Pick exactly one option.
2. Optionally add free-text elaboration in the same submit.

The picked option drives branching. The text is stored alongside as
elaboration and surfaces in the psychologist's reports.

## Non-goals

- Changing branching logic for nodes without `allow_text`.
- Re-running the free-text relevance validator on elaborations — when
  an option is committed we trust the user.
- Supporting multiple option picks. The MCQ radio model is unchanged.
- Retroactively enriching answers from prior sessions.

## UX

New layout per `allow_text: true` MCQ:

```
┌─────────────────────────────────────────┐
│  [ text box (prefilled on option pick)] │  editable, multi-line
├─────────────────────────────────────────┤
│  [ Yes, often ]  [ Sometimes ]          │  option chips
│  [ Rarely ]      [ Never ]              │
├─────────────────────────────────────────┤
│                              [ Send ]   │
└─────────────────────────────────────────┘
```

Rules:

- Text box sits ON TOP, chips BELOW. (Explicit per the user.)
- Clicking a chip sets the text box value to the option's `label` and
  stores `resolved_option = option.value` in local component state.
  The chip renders as selected (highlight).
- The user can edit / append / delete text after picking. The picked
  option remains selected; the text change does not clear it.
- Picking a different chip:
  - If the current text is unchanged from the previously-picked label,
    silently overwrite.
  - If the user typed past the label, prompt a small inline confirm
    ("Replace your text with the new option?") with Yes / Cancel.
- Send enabled when EITHER an option is picked OR text is non-empty.
- Enter (without Shift) sends; Shift+Enter inserts a newline.

Nodes with `allow_text: false` render options only, unchanged.

## Decision: option wins for branching

When both an option is picked and the text is edited, the option's
`next` path determines the next node. Rationale: matches the user's
stated intent ("select option AND type extra"); fast and deterministic
with no LLM on the critical path. If a parent writes something that
contradicts the chip they picked, the psychologist sees both in the
elaboration field and can judge — better than silently routing to a
different question based on fuzzy text interpretation.

## Backend contract

`ChatMessageInput` already carries both `content` and
`resolved_option`. No schema change.

Routing in `send_message`:

| `message_type` | `resolved_option` | Path |
|---|---|---|
| `mcq_choice` | set | NEW: `_handle_mcq_choice` extended to capture elaboration |
| `mcq_choice` | unset / `continue` / `more` | existing quick-reply paths unchanged |
| `free_text` | — | unchanged |

Extended `_handle_mcq_choice` behaviour:

1. Mark current node answered (unchanged).
2. Look up the picked option on the current node to get its label and
   branching metadata.
3. Call `_store_mcq_answer` — extended to also persist elaboration.
4. If `content.strip()` differs from the option's `label`, store the
   stripped text as elaboration on the same answer entry.
5. Skip the free-text validator — the option is already a commitment.
6. Use `option.next` for branching (unchanged).

Shape of each answer row in `session.context_data["assessment_data"]`:

```json
{
  "attention_1": {
    "option": "sometimes",
    "label": "Sometimes",
    "severity": "medium",
    "elaboration": "only during maths",
    "timestamp": "2026-04-22T09:12:45Z"
  }
}
```

`elaboration` is absent when none was provided. Existing consumers
reading `option` / `severity` keep working.

## Agent prompts

`BackgroundSummaryAgent` and `AssessmentAgent` receive
`assessment_data` via the orchestrator's context summary. Add a small
instruction to their prompts: when an answer has an `elaboration`
field, quote or paraphrase it alongside the option so the narrative
reflects the parent's words.

## Edge cases

- **Empty text after picking option:** send with `content =
  option.label`. Backend detects no elaboration (label equals content)
  and stores the option only.
- **Text typed, no option picked, `allow_text: true`:** falls through
  to the existing `_handle_free_text` path — validator runs, empathy
  agent replies.
- **Text typed + option picked + different option picked:** inline
  confirm; on Yes, replace the text with the new label and update
  `resolved_option`; on Cancel, keep current text and current option.
- **Node with `allow_text: false`:** the composite layout degrades —
  text box hidden, chips render as before, click sends immediately.
- **Old sessions resumed mid-flow:** no data migration needed. New
  answers use the new shape; old answers keep the old shape.

## Files

| Kind | Path | Change |
|---|---|---|
| edit | `frontend/src/components/chat/McqOptions.tsx` | Render text box + chips + Send; emit `{ content, resolved_option }` |
| edit | `frontend/src/components/chat/HybridChat.tsx` | Pass `resolved_option` alongside `content` for MCQ submits; keep free-text fallback |
| edit | `frontend/src/types/chat.ts` | Optional: surface `elaboration` on rendered message if we want to show the parent's own words inline |
| edit | `backend/app/api/hybrid_chat.py` | Extend `_handle_mcq_choice` + `_store_mcq_answer` for elaboration |
| edit | `backend/app/agents/assessor.py` | Prompt nudge: use elaboration text when present |
| edit | `backend/app/agents/background.py` | Same prompt nudge |

No flow JSON edits. No migration.

## Verification

1. Parent flow `attention_1`: click "Sometimes" → text box fills with
   "Sometimes" → append " only during maths" → Send. Verify
   `assessment_data.attention_1` has
   `option="sometimes"`, `elaboration="only during maths"`, and the
   next bot message asks `attention_2`.
2. Same node: click "Rarely" without editing → Send. Verify no
   `elaboration` key is stored.
3. Same node: type "he zones out a lot" without clicking → Send.
   Verify the free-text path runs (validator, empathy) and
   `attention_1` is NOT marked answered via the MCQ branch.
4. School flow `classroom_attention`: same three cases.
5. Generate Background Summary after a mix of elaborated + plain
   answers — verify the narrative reflects the parent's typed words
   where they were provided.
6. Node with `allow_text: false` (if any remain in the flows): chips
   only, click sends immediately, no text box rendered.
