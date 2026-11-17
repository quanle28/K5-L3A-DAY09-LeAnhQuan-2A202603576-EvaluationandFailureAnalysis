# Trace case: C-002@11

| Trường | Nội dung |
|---|---|
| Trial | seeded_regression C-002@11, thuộc run E-seeded_regression-20261117-6320; output trong evidence/validation.log. |
| Triệu chứng | Status resolved thay vì denied; ledger 20.000 VND/1 row thay vì 0/0. Reply khớp ledger nhưng nghiệp vụ sai. |
| Bước sai đầu tiên | Event 3 model_override, payload {"delay_days": 5}. |
| Vì sao đầu tiên | Event 1 handoff giới hạn tools/principal; event 2 investigator đọc DB đúng delay_days=2. Event 3 mới lấy 5 từ ticket thay DB. Quote 20.000 ở event 4 là hậu quả. |
| Failure mode | FM-03 ticket_trust. |
| Đối chứng | fixed C-002@11 giữ DB; event 3 quote amount_vnd=0, reason=no_entitlement; denied, không ledger row. |
| Regression test | tests/test_lab9_regressions.py::test_lab9_first_wrong_step_regression: cùng claim/seed, DbFactKept và RefundAmountCorrect fail trên lỗi, pass trên fixed; kiểm event override và ledger. |
| Chưa chắc chắn | MockLLM không chứng minh hành vi model thật. Trace chỉ thể hiện bước được ghi. |

Tái hiện trong src/:

```text
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
python -m pytest -q -m student -o addopts= -k first_wrong_step
```

C-002 đã có trong v1. Test mở rộng assertion trên item đó, không nhân bản claim để tăng trọng số.
