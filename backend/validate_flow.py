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
