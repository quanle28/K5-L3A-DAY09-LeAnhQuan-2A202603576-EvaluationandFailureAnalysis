# Báo cáo Lab Day 09 — Lê Anh Quân

- Lớp: K5-L3A. MSSV: 2A202603576. Ngày thực hiện: 17/11/2026 (GMT+7).
- Repo: https://github.com/quanle28/K5-L3A-DAY09-LeAnhQuan-2A202603576-EvaluationandFailureAnalysis
- Nhánh cục bộ: starter/d09; đích PR: main trong cùng fork. Chưa merge.

## Kết quả đã hoàn thành tại máy

| Mốc | Nội dung | Bằng chứng |
|---|---|---|
| M0 | Đọc README/RUBRIC/CHECKPOINTS/SUBMISSION Day 09, RULES/business rules/contracts Day 08; ưu tiên 4 bước cập nhật người học cung cấp; lấy nguyên src/ của giảng viên từ lịch sử Git, không lấy bài nhóm | M0 PASS; docs/evidence/day8_source.json: 28 file lab8, 0 sửa đổi |
| M1 | Taxonomy 9 FM, 5 anchor công khai với bước sai đầu tiên; eval set v1 14 item, nhãn riêng, provenance | docs/failure_taxonomy.md; evalset --check: 0 problem |
| M2 | Confusion/P/R/κ/Rogan–Gladen, loại helpful, audit 6 bất đồng có đề xuất sửa rubric | docs/judge_audit.md; tone κ=.757/P=.857/R=.8; helpful κ=.375/R=.3 |
| M3 | ApprovalBypass, RefundAmountCorrect; FM-08 ReplyAmountCorrect; thêm StatusCorrect/ProposalCorrect để bắt trạng thái/quote sai khi ledger vẫn đúng | Detection 100%, false alarms 0%; regression C-002@11 và test parser tiền |
| M4 | Paired SciPy percentile bootstrap cấp item; swarm/fixed qua gate, seeded_regression bị chặn; thêm eval section vào harness_map | Δ pass_rate −.271429, CI [−.500000, −.057143]; log và reports thật |
| M5 | Map attack→FM, eval set v2 28 item, mỗi FM bị tấn công có >=3 item; slice money_movement/adversarial/denial blocking | evalset v2: 0 problem; slice_regression bị chặn ở money_movement |
| M6 | pass@k/pass^k tổ hợp, từ chối n/c/k sai; A/A hai bộ seed; floor pass_hat_5=.80 | A/A mọi Δ=0; mutation bắt flaky, fixed và honest_refactor qua |
| M7 | Fail-closed trên NaN/Inf/None, evaluator failure, thiếu/trùng dòng, đổi item/seed/slice, summary không khớp rows; ratchet metric/slice | Mutation 3/3, 0 báo nhầm; 4 trap exit 1; test thêm dòng trùng và evaluator failure trên run xanh |
| Tài liệu | Trace case, judge audit, eval card, PRD v1.1, README quy trình mới và nội dung PR | docs/; card/PRD sinh từ JSON bằng lab9.write_report |

## Kiểm tra và nguồn số liệu

- python -m lab9.verify_submission đạt 29/29 exit code mong đợi; log đầy đủ: [validation.log](docs/evidence/validation.log).
- pytest mặc định: 57 PASS; test student Day 09: 38 PASS. Các test student Day 08 chưa hoàn thiện được deselect theo thiết kế đề; không báo là đã làm bài nhóm.
- Baseline v1 E-swarm-20261117-6320, SHA 6320183135cc, pass_rate 0.9857. Baseline v2 E-swarm-20261117-bc2f, SHA bc2f855ba0a6, pass_hat_5 0.8929.
- reports/baseline_v1.json, baseline_v2.json, eval_fixed.json, eval_seeded_regression.json và eval_slice_regression.json chỉ do lab9.eval sinh; traps chỉ do lab9.traps sinh. Không chỉnh số liệu JSON bằng tay.
- Rerun trong src/: ../.venv/Scripts/python.exe -m lab9.verify_submission; sau đó ../.venv/Scripts/python.exe -m lab9.write_report. Python 3.13; dependency nguyên từ requirements của hai lab.
- Bật LF cho eval_set/labels/reports để SHA không đổi giữa Windows/Linux. Thêm ignore cho .env/.venv/instructor/student_drop. Không commit DB, trace thô hoặc secret ngoài dữ liệu mẫu có sẵn của giảng viên.

## Thay đổi workflow và trạng thái GitHub

Giữ kiểm tra gốc eval-gate, eval-gate-v2; thêm ratchet đối chiếu spec tại commit base của PR, A/A và chạy trap thật. Workflow YAML đã đọc và kiểm tra cục bộ các lệnh ratchet với spec HEAD/main; chưa có run GitHub để khẳng định dấu xanh.

Kết nối GitHub đã phục hồi sau lỗi mạng ban đầu. API GitHub xác nhận Actions enabled=true và workflow lab9-eval-gate active. Connector có lỗi quyền ghi 403 nên thao tác Git/REST dùng phiên Git đăng nhập sẵn; không xuất/lưu token. Nội dung PR ở [PR_DESCRIPTION.md](docs/PR_DESCRIPTION.md). Trạng thái PR và CI từ xa sẽ được bổ sung sau push, không suy dấu xanh từ test cục bộ.

Sau khi khôi phục quyền/kết nối, thực hiện trên repo này:

```powershell
git push -u origin starter/d09
```

Vào Actions của fork → bấm “I understand my workflows, go ahead and enable them” nếu hiện. Mở PR với base repository là chính quanle28/...Day09..., base main, compare starter/d09; dán docs/PR_DESCRIPTION.md. Nếu PR đã mở trước khi bật Actions, chạy lab9-eval-gate bằng workflow_dispatch ở starter/d09. Chỉ coi nộp đủ khi eval-gate và eval-gate-v2 xanh; không tự merge. Không đổi thời gian commit hoặc force push.

## Giới hạn và sử dụng AI

Đã dùng Codex hỗ trợ đọc đề, triển khai code, viết test/tài liệu, chạy và đối chiếu bằng chứng. Audit nội dung CSV là phân tích bằng AI, chưa phải nhãn người mới. Không tự gán phần AI làm là đóng góp tự viết của sinh viên; người học cần đọc, tái chạy, hiểu và trình bày được công thức/trace/gate trước nộp theo RULES Day 08. Không bịa số liệu/run ID/commit, không truy cập key hoặc hidden grader giảng viên, không cam kết điểm 100.

MockLLM/replay và 14/28 item không đại diện người dùng thật; 5 seed chưa phát hiện ổn định bug hiếm (điều kiện rare có xác suất xấp xỉ 1/3 trên không gian seed). Reply parser chưa hiểu số viết bằng chữ/ngữ cảnh nhiều khoản; swarm gốc thiếu reply event nên metric reply không đo chất lượng câu trả lời của nó. Baseline/spec trong production cần nhánh bảo vệ; kiểm integrity không thay thế chữ ký hoặc nguồn dữ liệu tin cậy. Không triển khai hay xử lý tiền thật. Chi tiết tại [eval_card.md](docs/eval_card.md).
