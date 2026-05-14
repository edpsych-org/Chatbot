# Questionnaire Cleanup + Magic Link Expiry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove 6 classroom-only questions from the parent assessment flow, add one split-attention question to the school flow, and extend magic-link invitation expiry from 48 hours to 7 days (with friendly "7 days" copy in invite emails).

**Architecture:** Three independent edits in one PR — (a) one-line config bump + email-template format helper in `backend/`, (b) JSON edits in `backend/flows/`, (c) new reachability-validator utility script as a guardrail. Single bundled PR `akshay → staging`. No schema migration. No new dependencies.

**Tech Stack:** Python 3.11, FastAPI, pytest 7.4.4, JSON flow files, Git.

**Spec:** [`docs/superpowers/specs/2026-05-14-questionnaire-cleanup-and-magic-link-expiry-design.md`](../specs/2026-05-14-questionnaire-cleanup-and-magic-link-expiry-design.md)

---

## File Structure

**Created:**
- `backend/validate_flow.py` — reachability checker for flow JSONs (reusable utility)
- `backend/tests/__init__.py` — empty marker
- `backend/tests/test_email_helpers.py` — pytest for `_format_expiry`

**Modified:**
- `backend/app/core/config.py` — one default value
- `backend/app/utils/email.py` — add helper + swap 5 template strings
- `backend/flows/parent_assessment_v1.json` — delete 6 nodes, rewire 6 predecessor option-`next` sets
- `backend/flows/school_assessment_v1.json` — insert 1 node, rewire 1 predecessor option-`next` set

**Untouched (verified during plan):** `magic_link.py`, `assignments.py`, `admin.py`, `psychologist.py`, `student_guardians.py`, orchestrator. They reference `settings.MAGIC_LINK_EXPIRY_HOURS` and pick up the new value automatically.

---

### Task 1: Add test infrastructure + failing test for `_format_expiry`

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_email_helpers.py`

- [ ] **Step 1: Create empty package marker**

```bash
touch backend/tests/__init__.py
```

- [ ] **Step 2: Write the failing test**

Create `backend/tests/test_email_helpers.py`:

```python
"""Tests for email template helpers."""
from app.utils.email import _format_expiry


def test_format_expiry_one_day():
    assert _format_expiry(24) == "1 day"


def test_format_expiry_seven_days():
    assert _format_expiry(168) == "7 days"


def test_format_expiry_two_days():
    assert _format_expiry(48) == "2 days"


def test_format_expiry_one_hour():
    assert _format_expiry(1) == "1 hour"


def test_format_expiry_non_day_multiple():
    assert _format_expiry(36) == "36 hours"


def test_format_expiry_zero_hours():
    # Edge: zero should be "0 hours" not "0 days"
    assert _format_expiry(0) == "0 hours"
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_email_helpers.py -v
```

Expected: FAIL with `ImportError: cannot import name '_format_expiry' from 'app.utils.email'`.

- [ ] **Step 4: Commit failing test**

```bash
cd d:/Chatbot
git add backend/tests/__init__.py backend/tests/test_email_helpers.py
git commit -m "test: add _format_expiry pytest cases"
```

---

### Task 2: Implement `_format_expiry` helper

**Files:**
- Modify: `backend/app/utils/email.py` (add helper near top of file, after the imports and constants block, before the `send_invite_email`-style functions)

- [ ] **Step 1: Add the helper function**

Find the `DEFAULT_LINK_EXPIRY_HOURS = settings.MAGIC_LINK_EXPIRY_HOURS` line (around line 26). Immediately after it, add:

```python


def _format_expiry(hours: int) -> str:
    """Human-friendly expiry string. Returns '7 days' for clean day counts, else 'N hours'."""
    if hours > 0 and hours % 24 == 0:
        days = hours // 24
        return f"{days} day" if days == 1 else f"{days} days"
    return f"{hours} hour" if hours == 1 else f"{hours} hours"
```

- [ ] **Step 2: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/test_email_helpers.py -v
```

Expected: 6 passed.

- [ ] **Step 3: Commit**

```bash
cd d:/Chatbot
git add backend/app/utils/email.py
git commit -m "feat(email): add _format_expiry helper for human-friendly expiry copy"
```

---

### Task 3: Update email templates to use `expiry_label`

**Files:**
- Modify: `backend/app/utils/email.py` (5 template-string sites)

Each template function takes `expiry_hours: int` as a parameter. Compute `expiry_label = _format_expiry(expiry_hours)` once at the top of each function body and substitute into the template strings.

- [ ] **Step 1: Edit the assessment invite (HTML) — around line 212**

Find:

```html
                ⏰ This invitation link expires in {expiry_hours} hours. If it expires, ask whoever invited you to send a new one.
```

Replace with:

```html
                ⏰ This invitation link expires in {expiry_label}. If it expires, ask whoever invited you to send a new one.
```

- [ ] **Step 2: Edit the assessment invite (text) — around line 250**

Find:

```
Note: this link expires in {expiry_hours} hours. If it expires, ask {psychologist_name} for a new one.
```

Replace with:

```
Note: this link expires in {expiry_label}. If it expires, ask {psychologist_name} for a new one.
```

- [ ] **Step 3: Edit parent invitation (HTML body) — around line 328**

Find:

```html
                    The link is secure and signs you in automatically. It is valid for {expiry_hours} hours.
```

Replace with:

```html
                    The link is secure and signs you in automatically. It is valid for {expiry_label}.
```

- [ ] **Step 4: Edit parent invitation (HTML footer) — around line 359**

Find:

```html
            <p>The login link expires in {expiry_hours} hours for your security.</p>
```

Replace with:

```html
            <p>The login link expires in {expiry_label} for your security.</p>
```

- [ ] **Step 5: Edit parent invitation (text body + footer) — around lines 377 and 399**

Find both occurrences:

```
The link is valid for {expiry_hours} hours.
```

and:

```
The login link expires in {expiry_hours} hours for your security.
```

Replace with:

```
The link is valid for {expiry_label}.
```

and:

```
The login link expires in {expiry_label} for your security.
```

- [ ] **Step 6: Add `expiry_label = _format_expiry(expiry_hours)` to each template-rendering function that uses these strings**

For each function whose body contains `{expiry_label}` in an f-string or `.format()` call: locate the first line of the function body and add (after any other local var assignments, before the `subject = ...` / `html_body = ...` blocks):

```python
    expiry_label = _format_expiry(expiry_hours)
```

The functions to update are those that previously embedded `expiry_hours` directly in template strings. In the current file these are the two invitation functions: `send_invite_email` (or whatever the assessment invite is named — the one containing line 212) and `send_parent_invitation_email` (around line 272). Verify by grepping after edits:

```bash
grep -n "expiry_label" backend/app/utils/email.py
```

You should see one assignment per affected function and N usages per template.

- [ ] **Step 7: Verify no orphan `{expiry_hours}` remains in template strings**

```bash
grep -n "{expiry_hours}" backend/app/utils/email.py
```

Expected: no matches (the function *parameter* `expiry_hours: int = DEFAULT_LINK_EXPIRY_HOURS` is fine — only template-string occurrences inside f-strings / format strings should be gone).

- [ ] **Step 8: Smoke-import**

```bash
cd backend && python -c "from app.utils.email import _format_expiry; print(_format_expiry(168))"
```

Expected output: `7 days`

- [ ] **Step 9: Re-run tests**

```bash
cd backend && python -m pytest tests/test_email_helpers.py -v
```

Expected: 6 passed.

- [ ] **Step 10: Commit**

```bash
cd d:/Chatbot
git add backend/app/utils/email.py
git commit -m "feat(email): use expiry_label in invitation templates"
```

---

### Task 4: Bump `MAGIC_LINK_EXPIRY_HOURS` default to 168

**Files:**
- Modify: `backend/app/core/config.py:103`

- [ ] **Step 1: Read the current line**

```bash
grep -n "MAGIC_LINK_EXPIRY_HOURS" backend/app/core/config.py
```

Expected: `103:    MAGIC_LINK_EXPIRY_HOURS: int = 48`

- [ ] **Step 2: Replace the value**

Edit `backend/app/core/config.py` line 103. Find:

```python
    MAGIC_LINK_EXPIRY_HOURS: int = 48
```

Replace with:

```python
    MAGIC_LINK_EXPIRY_HOURS: int = 168  # 7 days — invitation links sent Mon often opened on weekend
```

- [ ] **Step 3: Verify**

```bash
grep -n "MAGIC_LINK_EXPIRY_HOURS" backend/app/core/config.py
```

Expected: line 103 shows `168`.

- [ ] **Step 4: Commit**

```bash
cd d:/Chatbot
git add backend/app/core/config.py
git commit -m "config: extend magic link expiry from 48h to 7 days"
```

---

### Task 5: Create flow reachability validator

**Files:**
- Create: `backend/validate_flow.py`

- [ ] **Step 1: Write the script**

Create `backend/validate_flow.py`:

```python
"""Validate a flow JSON: ensure every `next` reference resolves to a defined node.

Usage:
    python validate_flow.py flows/parent_assessment_v1.json
    python validate_flow.py flows/school_assessment_v1.json

Exit code 0 if all `next` targets resolve and the start node is set.
Exit code 1 otherwise; dangling references and orphan nodes are printed to stderr.
"""
import json
import sys
from collections import deque


def _collect_next_targets(node: dict) -> list[str]:
    """Return all string values found at any 'next' key inside the node."""
    targets: list[str] = []
    top = node.get("next")
    if isinstance(top, str):
        targets.append(top)
    for option in node.get("options", []) or []:
        nxt = option.get("next") if isinstance(option, dict) else None
        if isinstance(nxt, str):
            targets.append(nxt)
    return targets


def validate(flow_path: str) -> int:
    with open(flow_path, "r", encoding="utf-8") as handle:
        flow = json.load(handle)

    nodes: dict = flow.get("nodes", {})
    start = flow.get("start_node")
    errors: list[str] = []

    if not start:
        errors.append("flow has no `start_node`")
    elif start not in nodes:
        errors.append(f"start_node `{start}` is not defined in `nodes`")

    dangling: list[tuple[str, str]] = []
    for node_id, node in nodes.items():
        for target in _collect_next_targets(node):
            if target not in nodes:
                dangling.append((node_id, target))

    reachable: set[str] = set()
    if start in nodes:
        queue: deque[str] = deque([start])
        while queue:
            current = queue.popleft()
            if current in reachable:
                continue
            reachable.add(current)
            for target in _collect_next_targets(nodes.get(current, {})):
                if target in nodes and target not in reachable:
                    queue.append(target)

    orphans = sorted(set(nodes.keys()) - reachable)

    if dangling:
        for src, tgt in dangling:
            errors.append(f"dangling next: `{src}` -> `{tgt}` (target not defined)")
    if orphans:
        errors.append(f"unreachable node(s): {orphans}")

    if errors:
        for msg in errors:
            print(f"[FAIL] {flow_path}: {msg}", file=sys.stderr)
        return 1

    print(f"[OK] {flow_path}: {len(nodes)} nodes, all reachable, all `next` targets resolve.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_flow.py <flow.json>", file=sys.stderr)
        sys.exit(2)
    sys.exit(validate(sys.argv[1]))
```

- [ ] **Step 2: Run baseline against both flows (pre-edit)**

```bash
cd backend
python validate_flow.py flows/parent_assessment_v1.json
python validate_flow.py flows/school_assessment_v1.json
```

Expected: both print `[OK] ... all reachable, all next targets resolve.` Exit code 0.

If either fails on the baseline, the flow already had a problem — investigate before continuing. Do not start the JSON edits until baseline passes.

- [ ] **Step 3: Commit**

```bash
cd d:/Chatbot
git add backend/validate_flow.py
git commit -m "tools: add validate_flow.py reachability checker"
```

---

### Task 6: Parent flow — delete 6 nodes

**Files:**
- Modify: `backend/flows/parent_assessment_v1.json`

Six nodes to delete. Approximate line numbers for orientation only; locate the exact node by its quoted ID key (e.g. `"attention_5": {`) and delete the entire object including its trailing comma.

| Node | Approx. line |
|---|---|
| `attention_5` | 111 |
| `attention_11` | 213 |
| `academic_12` | 1277 |
| `academic_14` | 1311 |
| `academic_16` | 1345 |
| `academic_18` | 1379 |

- [ ] **Step 1: Delete `attention_5`**

Open `backend/flows/parent_assessment_v1.json`. Find:

```json
    "attention_5": {
```

Delete the entire object from the opening `"attention_5":` through the closing `},` (inclusive). Make sure no leading/trailing commas are left dangling.

- [ ] **Step 2: Delete `attention_11`**

Same process — find `"attention_11": {`, delete through closing `},`.

- [ ] **Step 3: Delete `academic_12`**

Same process — `"academic_12": {` through closing `},`.

- [ ] **Step 4: Delete `academic_14`**

Same process.

- [ ] **Step 5: Delete `academic_16`**

Same process.

- [ ] **Step 6: Delete `academic_18`**

Same process.

- [ ] **Step 7: JSON-parse check**

```bash
cd backend
python -c "import json; json.load(open('flows/parent_assessment_v1.json')); print('JSON OK')"
```

Expected: `JSON OK`. If you see a `JSONDecodeError` about an unexpected `,` or `}`, you left a dangling comma — fix it. After all six deletions the file should still be a valid JSON object.

- [ ] **Step 8: Run reachability validator (expect FAIL)**

```bash
python validate_flow.py flows/parent_assessment_v1.json
```

Expected: FAIL. The validator should now report dangling `next` references to all 6 deleted node IDs from their predecessors:

```
[FAIL] ...: dangling next: `attention_4` -> `attention_5` (target not defined)
[FAIL] ...: dangling next: `attention_10` -> `attention_11` (target not defined)
[FAIL] ...: dangling next: `academic_11` -> `academic_12` (target not defined)
[FAIL] ...: dangling next: `academic_13` -> `academic_14` (target not defined)
[FAIL] ...: dangling next: `academic_15` -> `academic_16` (target not defined)
[FAIL] ...: dangling next: `academic_17` -> `academic_18` (target not defined)
```

These dangling refs are what Task 7 fixes. Do **not** commit yet — keep the deletions and rewires in one commit.

---

### Task 7: Parent flow — rewire 6 predecessor `next` chains

**Files:**
- Modify: `backend/flows/parent_assessment_v1.json` (same file as Task 6 — combined into one commit)

Each predecessor node has 4 MCQ options (sometimes more). All option-level `next` values currently pointing to a deleted node must be retargeted to the deleted node's former successor.

| Predecessor | Find option `next` | Replace with |
|---|---|---|
| `attention_4` (around line 94) | `"next": "attention_5"` | `"next": "attention_6"` |
| `attention_10` (around line 196) | `"next": "attention_11"` | `"next": "attention_12"` |
| `academic_11` (around line 1260) | `"next": "academic_12"` | `"next": "academic_13"` |
| `academic_13` (around line 1294) | `"next": "academic_14"` | `"next": "academic_15"` |
| `academic_15` (around line 1328) | `"next": "academic_16"` | `"next": "academic_17"` |
| `academic_17` (around line 1362) | `"next": "academic_18"` | `"next": "academic_19"` |

- [ ] **Step 1: Rewire `attention_4` options**

Inside the `attention_4` node's `options` array, all 4 occurrences of `"next": "attention_5"` become `"next": "attention_6"`.

Use Edit with `replace_all` scoped to the file — but cross-check with grep first because the same string might appear elsewhere if `attention_5` was referenced from anywhere besides `attention_4`. After the deletions in Task 6 the only remaining references *should* be from `attention_4`:

```bash
grep -n '"next": "attention_5"' backend/flows/parent_assessment_v1.json
```

Expected: 4 matches, all inside the `attention_4` block. If so, safe to `replace_all`.

Apply the edit.

- [ ] **Step 2: Rewire `attention_10` options**

Same pattern:

```bash
grep -n '"next": "attention_11"' backend/flows/parent_assessment_v1.json
```

Expected: 4 matches inside `attention_10`. Replace `"next": "attention_11"` → `"next": "attention_12"`.

- [ ] **Step 3: Rewire `academic_11` options**

```bash
grep -n '"next": "academic_12"' backend/flows/parent_assessment_v1.json
```

Expected: 4 matches inside `academic_11`. Replace `"next": "academic_12"` → `"next": "academic_13"`.

- [ ] **Step 4: Rewire `academic_13` options**

```bash
grep -n '"next": "academic_14"' backend/flows/parent_assessment_v1.json
```

Expected: 4 matches inside `academic_13`. Replace `"next": "academic_14"` → `"next": "academic_15"`.

- [ ] **Step 5: Rewire `academic_15` options**

```bash
grep -n '"next": "academic_16"' backend/flows/parent_assessment_v1.json
```

Expected: 4 matches inside `academic_15`. Replace `"next": "academic_16"` → `"next": "academic_17"`.

- [ ] **Step 6: Rewire `academic_17` options**

```bash
grep -n '"next": "academic_18"' backend/flows/parent_assessment_v1.json
```

Expected: 4 matches inside `academic_17`. Replace `"next": "academic_18"` → `"next": "academic_19"`.

- [ ] **Step 7: Verify no references remain to deleted nodes**

```bash
grep -E '"(attention_5|attention_11|academic_12|academic_14|academic_16|academic_18)"' backend/flows/parent_assessment_v1.json
```

Expected: no output (no remaining references anywhere).

- [ ] **Step 8: JSON-parse check**

```bash
cd backend
python -c "import json; json.load(open('flows/parent_assessment_v1.json')); print('JSON OK')"
```

Expected: `JSON OK`.

- [ ] **Step 9: Run reachability validator**

```bash
python validate_flow.py flows/parent_assessment_v1.json
```

Expected: `[OK] flows/parent_assessment_v1.json: N nodes, all reachable, all next targets resolve.` where N is the previous count minus 6.

- [ ] **Step 10: Commit deletions + rewires together**

```bash
cd d:/Chatbot
git add backend/flows/parent_assessment_v1.json
git commit -m "flow(parent): drop 6 classroom-only nodes and rewire predecessors"
```

---

### Task 8: School flow — insert `multitask` node + rewire `attention_class`

**Files:**
- Modify: `backend/flows/school_assessment_v1.json`

- [ ] **Step 1: Insert the `multitask` node**

Open `backend/flows/school_assessment_v1.json`. Find the `attention_class` node (around line 65) — its closing `},` ends around line 77. Immediately after the `attention_class` block (and before `task_completion`), insert:

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
    },
```

Ensure the preceding node's closing `},` is correct and the new block's trailing comma is present (because `task_completion` follows).

- [ ] **Step 2: Rewire `attention_class` options to point to `multitask`**

`attention_class` currently has 4 options all with `"next": "task_completion"`. Replace each with `"next": "multitask"`.

```bash
grep -n '"next": "task_completion"' backend/flows/school_assessment_v1.json
```

Expected before edit: 4 matches inside `attention_class`.

After your edit, those 4 references move from `attention_class` options to `multitask` options. Verify:

```bash
grep -n '"next": "task_completion"' backend/flows/school_assessment_v1.json
```

Expected after edit: 4 matches, now all inside the new `multitask` block.

- [ ] **Step 3: JSON-parse check**

```bash
cd backend
python -c "import json; json.load(open('flows/school_assessment_v1.json')); print('JSON OK')"
```

Expected: `JSON OK`.

- [ ] **Step 4: Run reachability validator**

```bash
python validate_flow.py flows/school_assessment_v1.json
```

Expected: `[OK] flows/school_assessment_v1.json: N nodes, all reachable, all next targets resolve.` where N is the previous count + 1.

- [ ] **Step 5: Confirm `multitask` is reachable from `welcome` (trace)**

Add a one-shot trace to confirm the new node appears in the natural path. Run:

```bash
python - <<'PY'
import json, collections
flow = json.load(open('flows/school_assessment_v1.json'))
nodes = flow['nodes']
start = flow['start_node']
seen, order = set(), []
q = collections.deque([start])
while q:
    n = q.popleft()
    if n in seen: continue
    seen.add(n); order.append(n)
    node = nodes[n]
    if isinstance(node.get('next'), str): q.append(node['next'])
    for opt in node.get('options', []) or []:
        if isinstance(opt.get('next'), str): q.append(opt['next'])
print('multitask in BFS order:', 'multitask' in order)
print('position from start:', order.index('multitask') if 'multitask' in order else 'NOT FOUND')
PY
```

Expected: `multitask in BFS order: True`, position near `attention_class`.

- [ ] **Step 6: Commit**

```bash
cd d:/Chatbot
git add backend/flows/school_assessment_v1.json
git commit -m "flow(school): add multitask node between attention_class and task_completion"
```

---

### Task 9: Final integrity check across the whole branch

**Files:** (no edits — pure verification)

- [ ] **Step 1: Re-run all tests**

```bash
cd backend
python -m pytest tests/ -v
```

Expected: 6 passed (the email helper tests). No collection errors.

- [ ] **Step 2: Re-run reachability validator on both flows**

```bash
python validate_flow.py flows/parent_assessment_v1.json
python validate_flow.py flows/school_assessment_v1.json
```

Expected: both `[OK]`. Exit code 0 for both.

- [ ] **Step 3: Re-confirm no orphan template references**

```bash
grep -n "{expiry_hours}" backend/app/utils/email.py
```

Expected: no matches inside template strings (parameter declarations like `expiry_hours: int = DEFAULT_LINK_EXPIRY_HOURS` are fine if they appear — they're function signatures, not template substitutions). If grep matches anything that's a template, fix and re-run.

- [ ] **Step 4: Confirm deleted parent nodes are truly gone**

```bash
grep -nE '"(attention_5|attention_11|academic_12|academic_14|academic_16|academic_18)"' backend/flows/parent_assessment_v1.json
```

Expected: no output.

- [ ] **Step 5: Confirm `multitask` exists in school flow exactly once as a defined node**

```bash
grep -c '"multitask":' backend/flows/school_assessment_v1.json
```

Expected: `1` (the node definition; option `next` references use `"next": "multitask"` which is a different string).

- [ ] **Step 6: Quick git log review**

```bash
git log --oneline origin/akshay..HEAD
```

Expected: 6 commits — `test: add _format_expiry pytest cases`, `feat(email): add _format_expiry helper`, `feat(email): use expiry_label in invitation templates`, `config: extend magic link expiry…`, `tools: add validate_flow.py reachability checker`, `flow(parent): drop 6 classroom-only nodes and rewire predecessors`, `flow(school): add multitask node…` — plus the spec doc commit `docs: spec for questionnaire cleanup…` already on the branch.

(Note: that totals 7 + spec; if you see something unexpected, investigate before pushing.)

---

### Task 10: Push and open PR — **PAUSE FOR USER APPROVAL**

**Files:** (none — git remote operation)

Per repo convention, never `git push` without explicit user approval, even after passing local checks.

- [ ] **Step 1: Pause and ask the user**

Show the user the commit summary from Task 9 Step 6 and ask:

> "All local checks pass. Ready to push `akshay` to `origin` and open a PR to `staging`. Proceed?"

Wait for explicit "yes" / "push" / equivalent before continuing.

- [ ] **Step 2: Push the branch**

After approval:

```bash
cd d:/Chatbot
git push origin akshay
```

Expected: push succeeds.

- [ ] **Step 3: Open PR with `gh`**

```bash
gh pr create --base staging --head akshay --title "Questionnaire cleanup + 7-day magic link expiry" --body "$(cat <<'EOF'
## Summary

- Removes 6 classroom-only questions from the parent assessment flow (`attention_5`, `attention_11`, `academic_12`, `academic_14`, `academic_16`, `academic_18`). Parents cannot directly observe these; school flow already covers analogues.
- Adds one new `multitask` question to the school flow (between `attention_class` and `task_completion`) — covers split-attention, the only parent-flow concern without a clean school analogue.
- Extends magic-link invitation expiry from 48 hours to 7 days (`MAGIC_LINK_EXPIRY_HOURS: 48 → 168`). Adds `_format_expiry` helper so invite emails read "expires in 7 days" instead of "168 hours".
- Adds `backend/validate_flow.py` reachability checker as a reusable guardrail for future flow edits.

Spec: `docs/superpowers/specs/2026-05-14-questionnaire-cleanup-and-magic-link-expiry-design.md`
Plan: `docs/superpowers/plans/2026-05-14-questionnaire-cleanup-and-magic-link-expiry.md`

## Test plan

- [ ] After merge + ECS deploy (~5 min), send a fresh invite from admin on stage-cb.theedpsych.co.uk.
- [ ] Confirm the invite email body reads "expires in 7 days".
- [ ] Confirm the parent assessment no longer asks the 6 removed questions.
- [ ] Confirm the school assessment now includes the `multitask` question right after the classroom-attention question.
- [ ] Confirm an existing in-flight parent session (if any) does not crash if its stored `node_id` happens to be one of the deleted ones — orchestrator's "skip without node_id" branch should kick in.
EOF
)"
```

Expected: `gh` prints the new PR URL.

- [ ] **Step 4: Share the PR URL with the user**

Echo the URL in the chat and stop. Live testing on staging happens after admin merges the PR.

---

## Self-Review

Checked the plan against the spec:

1. **Spec coverage:**
   - Spec §1 (magic link expiry → 168h + email format helper) → Tasks 1, 2, 3, 4 ✓
   - Spec §2 (parent flow 6 deletions + 6 rewires) → Tasks 6, 7 ✓
   - Spec §3 (school flow `multitask` insertion + `attention_class` rewire) → Task 8 ✓
   - Spec §4 (validate_flow.py utility) → Task 5 ✓
   - Spec §5 (rollout order, single PR, ask before push, post-deploy smoke) → Tasks 9, 10 ✓
   - Spec "Risks": stale in-flight conversation note is surfaced in the PR test plan ✓

2. **Placeholder scan:** No "TBD", "TODO", "fill in later", "appropriate error handling", or shell stubs. Every code block is complete. ✓

3. **Type consistency:** Helper name is `_format_expiry` everywhere (function definition, test imports, template substitutions). Template variable name is `expiry_label` consistently. Settings name is `MAGIC_LINK_EXPIRY_HOURS` (matches existing source). Node IDs match exactly between spec and plan (`attention_5/11`, `academic_12/14/16/18`, `multitask`). ✓
