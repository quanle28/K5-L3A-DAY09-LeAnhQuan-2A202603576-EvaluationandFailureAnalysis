"""Run the public submission checks and save actual commands, exits, and stdout."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[2]
    os.chdir(root / "src")
    tmp = root / ".tmp"
    tmp.mkdir(exist_ok=True)
    env = {**os.environ, "PYTHONUTF8": "1", "TEMP": str(tmp), "TMP": str(tmp)}
    commands = [
        ("lab9.smoke", 0), ("lab9.evalset --build --check", 0),
        ("lab9.evalset --v2 --build", 0),
        ("pytest -q --tb=short", 0),
        ("pytest -q -m student -o addopts= -k lab9 --tb=short", 0),
        ("lab9.judge --csv data/eval/judge_tone_public.csv --audit 10", 0),
        ("lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5", 1),
        ("lab9.eval --shape swarm --out reports/baseline_v1.json", 0),
        ("lab9.eval --shape swarm --out reports/eval_pr.json", 0),
        ("lab9.ci_check --pr reports/eval_pr.json --baseline reports/baseline_v1.json", 0),
        ("lab9.gate --pr reports/eval_pr.json --baseline reports/baseline_v1.json", 0),
        ("lab9.eval --shape fixed", 0),
        ("lab9.gate --pr reports/eval_fixed.json --baseline reports/baseline_v1.json", 0),
        ("lab9.eval --shape seeded_regression", 0),
        ("lab9.gate --pr reports/eval_seeded_regression.json --baseline reports/baseline_v1.json", 1),
        ("lab9.mutation --detect", 0),
        ("lab9.eval --shape swarm --spec config/metric_spec_v2.yaml --out reports/baseline_v2.json", 0),
        ("lab9.gate --pr reports/baseline_v2.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml --base-spec config/metric_spec_v2.yaml", 0),
        ("lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110", 0),
        ("lab9.mutation --spec config/metric_spec_v2.yaml --baseline reports/baseline_v2.json", 0),
        ("lab9.eval --shape slice_regression --spec config/metric_spec_v2.yaml --out reports/eval_slice_regression.json", 0),
        ("lab9.traps --pr reports/eval_slice_regression.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml", 0),
    ]
    for name in ("evaluator_errors_as_nan", "dropped_failing_rows", "cherry_picked_seeds", "loosened_spec"):
        spec = f"reports/traps/{name}.spec.yaml --base-spec config/metric_spec_v2.yaml" if name == "loosened_spec" else "config/metric_spec_v2.yaml"
        commands.append((f"lab9.gate --pr reports/traps/{name}.json --baseline reports/baseline_v2.json --spec {spec}", 1))
    commands.extend([("lab9.evidence", 0),
                     ("lab9.trace_case --shape seeded_regression --claim C-002 --seed 11", 0),
                     ("lab9.trace_case --shape fixed --claim C-002 --seed 11", 0)])
    path = root / "docs/evidence/validation.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    failures = []
    with path.open("w", encoding="utf-8") as log:
        for command, expected in commands:
            result = subprocess.run([sys.executable, "-m", *command.split()], env=env,
                                    capture_output=True, text=True, encoding="utf-8")
            output = "\n".join(line.rstrip() for line in (result.stdout + result.stderr).splitlines())
            log.write(f"$ python -m {command}\n{output}\nexit={result.returncode}; expected={expected}\n\n")
            log.flush()
            print(f"exit={result.returncode} expected={expected} {command}", flush=True)
            if result.returncode != expected:
                failures.append(command)
    with path.open("a", encoding="utf-8") as log:
        log.write(f"validation: {len(commands) - len(failures)}/{len(commands)} expected exits\n")
    print(f"validation: {len(commands) - len(failures)}/{len(commands)} expected exits; log={path}")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
