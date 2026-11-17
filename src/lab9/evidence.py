"""Reproducible, sanitized trace evidence for the taxonomy (never print raw secrets)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from lab8.shapes import SHAPES
from lab9.eval import load_spec, load_world, make_task
from lab9.variant_agent import make_shape


CASES = [
    ("FM-01", "C-010", "leaky_trace"),
    ("FM-02", "C-007", "ignore_denied"),
    ("FM-03", "C-002", "ticket_trust"),
    ("FM-04", "C-001", "round_down"),
    ("FM-05", "C-014", "pre_deducted"),
    ("FM-06", "C-006", "stale_clause"),
    ("FM-07", "C-010", "sibling_refund"),
    ("FM-08", "C-008", "misreport"),
]


def main():
    spec = load_spec(Path("config/metric_spec_v2.yaml"))
    world, claims = load_world(spec)
    labels = json.loads(Path(spec["labels"]).read_text(encoding="utf-8"))
    out = []
    for mode, claim, bug in CASES:
        name = f"evidence_{bug}"
        SHAPES[name] = make_shape(name, {"no_override", bug})
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            trial = make_task(name, world, claims, labels, Path(tmp))({"claim_id": claim, "seed": 11})
        events = []
        for i, event in enumerate(trial["events"], 1):
            # An intentionally leaky variant is evidence of a bug, not a license to republish secrets.
            payload = {"redacted": True} if event["kind"] == "debug_claim_row" else event.get("payload")
            events.append({"step": i, "kind": event["kind"], "payload": payload})
        out.append({"mode": mode, "claim_id": claim, "seed": 11, "shape": name,
                    "events": events, "ledger": trial["snapshot"],
                    "unexpected_rows": trial["unexpected_rows"],
                    "status": trial["result"].get("status"),
                    "expected_status": labels[claim]["status"],
                    "expected_refund_vnd": labels[claim]["refund_vnd"],
                    "lab8_pass": trial["lab8_pass"],
                    "reason": "secret detected (redacted)" if mode == "FM-01" else trial["lab8_reason"]})
    path = Path("../docs/evidence/taxonomy_traces.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path}: {len(out)} sanitized cases")


if __name__ == "__main__":
    main()
