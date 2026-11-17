# Judge audit

Số liệu từ lab9.judge trong [validation.log](evidence/validation.log). Positive class là FAIL: precision/recall đo phát hiện lỗi.

| Tiêu chí | n | TP/FP/FN/TN | κ | Precision | Recall | FLOORS κ≥0.6, P≥0.8, R≥0.7 | Quyết định |
|---|---|---|---|---|---|---|---|
| tone_ok | 100 | 24/4/6/66 | 0.757 | 0.857 | 0.800 | PASS | Đủ calibration trên replay cho tone; chưa dùng làm gate người dùng thật |
| helpful | 100 | 9/0/21/70 | 0.375 | 1.000 | 0.300 | FAIL | Loại khỏi gate |

Tone FAIL quan sát=0.28, Rogan–Gladen=0.30. Helpful quan sát=0.09, hiệu chỉnh=0.30. Hiệu chỉnh tỷ lệ không sửa verdict từng item, không làm helpful đủ calibration. κ không xác định phải FAIL.

## Audit nội dung bất đồng

Đây là phân tích bằng AI trên CSV công khai, không phải vòng gán nhãn người mới. Quyết định dưới đây không thay nhãn gốc.

| Case | Judge | Human | Quyết định audit | Sửa rubric đề xuất |
|---|---|---|---|---|
| H-008 | PASS | FAIL | Theo human: “em”, “nha”, “check” quá suồng sã theo rubric dịch vụ này. | Ví dụ phân biệt thân thiện chuyên nghiệp và thân mật quá mức. |
| H-017 | PASS | FAIL | Theo human/rubric: “bạn”, “rồi nha” sai cách xưng hô mục tiêu. | Quy định anh/chị, dùng cách xưng hô trung tính khi chưa biết tuổi. |
| H-029 | PASS | FAIL | Theo human: “không cần nhắn thêm” ra lệnh dù mở đầu lễ phép. | Chấm toàn câu; từ “Dạ” không bù hành vi ngăn khách hỏi. |
| H-042 | FAIL | PASS | Theo human về tone: ngắn nhưng lịch sự; đúng tiền là tiêu chí khác. | Không phạt độ ngắn, không trộn correctness vào tone. |
| H-051 | FAIL | PASS | Theo human: dùng từ refund không tự động bất lịch sự. | Thêm ví dụ thuật ngữ Anh trong câu lịch sự. |
| HL-015 | PASS | FAIL | Theo human_failure trong CSV: lời văn lịch sự chưa đủ chứng minh helpful. | Liên kết claim/ledger/next step; sai tiền chấm code. |

Helpful bỏ sót 21/30 lỗi, precision 1.0 không đủ. Tiền và approval không giao judge. Tone chưa thêm thành blocking metric vì harness chưa có điểm tone độc lập mỗi trial.

CSV replay công khai, 100 item/criterion, chưa có held-out mới. Audit cần người học đọc và xác nhận độc lập. Trước dùng thật cần nhãn người mới, độ nhất quán người-người, model/rubric version và calibration trên held-out.
