"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from lab9.graders import GRADERS
from lab9.eval import aggregate
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = []
    graded = [m["id"] for m in spec["metrics"] if m["id"] in GRADERS]
    def finite(v):
        return isinstance(v, (int, float)) and math.isfinite(v)
    def inspect(rep, name):
        manifest = rep.get("manifest", {})
        rows = rep.get("rows", [])
        seeds = manifest.get("seeds", [])
        items = manifest.get("items", 0)
        pairs = [(r.get("item_id"), r.get("seed")) for r in rows]
        if len(rows) != items * len(seeds) or len(set(pairs)) != len(rows):
            problems.append(f"{name}: dropped or duplicate rows")
        if len(set(seeds)) != len(seeds) or len({p[0] for p in pairs}) != items:
            problems.append(f"{name}: invalid manifest")
        if set(pairs) != {(i, seed) for i, _ in pairs for seed in seeds}:
            problems.append(f"{name}: incomplete item x seed grid")
        if rep.get("evaluator_failures"):
            problems.append(f"{name}: evaluator failures")
        for mid, value in rep.get("metrics", {}).items():
            if not finite(value):
                problems.append(f"{name}: invalid metric {mid}")
        for m in spec["metrics"]:
            if not finite(rep.get("metrics", {}).get(m["id"])):
                problems.append(f"{name}: missing metric {m['id']}")
        for r in rows:
            for mid in graded:
                if not isinstance(r.get(mid), bool):
                    problems.append(f"{name}: missing/invalid row metric {mid}")
            if "cost" in r and (not finite(r["cost"]) or r["cost"] < 0):
                problems.append(f"{name}: invalid cost")
        # Recompute complete production reports: summaries cannot contradict row evidence.
        if rows and all("cost" in r and all(isinstance(r.get(m), bool) for m in graded) for r in rows):
            recalculated = aggregate(rows, graded, k_values=spec.get("pass_k", []))
            for mid, value in recalculated.items():
                reported = rep.get("metrics", {}).get(mid)
                if not finite(reported) or value is None or abs(reported - value) > 1e-8:
                    problems.append(f"{name}: aggregate mismatch {mid}")
        return pairs
    pp, bp = inspect(pr, "PR"), inspect(base, "baseline")
    if Counter(pp) != Counter(bp):
        problems.append("PR item/seed multiset differs from baseline")
    if pr.get("manifest", {}).get("items") != base.get("manifest", {}).get("items") or set(pr.get("manifest", {}).get("seeds", [])) != set(base.get("manifest", {}).get("seeds", [])):
        problems.append("PR manifest differs from baseline")
    baseline_tags = {(r["item_id"], r["seed"]): set(r.get("slices") or []) for r in base.get("rows", [])}
    item_tags = {}
    for r in pr.get("rows", []):
        key = (r["item_id"], r["seed"])
        tags = set(r.get("slices") or [])
        if key in baseline_tags and tags != baseline_tags[key]:
            problems.append("PR slice tags differ from baseline")
        if r["item_id"] in item_tags and item_tags[r["item_id"]] != tags:
            problems.append("inconsistent slice tags across seeds")
        item_tags[r["item_id"]] = tags
    if base_spec is not None and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
        def ratchet(new_entries, old_entries, key, nested):
            current = {key(m): m for m in new_entries}
            for old in old_entries:
                ident = key(old)
                new = current.get(ident)
                if new is None:
                    problems.append(f"ratchet: removed {ident}")
                    continue
                if old.get("blocking") and not new.get("blocking"):
                    problems.append(f"ratchet: disabled {ident}")
                ot = old.get("threshold", {}) if nested else old
                nt = new.get("threshold", {}) if nested else new
                for field in ("min", "max", "max_increase", "no_significant_drop"):
                    if field not in ot:
                        continue
                    if field not in nt or (field == "min" and nt[field] < ot[field]) or (field in ("max", "max_increase") and nt[field] > ot[field]) or (field == "no_significant_drop" and ot[field] and not nt[field]):
                        problems.append(f"ratchet: loosened {ident}/{field}")
        ratchet(spec.get("metrics", []), base_spec.get("metrics", []), lambda m: m["id"], True)
        ratchet(spec.get("slices", []), base_spec.get("slices", []), lambda m: (m["name"], m["metric"]), False)
    return sorted(set(problems))


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for entry in spec.get("slices", []):
        ident = f"slice:{entry['name']}/{entry['metric']}"
        a = per_item(pr, entry["metric"], slice_name=entry["name"])
        b = per_item(base, entry["metric"], slice_name=entry["name"])
        invalid = not a or a.keys() != b.keys()
        value = sum(a.values()) / len(a) if a else None
        bad = invalid or ("min" in entry and value < entry["min"])
        note = ""
        if not invalid and entry.get("no_significant_drop"):
            keys = sorted(a)
            delta, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027), confidence=bs.get("confidence", .95))
            bad |= hi < 0
            note = f"delta {delta:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
        if bad and entry.get("blocking"):
            blocked.append(ident)
        lines.append(f"  {ident} {value} {note} {'BLOCK' if bad else 'ok'}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027), confidence=bs.get("confidence", .95))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
