"""Behavior checks beyond the starter vectors; no reference code is changed."""
import copy
import pytest

from lab9.graders import ReplyAmountCorrect
from test_lab9_graders import ctx, trial

pytestmark = pytest.mark.student


@pytest.mark.parametrize("text", [
    "Đã hoàn 20.000đ.", "Đã hoàn 20,000 VND.",
    "LogiX đã hoàn phí 20000 đồng cho đơn O-808.", "Đã hoàn 20 000₫.",
])
def test_lab9_reply_accepts_equivalent_currency_formats(text):
    t = trial(refund_vnd=20000, events=[{"kind": "reply", "payload": {"text": text}}])
    assert ReplyAmountCorrect().evaluate(ctx(t)).value is True


def test_lab9_reply_rejects_proposal_in_place_of_ledger():
    t = trial(refund_vnd=20000, events=[{"kind": "reply", "payload": {"text": "Đã hoàn 35.000đ."}}])
    assert ReplyAmountCorrect().evaluate(ctx(t)).value is False


def test_lab9_first_wrong_step_regression(tmp_path):
    from lab9.trace_case import investigate
    from lab9.graders import DbFactKept, RefundAmountCorrect
    bad = investigate("seeded_regression", "C-002", 11)
    good = investigate("fixed", "C-002", 11)
    overrides = [(i, e) for i, e in enumerate(bad["trial"]["events"], 1) if e["kind"] == "model_override"]
    assert overrides and overrides[0][1]["payload"]["delay_days"] == 5
    assert bad["trial"]["snapshot"]["refund_vnd"] > 0
    assert good["trial"]["snapshot"]["refund_vnd"] == 0
    for grader in (DbFactKept(), RefundAmountCorrect()):
        assert grader.evaluate(ctx(bad["trial"], bad["label"])).value is False
        assert grader.evaluate(ctx(good["trial"], good["label"])).value is True


@pytest.mark.parametrize("mutation", ["duplicate", "evaluator_failure", "slice_relabel", "summary"])
def test_lab9_advanced_integrity_rejects_corruption(mutation):
    from lab9 import gate
    from test_lab9_advanced import ROWS, SPEC, _report
    base = _report(copy.deepcopy(ROWS), {"pass_rate": 1.0})
    pr = copy.deepcopy(base)
    if mutation == "duplicate":
        pr["rows"][-1] = copy.deepcopy(pr["rows"][0])
    elif mutation == "evaluator_failure":
        pr["evaluator_failures"] = ["grader crashed on a nominally green run"]
    elif mutation == "slice_relabel":
        pr["rows"][0]["slices"] = []
    else:
        for rep in (pr, base):
            for row in rep["rows"]:
                row["cost"] = 1.0
            rep["metrics"].update(pass_5=1.0, cost_per_success=1.0)
        pr["metrics"]["pass_rate"] = 0.99
    assert gate.integrity_check(pr, base, SPEC)


@pytest.mark.parametrize("args", [(0, 0, 1), (5, -1, 1), (5, 2, 6), (5.0, 2, 1), (True, 1, 1)])
def test_lab9_advanced_both_estimators_reject_invalid_inputs(args):
    from lab9.stats import pass_at_k, pass_hat_k
    for estimator in (pass_at_k, pass_hat_k):
        with pytest.raises(ValueError):
            estimator(*args)
