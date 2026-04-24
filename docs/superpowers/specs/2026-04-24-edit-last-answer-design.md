# Edit the Last Answer — Design

**Date:** 2026-04-24
**Status:** Approved for implementation planning

## Problem

Parents and schools sometimes realise the answer they just submitted
was wrong (tapped the wrong MCQ option, typed a typo, omitted a
detail). The chatbot currently has no way to correct a sent message —
they either live with the mistake or the psychologist has to clean it
up in the report.

## Goal

Let the respondent edit their most recent user message in the
session. The edit updates the stored message + the derived
`assessment_data` row, and confirms with a "Response saved" toast.
The bot's follow-up question stays in place.

## Non-goals

- Editing any message older than the most recent user bubble.
- Rolling back or regenerating bot responses.
- Branching re-route when the edit changes an MCQ option (the new
  option's value lands in `assessment_data`, but the conversation
  continues from the node the bot already asked next).
- Editing after the session is finalised / completed.
- Giving parents/schools edit access to each other's sessions.

## UX

### Trigger

A small pencil icon is rendered on the most-recent user bubble when
all of these are true:
- Bubble's message id equals the largest user-message id in the
  current session.
- `session.status != "completed"`.
- Session is loaded and editable (no save-in-flight).

Older bubbles do not show a pencil.

### Edit mode

Tap the pencil → bubble morphs into an inline edit panel:

- **If the message was an MCQ answer** (i.e. it carries a
  `resolved_option` in `message_metadata.selected_option`): render
  the same chip row that was shown when the question was asked, plus
  a textarea, plus **Save** / **Cancel** buttons. The textarea is
  prefilled with the bubble's current content. The chip matching the
  current `resolved_option` is preselected.
- **If the message was free text**: render a textarea prefilled with
  the current content, plus **Save** / **Cancel** buttons.

While the panel is open:
- The composer at the bottom (text box / chips / Send) is disabled
  so the respondent cannot queue a new answer mid-edit.
- Cancel restores the bubble exactly as it was before editing.

### Save behaviour

On **Save**:
1. Fire `PATCH /api/v1/hybrid-chat/sessions/{session_id}/messages/{message_id}`.
2. Body: `{ content: string, resolved_option: string | null }`.
3. On 200: replace the bubble's content/metadata with the response,
   re-enable the composer, show a small toast at the bottom:
   ✓ "Response saved" that auto-dismisses after 3 seconds.
4. On 4xx: keep edit panel open, surface the error under the
   textarea (red, 1-2 lines), do not change the bubble.
5. On network failure: keep panel open with inline "Couldn't save.
   Try again."

Pencil stays on the bubble after a successful edit so the user can
edit again if needed, until they send their next message (which
promotes that bubble to the new "latest" and strips the pencil from
the old one).

## Backend

### Endpoint

`PATCH /api/v1/hybrid-chat/sessions/{session_id}/messages/{message_id}`

Auth: `get_current_active_user`. Ownership check identical to the
existing `/sessions/{id}/message` route — the requester is either
the session's `user_id` OR role == `ADMIN`.

Request schema (`EditMessageIn`):
```
content: str   # required, stripped length >= 1
resolved_option: Optional[str]  # None for free-text edits
```

### Validation (all 400 with specific detail)

1. Session not found or ownership check fails → 404.
2. `session.status == "completed"` → 400 "This has already been completed".
3. Message not found or not in this session → 404.
4. Message role != `"user"` → 400 "Only your own messages can be edited".
5. Message id != `max(id)` of user messages for this session → 400 "Only the latest answer can be edited".
6. `content.strip()` empty AND `resolved_option` is null → 400 "Answer cannot be empty".
7. `resolved_option` provided but the referenced node has no matching option → 400 "Invalid option".
8. `resolved_option` is null but the node is MCQ-only (no `allow_text` equivalent accepted for free text) — same node must still allow free text (every node effectively does today; enforce by trusting the existing combined layout). Skip strict rejection here.

### Mutation (single transaction, `SELECT ... FOR UPDATE` on the session row)

1. Update `ChatMessage.content` = new content.
2. Update `ChatMessage.message_metadata`:
   - `selected_option` = new `resolved_option` (or removed if null)
   - add `edited_at` = now (for audit)
3. Resolve the question node from `message_metadata.question_id`.
4. Compute the category for that node (fallback "general").
5. Recompute `assessment_data[category]`:
   - If `resolved_option` set: call the existing `_store_mcq_answer`
     helper (it already handles severity + elaboration) with the
     computed elaboration (content minus option label, or None if
     they match).
   - If `resolved_option` null: delete
     `assessment_data[category].mcq_answers[node_id]`, set
     `assessment_data[category].elaborations[node_id] = content`,
     recompute severity if the category's current severity came from
     the now-deleted option (best-effort: leave as-is; psychologist
     can re-judge from elaboration).
6. `flag_modified(session, "context_data")`.
7. Commit.

Response (200):
```
{
  "id": "...",
  "content": "...",
  "message_metadata": { ... },
  "edited_at": "2026-04-24T..."
}
```

### Race protection

The `SELECT ... FOR UPDATE` on the session row serialises any
concurrent PATCH with an in-flight `/sessions/{id}/message` call.
If a new message lands first, the edit request fails validation #5
("not the latest") and the frontend re-syncs.

## Frontend

| File | Change |
|---|---|
| `src/types/chat.ts` | Add `resolvedOption?: string \| null` to `ChatMessage`; add `EditMessagePayload` type |
| `src/components/chat/MessageBubble.tsx` | New props: `isLatestUserMessage`, `canEdit`, `onEditSubmit`, `onEditCancel`. Render pencil button when editable. Internal state for open/closed edit mode + textarea value + picked option |
| `src/components/chat/MessageList.tsx` | Compute `lastUserMessageId` once per render, pass `isLatestUserMessage={msg.id === lastUserMessageId}` to each bubble |
| `src/components/chat/HybridChat.tsx` | `handleEditSubmit(messageId, content, resolvedOption)` → PATCH → on success merge into `messages` state + fire "Response saved" toast; disable composer while any bubble is in edit mode via existing `loading` flag |
| `src/components/chat/EditToast.tsx` (new, tiny) | Fixed-position success toast ("Response saved") with 3s auto-dismiss; renders via portal |

The existing `McqOptions` component is reused inside MessageBubble's
edit mode — pass the message's question options (read from the
preceding bot message's metadata).

## Data model

No schema changes. The edit reuses existing columns:
- `chat_messages.content` — replaced in place.
- `chat_messages.message_metadata` — gains `edited_at`; existing
  `selected_option` is updated or removed.
- `chat_sessions.context_data["assessment_data"]` — mcq_answers,
  elaborations, severity updated per rules above.

## Testing

1. Parent submits an MCQ answer with elaboration, sees the bot's
   next question, clicks pencil, picks a different chip, changes
   the typed text, saves → bubble updates, toast appears, DB row
   reflects new mcq_answer + elaboration + severity, `edited_at` set.
2. Parent edits a free-text answer (no chip) → content + elaboration
   updated; `mcq_answers` unchanged for that node.
3. Parent opens pencil, sends a new message from another tab, then
   clicks Save in the first tab → 400 "Only the latest answer can
   be edited"; UI refetches and removes pencil from now-stale bubble.
4. Parent clears both text and option, clicks Save → 400 "Answer
   cannot be empty"; edit mode stays open with inline error.
5. Admin hits PATCH on a parent's session → allowed (admin bypass).
6. Session is COMPLETED (thank-you screen) → pencil not rendered;
   direct PATCH from curl → 400.
7. PATCH race: fire `/message` and `/messages/{id}` concurrently —
   whichever reaches the row lock first wins; the other returns a
   clean 400.
