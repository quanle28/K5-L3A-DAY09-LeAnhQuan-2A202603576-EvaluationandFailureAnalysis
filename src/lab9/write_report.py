"""Build Markdown summaries directly from generated reports; never alter reports/."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from lab9 import gate
from lab9.eval import load_spec, per_item
from lab9.judge import calibrate
from lab9.stats import paired_bootstrap


def main():
    root = Path(__file__).resolve().parents[2]
    def read(name):
        return json.loads(Path(f"reports/{name}.json").read_text(encoding="utf-8"))
    base, fixed, bad, v2 = map(read, ("baseline_v1", "eval_fixed", "eval_seeded_regression", "baseline_v2"))
    spec = load_spec()
    spec2 = load_spec(Path("config/metric_spec_v2.yaml"))
    tone = calibrate(Path("data/eval/judge_tone_public.csv"))
    helpful = calibrate(Path("data/eval/judge_helpful_public.csv"))
    a, b = per_item(bad, "pass_rate"), per_item(base, "pass_rate")
    keys = sorted(a)
    delta, lo, hi = paired_bootstrap([a[k] for k in keys], [b[k] for k in keys])
    metric_table = "| Metric | Threshold | Blocking | Baseline v1 | Fixed | Seeded regression |\n|---|---|---|---|---|---|\n"
    for m in spec["metrics"]:
        mid = m["id"]
        metric_table += f"| {mid} | {json.dumps(m.get('threshold', {}))} | {m.get('blocking', False)} | {base['metrics'][mid]} | {fixed['metrics'][mid]} | {bad['metrics'][mid]} |\n"
    v2_table = "| Metric | Baseline v2 |\n|---|---|\n" + "".join(f"| {k} | {v} |\n" for k, v in v2["metrics"].items())
    verdicts = []
    for rep in (base, fixed, bad):
        blocked, _ = gate.check(rep, base, spec)
        verdicts.append(f"- {rep['run_id']}: {'BLOCK ' + ', '.join(blocked) if blocked else 'MERGE'}, exit {int(bool(blocked))}.")
    card = f"""# Eval card — LogiX-VN

Sinh bằng `python -m lab9.write_report`, số liệu đọc trực tiếp report JSON do harness sinh.

- Baseline v1: `{base['run_id']}`, eval SHA `{base['manifest']['eval_set_sha']}`.
- Baseline v2: `{v2['run_id']}`, eval SHA `{v2['manifest']['eval_set_sha']}`.
- Code/grader/spec: commit chứa card này; nguồn Day 8 và hash từng file: [day8_source.json](evidence/day8_source.json). Không tạo commit hash giả hoặc tự tham chiếu hash của chính commit.
- v1: {base['manifest']['items']} item × {len(base['manifest']['seeds'])} seed; v2: {v2['manifest']['items']} item × {len(v2['manifest']['seeds'])} seed. Seeds: {base['manifest']['seeds']}. Labels tách riêng; provenance trong item.
- Metric spec v1={spec['metric_spec_version']}, v2={spec2['metric_spec_version']}; graders: lab9.graders.GRADERS; MockLLM, judge replay, không gọi API model.

{metric_table}

Paired bootstrap trên mean mỗi item (không coi 70 trial là 70 item độc lập), PR−baseline: seeded pass_rate Δ={delta:.6f}, CI 95% [{lo:.6f}, {hi:.6f}]. SciPy percentile, paired=True, 1000 resamples, RNG 2027. Chặn khi vi phạm floor hoặc toàn CI nằm dưới 0; safety đếm vi phạm tuyệt đối.

{chr(10).join(verdicts)}

Tone: κ={tone['kappa']}, P={tone['precision']}, R={tone['recall']}, calibration PASS. Helpful: κ={helpful['kappa']}, P={helpful['precision']}, R={helpful['recall']}, calibration FAIL. Xem [judge_audit.md](judge_audit.md). Tone chỉ đủ trên replay; tiền/approval dùng code.

Trace case: [C-002@11](trace_case.md), event 3 model_override; regression test kiểm cả variant lỗi và fixed. FM-08 so mọi số tiền có đơn vị đ/đồng/VND/₫ trong reply với ledger, không dùng proposal thay ledger. Swarm gốc không có reply event: metric này pass do không có khẳng định tiền, không phải đã kiểm chất lượng ngôn ngữ swarm.

## v2: slices, độ ổn định và integrity

{v2_table}

A/A hai bộ seed 11,22,33,44,55 và 66,77,88,99,110 có Δ=0 trên mọi metric trong log. pass_hat_5 floor=0.80 nằm dưới baseline {v2['metrics']['pass_hat_5']}, không cắt vào dải nhiễu A/A quan sát. Với model thật cần lặp A/A nhiều lần, đo phân bố nhiễu và chọn floor/biên bảo vệ trên dữ liệu độc lập.

- money_movement/pass_rate floor 0.95 chặn slice_regression dù toàn bộ pass_rate vẫn vượt 0.85; adversarial floor 0.90 và denial floor 0.90 đều blocking, có paired CI.
- pass_hat_5 blocking bắt độ ổn định kém ở flaky_regression; không dựa event override hay tên variant. Code thống kê dùng tổ hợp không hoàn lại, kiểm n/c/k hợp lệ.
- Integrity kiểm finite/missing score, evaluator_failures, đủ lưới item×seed, dòng trùng, tập cặp và tags slice bằng baseline, tính lại summary từ rows; ratchet với --base-spec chặn nới threshold, bỏ metric/slice/blocking/no_significant_drop.
- Mutation/trap exit và A/A đầy đủ: [validation.log](evidence/validation.log). Hidden tests của giảng viên chưa được truy cập/chạy; không cam kết điểm số.

## Owner, phạm vi và giới hạn

Eval owner: Lê Anh Quân (2A202603576); khi gate đỏ cần tìm trace, sửa đúng layer, chạy lại tests/gate. Không merge khi đỏ; thay policy cần phê duyệt giảng viên, giải thích và version/baseline mới, không hạ ngưỡng để hợp thức hóa PR.

Pilot chỉ sandbox dữ liệu giả LogiX-VN, claim một đơn, policy hiện hành; entitlement tối đa theo cấu hình host, không đưa ra production. Không thử trên người dùng thật. MockLLM, 14 item v1/28 item v2 và judge replay chưa đại diện phân bố thật; các biến thể có chủ đích không đo recall trên tất cả lỗi. 5 seed cho CI rộng; bug phụ thuộc điều kiện seed chia hết cho 3 (rare, tần suất xấp xỉ 1/3 trên không gian seed) không được phát hiện ổn định với 5 seed. Không hạ ngưỡng để săn bug này. pass^5 không bảo đảm độ tin cậy tương lai.

Reply parser chưa hiểu số viết bằng chữ, ngoại tệ, nhiều khoản trong cùng câu hay tiền giả định; cần output schema có cấu trúc/nhãn người trước mở rộng. Integrity không phải chữ ký mật mã: người thay đồng thời baseline và dữ liệu nguồn vẫn có thể gian lận; production cần baseline/spec bất biến trên nhánh bảo vệ. CI kiểm baseline bằng rerun swarm, ratchet CLI cần --base-spec từ nhánh tin cậy.

Tăng eval_set_version khi đổi item/nhãn/provenance, thêm phân bố tấn công hoặc đổi scope; sinh lại baseline. Đổi metric/ngưỡng cần tăng metric_spec_version và ghi lý do; cùng eval-set version chỉ chặt hơn. Báo cáo AI hỗ trợ phải được người học đọc, tái chạy và giải thích trước nộp.
"""
    (root / "docs/eval_card.md").write_text(card, encoding="utf-8")
    prd = f"""# PRD v1.1 — bổ sung đánh giá LogiX-VN

Sinh từ report bằng lab9.write_report. Không đổi tính năng agent Day 8; bổ sung định nghĩa thành công, trách nhiệm và cổng release.

## 1. Thay đổi từ v1.0

Demo thủ công được bổ sung eval set versioned, nhãn tách riêng, code grader, calibrated judge, paired bootstrap và CI. Nguồn agent Day 8 là commit 034c6c421c198dae67a9211d15e2587d5a378972, 28 file lab8 giữ nguyên byte; không sử dụng ba shape bài nhóm.

## 2. Phạm vi pilot

Chỉ sandbox LogiX-VN, một claim/một order thuộc principal, ship trễ >=3 ngày hoặc damage_verified, policy hiện hành tại as_of của host. Hai entitlement dùng max, approval cap/paid cap/order history do host xử lý. Thiếu order => needs_info; trái principal => escalated; host từ chối => denied. Không xử lý đa đơn, tranh chấp pháp lý, dữ liệu hoặc tiền thật.

## 3. Định nghĩa chạy đúng

Baseline `{base['run_id']}`; tất cả số liệu bảng lấy từ report, không nhập tay.

{metric_table}

No_significant_drop nghĩa CI 95% của PR−baseline không được nằm hoàn toàn dưới 0. Bootstrap paired ở cấp item, cùng seeds; áp floor đồng thời. Không trung bình hóa để bỏ qua approval/secret leak. Metric db_fact_kept/cost/pass_5 giữ chế độ theo dõi của starter.

## 4. Failure mode → grader

Tham chiếu bảng đầy đủ [failure_taxonomy.md](failure_taxonomy.md). FM-01→SecretLeak; FM-02→StatusCorrect/ReplyAmountCorrect/ApprovalBypass; FM-03→DbFactKept và outcome; FM-04/05/06→RefundAmountCorrect/ProposalCorrect/TrialPass; FM-07→ApprovalBypass; FM-08→ReplyAmountCorrect; FM-09→SecretLeak/StatusCorrect/TrialPass. Tiền/approval luôn code, tone chỉ judge đã calibration. Helpful bị loại (κ={helpful['kappa']}, R={helpful['recall']}).

## 5. Cổng release và trách nhiệm

Trong src/: `python -m lab9.gate --pr reports/eval_<shape>.json --baseline reports/baseline_v1.json --spec config/metric_spec.yaml`. Với v2 dùng baseline/spec v2, thêm --base-spec lấy từ commit main tin cậy cho ratchet. Gate exit 1 không merge. Owner Lê Anh Quân đọc reason, tra trial/trace, sửa lỗi và rerun. Chưa có waiver tự động; ngoại lệ phải được giảng viên/product owner chấp thuận và ghi rõ trong PR. Không tự nhận đã được phê duyệt.

CI hiện có eval-gate và eval-gate-v2; baseline là swarm report do script sinh. Bản fork phải bật Actions. PR starter/d09 → main ngay trong fork; không tự merge PR. Dùng lịch sử commit thật, không backdate hoặc force push.

## 6. Bằng chứng còn thiếu

Chưa có người dùng/model thật, held-out judge mới, đánh giá ẩn của giảng viên hoặc phê duyệt production. CI rộng do mẫu nhỏ; 5 seed không phát hiện ổn định bug hiếm. Xem giới hạn parser, integrity và baseline trust tại [eval_card.md](eval_card.md).

## 7. Khi nào lên v1.2

Thêm item hoặc thay nhãn cần version eval-set và baseline mới. Đổi metric/ngưỡng cần version spec mới, giải thích và giữ ratchet khi cùng eval set. Khi mở pilot thật cần dữ liệu được phép dùng, held-out người gán nhãn, schema reply và quy trình baseline được bảo vệ.

## Phê duyệt

| Vai trò | Người phụ trách | Trạng thái |
|---|---|---|
| Eval owner / người học | Lê Anh Quân — 2A202603576 | Cần đọc, tái chạy và xác nhận hiểu bài trước nộp |
| Product / giảng viên | Chưa xác định người phê duyệt | Chưa phê duyệt pilot production |
"""
    (root / "docs/PRD_v1.1.md").write_text(prd, encoding="utf-8")
    print("wrote docs/eval_card.md and docs/PRD_v1.1.md from generated reports")


if __name__ == "__main__":
    main()
