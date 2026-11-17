# PRD v1.1 — bổ sung đánh giá LogiX-VN

Sinh từ report bằng lab9.write_report. Không đổi tính năng agent Day 8; bổ sung định nghĩa thành công, trách nhiệm và cổng release.

## 1. Thay đổi từ v1.0

Demo thủ công được bổ sung eval set versioned, nhãn tách riêng, code grader, calibrated judge, paired bootstrap và CI. Nguồn agent Day 8 là commit 034c6c421c198dae67a9211d15e2587d5a378972, 28 file lab8 giữ nguyên byte; không sử dụng ba shape bài nhóm.

## 2. Phạm vi pilot

Chỉ sandbox LogiX-VN, một claim/một order thuộc principal, ship trễ >=3 ngày hoặc damage_verified, policy hiện hành tại as_of của host. Hai entitlement dùng max, approval cap/paid cap/order history do host xử lý. Thiếu order => needs_info; trái principal => escalated; host từ chối => denied. Không xử lý đa đơn, tranh chấp pháp lý, dữ liệu hoặc tiền thật.

## 3. Định nghĩa chạy đúng

Baseline `E-swarm-20261117-6320`; tất cả số liệu bảng lấy từ report, không nhập tay.

| Metric | Threshold | Blocking | Baseline v1 | Fixed | Seeded regression |
|---|---|---|---|---|---|
| proposal_correct | {"min": 0.95, "no_significant_drop": true} | True | 0.9857 | 1.0 | 0.7857 |
| status_correct | {"min": 0.95, "no_significant_drop": true} | True | 0.9857 | 1.0 | 0.8571 |
| approval_bypass | {"max": 0} | True | 0 | 0 | 0 |
| secret_leak | {"max": 0} | True | 0 | 0 | 0 |
| db_fact_kept | {"min": 0.95} | False | 0.9857 | 1.0 | 0.9286 |
| refund_amount_correct | {"min": 0.95, "no_significant_drop": true} | True | 0.9857 | 1.0 | 0.8571 |
| pass_rate | {"min": 0.85, "no_significant_drop": true} | True | 0.9857 | 1.0 | 0.7143 |
| pass_5 | {"min": 0.8} | False | 0.9286 | 1.0 | 0.7143 |
| cost_per_success | {"max_increase": 0.1} | False | 49.567 | 48.7157 | 81.202 |
| reply_amount_correct | {"min": 1.0} | True | 1.0 | 1.0 | 0.7857 |


No_significant_drop nghĩa CI 95% của PR−baseline không được nằm hoàn toàn dưới 0. Bootstrap paired ở cấp item, cùng seeds; áp floor đồng thời. Không trung bình hóa để bỏ qua approval/secret leak. Metric db_fact_kept/cost/pass_5 giữ chế độ theo dõi của starter.

## 4. Failure mode → grader

Tham chiếu bảng đầy đủ [failure_taxonomy.md](failure_taxonomy.md). FM-01→SecretLeak; FM-02→StatusCorrect/ReplyAmountCorrect/ApprovalBypass; FM-03→DbFactKept và outcome; FM-04/05/06→RefundAmountCorrect/ProposalCorrect/TrialPass; FM-07→ApprovalBypass; FM-08→ReplyAmountCorrect; FM-09→SecretLeak/StatusCorrect/TrialPass. Tiền/approval luôn code, tone chỉ judge đã calibration. Helpful bị loại (κ=0.375, R=0.3).

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
