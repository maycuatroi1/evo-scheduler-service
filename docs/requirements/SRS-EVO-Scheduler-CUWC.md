# Đặc tả yêu cầu hệ thống (SRS)
## Hệ thống xếp thời khoá biểu tự động — Trường Cao đẳng Xây dựng Công trình Đô thị

| | |
|---|---|
| **Mã tài liệu** | SRS-EVO-SCHED-CUWC-v1.0 |
| **Sản phẩm** | EVO Scheduler Service (`evo-scheduler-service`) |
| **Đơn vị thụ hưởng** | Trường Cao đẳng Xây dựng Công trình Đô thị (CUWC) |
| **Ngày lập** | 20/08/2026 |
| **Nhánh phát triển** | `update-ui` |
| **Trạng thái** | Bản thảo để rà soát |

---

## 0. Cách đọc tài liệu này

Tài liệu gồm ba lớp thông tin, phân biệt rõ để người đọc biết đâu là sự thật đã kiểm chứng và đâu là đề xuất:

| Ký hiệu | Ý nghĩa |
|---|---|
| **[ĐÃ CÓ]** | Chức năng đã hiện diện trong mã nguồn tại thời điểm khảo sát. |
| **[THIẾU]** | Khoảng trống đã xác định trong mã nguồn, cần bổ sung. |
| **[ĐỀ XUẤT]** | Yêu cầu mới, suy ra từ nghiệp vụ trường nghề hoặc từ khảo sát phần mềm đối chiếu FTKB. |
| **[GIẢ ĐỊNH]** | Thông tin chưa kiểm chứng được, cần trường xác nhận trước khi chốt. |

Mã yêu cầu: `FR-x.y` (chức năng), `NFR-x` (phi chức năng), `BR-x` (quy tắc nghiệp vụ), `CT-x` (ràng buộc xếp lịch).

> **Nguyên tắc ưu tiên:** những gì **[ĐÃ CÓ]** trong hệ thống là **ưu tiên thấp nhất** — liệt kê chỉ để biết nền tảng đang đứng ở đâu, không phải việc cần làm. Trọng tâm của tài liệu là **[THIẾU]** và **[ĐỀ XUẤT]**, rút ra từ nghiệp vụ thật của trường.

---

## 0b. Sáu bài toán trọng tâm

Toàn bộ giá trị của dự án nằm ở sáu bài toán dưới đây. Đây là những thứ phần mềm xếp lịch phổ thông **không giải được**, và đều rút ra từ thời khoá biểu trường đang phát hành cùng quy chế đào tạo nội bộ.

| # | Bài toán | Vì sao khó | Mức |
|---|---|---|---|
| **1** | **Lớp văn hoá và nhóm nghề không trùng nhau** — 11A3 tách 3 nhóm (16/17/30); ngược lại 12A1+12A4 gộp 1 nhóm (44) | Quan hệ nhiều-nhiều **cả hai chiều**, vô hình trên bản in. Xếp sai là học sinh trùng giờ với chính mình | **Chặn** |
| **2** | **Trần sĩ số thực hành 18** trong khi lớp tới 44 SV | Nhân ba số buổi, nhu cầu xưởng và tải giáo viên. Là nguyên nhân gốc của bài toán 1 | **Chặn** |
| **3** | **Ca học cố định theo khối + ba luồng TKB** | Khối 12 và 10 học văn hoá sáng, khối 11 chiều → hai khối dồn về 11 xưởng cùng buổi chiều. CĐ và TC phát hành theo tuần, văn hoá ổn định cả kỳ | **Chặn** |
| **4** | **Đồng giảng và các kiểu ghép lớp** | Hai GV một buổi, ghép giảng đường, tách nhóm, luân phiên — bốn mô hình khác nhau | Cao |
| **5** | **Tuần thực tập trọn gói** | Chiếm trọn lịch nhưng không tốn phòng, không tốn giáo viên | Cao |
| **6** | **Giờ chuẩn ≠ số tiết** | LT 45 phút và TH 60 phút cùng bằng 1 giờ chuẩn; đếm tiết là sai định mức | Cao |

**Bản mẫu tương tác** minh hoạ sáu bài toán này: [prototype.html](./prototype.html).

---

## 1. Bối cảnh và phạm vi

### 1.1 Vấn đề nghiệp vụ

Xếp thời khoá biểu cho một trường cao đẳng nghề là bài toán tổ hợp mà cách làm thủ công trên Excel không còn kham nổi. Bốn đặc thù khiến trường nghề khó hơn trường phổ thông:

1. **Hai khối đào tạo song song.** Học sinh hệ 9+ (tốt nghiệp THCS) vừa học văn hoá THPT vừa học nghề. Hai khối này dùng chung giáo viên, chung phòng, nhưng do hai bộ phận khác nhau quản lý và thường xếp lịch ở hai thời điểm khác nhau.
2. **Thực hành chiếm tỉ trọng lớn.** Chương trình nghề bắt buộc thực hành nhiều hơn lý thuyết. Buổi thực hành cần xưởng hoặc bộ dụng cụ — tài nguyên khan hiếm, số lượng hữu hạn, và một buổi thực hành thường kéo dài liền 4–5 tiết, không thể cắt rời.
3. **Tài nguyên đếm được, không chỉ là phòng.** Một bộ dụng cụ có 10 suất dùng đồng thời; xưởng hàn có sức chứa 20 trong khi lớp có 35 sinh viên. Mô hình "một phòng một lớp" của phần mềm phổ thông không diễn đạt được điều này.
4. **Giáo viên dạy chéo khối.** Một giáo viên có thể vừa dạy văn hoá vừa dạy nghề, nên không thể xếp độc lập hai khối rồi ghép lại.

### 1.2 Mục tiêu hệ thống

| Mục tiêu | Chỉ số đo |
|---|---|
| Rút ngắn thời gian lập TKB | Từ nhiều ngày công thủ công xuống dưới 10 phút máy chạy |
| Không còn xung đột cứng | 0 trùng giáo viên / trùng lớp / vượt sức chứa tài nguyên trong lịch xuất bản |
| Giải thích được khi bế tắc | Mọi trường hợp không có lời giải phải chỉ đúng thực thể gây mâu thuẫn, không báo lỗi chung chung |
| Giữ được công sức đã bỏ ra | Sửa cục bộ một tiết không phá vỡ toàn bộ lịch |

### 1.3 Phạm vi

**Trong phạm vi:** quản lý dữ liệu nền (giáo viên, lớp, môn/mô-đun, phòng/thiết bị), khai báo ràng buộc, xếp lịch tự động, tinh chỉnh thủ công, kiểm tra khả thi, xuất bản và phân phối TKB.

**Ngoài phạm vi (giai đoạn 1):** điểm danh, quản lý điểm, tuyển sinh, tài chính, LMS. Hệ thống là một dịch vụ chuyên biệt, tích hợp với EVO LMS qua API.

---

## 2. Hồ sơ đơn vị thụ hưởng

### 2.1 Thông tin định danh

| Hạng mục | Thông tin | Nguồn |
|---|---|---|
| Tên đầy đủ | Trường Cao đẳng Xây dựng Công trình đô thị | Đề án tuyển sinh 2026 |
| Tên tiếng Anh | College of Urban Works Construction (CUWC) | cuwc.edu.vn |
| Mã trường | CDT0128 | Đề án tuyển sinh 2026 |
| Trụ sở chính | Số 328, đường Yên Thường, xã Phù Đổng, TP Hà Nội | Đề án tuyển sinh 2026 |
| Phân hiệu | Số 1355, đường Nguyễn Tất Thành, phường Phú Bài, TP Huế | Đề án tuyển sinh 2026 |
| Cơ quan chủ quản | **Bộ Giáo dục và Đào tạo** (từ 01/3/2025) | QĐ 596/QĐ-BGDĐT |
| Thành lập | 17/02/1976; nâng cấp cao đẳng 16/02/2004 theo QĐ 685/QĐ-BGD&ĐT | Lịch sử phát triển |

> **Lưu ý khi tích hợp dữ liệu:** trường trực thuộc **Bộ Xây dựng** trong phần lớn lịch sử, chuyển về Bộ LĐ-TB&XH năm 2024 và về **Bộ GD&ĐT từ 01/3/2025**. Các biểu mẫu nội bộ ban hành trước 2025 vẫn mang tiêu đề "BỘ XÂY DỰNG". Hệ thống cần cho phép cấu hình tên cơ quan chủ quản trên đầu bản in thay vì mã hoá cứng.

### 2.2 Quy mô

| Chỉ số | Giá trị | Độ tin cậy |
|---|---|---|
| Chỉ tiêu tuyển sinh 2026 | 2.000 (CĐ 400 · TC 500 · sơ cấp 100 · ngắn hạn 1.000) | Đề án 2026 — đã kiểm chứng |
| Học sinh, sinh viên CĐ + TC | > 2.000 | Báo chí — **[GIẢ ĐỊNH]** |
| Học sinh học văn hoá THPT (GDTX) | ~2.000 | Báo chí — **[GIẢ ĐỊNH]** |
| Số cơ sở đào tạo | 2 (Hà Nội ~5 ha; Phân hiệu Huế ~4 ha) | Đã kiểm chứng |
| **Số giáo viên** | **Chưa công bố** — trích được ~60 tên từ 3 file TKB tuần | **[GIẢ ĐỊNH]** — cần trường cung cấp |

### 2.3 Cơ cấu đào tạo

**Năm khoa:** Điện – Điện tử (3 tổ bộ môn); Xây dựng và Quản lý đô thị; Cơ khí; Công nghệ Thông tin và Du lịch; Giáo dục Chính trị và Khoa học Cơ bản. Kèm Trung tâm Đào tạo ngành Nước và Môi trường và Phân hiệu Huế.

**Năm nhóm ngành nghề** với chỉ tiêu 2026: Kiến trúc – Xây dựng – Cấp thoát nước (CĐ 120 / TC 60); Điện – Điện tử (115/125); Kế toán – Tin học (55/115); Cơ khí – Hàn – Ô tô (30/80); Nhà hàng – Khách sạn (80/120).

> Một số nghề đã đăng ký hoạt động nhưng **không có chỉ tiêu 2026** (Hàn, Kỹ thuật lắp đặt ống công nghệ). Mô hình dữ liệu phải phân biệt *nghề đăng ký* và *nghề đang có lớp chạy*.

**Hệ 9+ là khối lớn nhất:** 450 trên 500 chỉ tiêu trung cấp (**90%**) là **trung cấp song bằng**, 3 năm, học đồng thời chương trình GDTX cấp THPT và chương trình nghề. Đây chính là bài toán xếp lịch khó nhất của trường.

### 2.4 Thực tế vận hành thời khoá biểu — khảo sát từ TKB đã công bố

Phân tích trực tiếp các file TKB trường đang phát hành cho ra những phát hiện quyết định thiết kế:

**a) Ba luồng thời khoá biểu độc lập, phải xếp phối hợp**

| Luồng | Khoá | Nhịp phát hành | Khung ngày |
|---|---|---|---|
| Khối cao đẳng | K21, K22 | **Hằng tuần**, đánh số tuần 01–46 | 10 tiết/ngày (1–5 sáng, 6–10 chiều) |
| Khối trung cấp nghề | K42, K43 | **Hằng tuần**, tuần 01–46 | 5 tiết/buổi, chủ yếu sáng |
| Khối văn hoá | Khối 10, 11, 12 | **Ổn định theo kỳ** ("áp dụng từ…") | 5 tiết sáng + 5 tiết chiều |

Học sinh hệ 9+ xuất hiện đồng thời ở **hai luồng**. Hệ thống phải hỗ trợ cả mô hình **phát hành cuốn chiếu theo tuần** lẫn **thời khoá biểu gốc ổn định cả kỳ**.

**b) Một lớp văn hoá tách thành nhiều nhóm nghề** — phát hiện quan trọng nhất

Trong TKB nghề khối 11 (TC khoá 43), lớp văn hoá **11A3 xuất hiện ở ba cột nghề khác nhau** với sĩ số 16, 17 và 30; lớp **11A11** xuất hiện hai lần (14 và 25). Nghĩa là quan hệ giữa *lớp văn hoá* và *nhóm học nghề* là **nhiều-nhiều**, không phải một-một.

Mô hình `StudentGroup` hiện tại **không diễn đạt được điều này** (khoảng trống G-11). Đây là ràng buộc bắt buộc: khi nhóm nghề của 11A3 đang học, cả lớp 11A3 không thể có tiết văn hoá.

**c) Các đặc điểm khác đã xác nhận từ bản in thực tế**

- Tuần học **Thứ 2 → Thứ 6**; ngày 10 tiết.
- **Chào cờ bắt đầu 7h25 thứ Hai** — sự kiện chặn toàn trường, cố định.
- Ô lịch chứa **mô-đun + phòng + giáo viên**; **một mô-đun thường chiếm trọn buổi 4–5 tiết liền**, không cắt rời.
- **Đồng giảng có thật:** ô "Kỹ thuật gia công ống kim loại" ghi đồng thời *Thầy Đ.K.Huynh* và *Thầy N.V.Hiện*; ô "Máy điện và thiết bị điện gia dụng" ghi *Thầy L.N.Khanh* và *Cô N.P.Thuý*.
- **Sĩ số in ngay trên tiêu đề cột**, dao động **14–44**.
- **Tuần thực tập trọn gói:** lớp K22 có "THỰC TẬP TỐT NGHIỆP" chiếm mọi tiết mọi ngày — phải mô hình hoá như khối chặn cả tuần, **không tiêu tốn phòng hay giáo viên**.
- **Phòng có ngữ nghĩa theo dãy nhà:** A6 (giảng đường lớn, chủ yếu văn hoá), A11 (nhà kỹ thuật, phòng thí nghiệm điện/cơ), **A10-XTH** (xưởng thực hành), A4 (phòng máy tính), B3 (nhà ăn — thực hành chế biến món ăn), **SÂN A6** (ngoài trời — thực hành trắc địa), A7 tầng 1 (nghiệp vụ lễ tân).

### 2.5 Khung pháp lý

**Quy chế nội bộ của trường** (QĐ 245/QĐ-CDT ngày 06/6/2024) — trực tiếp ràng buộc bài toán xếp lịch:

| Điều | Nội dung ràng buộc |
|---|---|
| Điều 3.4.a | **Thời gian giảng dạy 6:00–22:00, kể cả Thứ 7 và Chủ nhật.** Đây là biên pháp lý; trường hiện chỉ dùng T2–T6, nên còn dư địa mở rộng |
| Điều 3.5 | **Giờ học văn hoá THPT không tính vào thời gian đào tạo nghề** — học sinh 9+ mang hai quỹ giờ độc lập phải nhét vào cùng một tuần vật lý |
| Điều 5 | Kế hoạch đào tạo phải tách riêng **thời gian lý thuyết, thực hành, thực tập**, kèm lịch thi và lịch nghỉ |
| Điều 12 | Lịch thi công bố trước **≥ 2 tuần**; **mỗi mô-đun thi riêng**, không ghép hai môn vào một ca cho cùng học sinh; **≤ 50 thí sinh/phòng, ≥ 2 giám thị** |
| Điều 13 | Phải dự **≥ 80%** thời lượng mới được thi kết thúc mô-đun |

**Quy định cấp bộ cần tuân thủ:**

| Văn bản | Nội dung áp dụng | Độ tin cậy |
|---|---|---|
| **TT 01/2024/TT-BLĐTBXH** | Tỉ lệ lý thuyết/thực hành: **CĐ = LT 30–50% / TH 50–70%**; **TC = LT 25–45% / TH 55–75%**. 1 tín chỉ = 15h LT hoặc 30h TH hoặc 45h thực tập | Tỉ lệ **[GIẢ ĐỊNH]** — cần đối chiếu công báo |
| **TT 07/2017/TT-BLĐTBXH** | **Giờ chuẩn:** 45 phút LT = 1 giờ chuẩn; 60 phút thực hành = 1 giờ chuẩn. **Định mức/năm:** CĐ 380–450; TC 430–510. **Quy mô lớp: LT ≤ 35; thực hành ≤ 18** (≤ 10 với nghề nặng nhọc, độc hại) | **[GIẢ ĐỊNH]** — cần đối chiếu công báo |
| **Luật GDNN 124/2025/QH15** | Hiệu lực **01/01/2026**, thay Luật 2014 | Đã kiểm chứng |

> **Rủi ro pháp lý cần lưu ý:** toàn bộ hệ thống thông tư của Bộ LĐ-TB&XH được Bộ GD&ĐT tiếp quản từ 01/3/2025, và Luật GDNN mới có hiệu lực 01/01/2026. Các thông tư trên vẫn là căn cứ hiện hành nhưng nhiều khả năng sẽ được ban hành lại. **Không mã hoá cứng** hệ số giờ chuẩn, định mức và trần sĩ số — phải đưa vào cấu hình.

### 2.6 Cơ sở vật chất — số liệu trường cung cấp

| Nhóm phòng | Số lượng | Sức chứa | Ghi chú |
|---|---|---|---|
| Phòng văn hoá lớn | **26** | 40–50 HS | |
| Phòng văn hoá nhỏ | **5** | < 30 HS | |
| Xưởng ô tô | **3** | | |
| Xưởng điện tầng 1 | **4** | | Điện, Máy lạnh & ĐHKK |
| Xưởng điện tầng 2 | **2 + 2** | | 2 phòng Điện tử, 2 phòng Điện dân dụng |
| Phòng máy tính | **5** | 18–24 máy | |
| Phòng lý thuyết nghề | **4 to + 5 nhỏ** | | **Dùng chung với khối văn hoá** |

**Tổng: 31 phòng văn hoá · 11 xưởng · 5 phòng máy · 9 phòng lý thuyết (chung).**

**Định mức giảng dạy: 550 tiết/giáo viên** — con số vận hành thực tế của trường. Dùng số này thay cho khoảng 430–510 suy ra từ thông tư.

> Phòng lý thuyết nghề **dùng chung** với khối văn hoá là một ràng buộc tranh chấp tài nguyên: mô hình dữ liệu phải cho phép một phòng phục vụ nhiều khối, và bộ giải phải biết hai khối đang cạnh tranh cùng một nhóm phòng.

### 2.7 Ca học văn hoá theo khối — ràng buộc cứng

*Kiểm chứng từ 30 file TKB trường công bố (khối 10/11/12 văn hoá, K42/K43 nghề, K21/K22 cao đẳng).*

| Khối | Ca văn hoá | Ca học nghề | Nguồn kiểm chứng |
|---|---|---|---|
| **Khối 12** | **Cả ngày** — sáng tiết 1–5 **và** chiều tiết 6–10 | Chiều, tiết 6–9 | 5/5 bản TKB khối 12 đều có hai trang *Buổi sáng* và *Buổi chiều* |
| **Khối 11** | Chiều, tiết 6–10 | Sáng | 3/3 bản khối 11 chỉ có *Buổi chiều* |
| **Khối 10** | Sáng, tiết 1–5 | Chiều | 2/2 bản khối 10 chỉ có *Buổi sáng* |

> **Đính chính:** phiên bản trước của tài liệu ghi "khối 12 học sáng". Khảo sát cho thấy **khối 12 học cả hai ca** — ngoài chương trình chính còn có các tiết **bổ trợ ôn thi tốt nghiệp THPT** (Văn/Toán/Địa/Sử bổ trợ, Tiếng Anh và Sinh học tăng cường) xếp vào buổi chiều. Khối 12 vì thế là khối chiếm nhiều tài nguyên nhất.

Học sinh hệ 9+ học văn hoá nửa ngày, học nghề nửa ngày còn lại. Ca của khối là **cố định**, nên ca học nghề được suy ra hoàn toàn — bộ giải không được tự chọn.

**Điểm nghẽn suy ra từ cấu hình này:**

- **Khối 10 và khối 12 cùng học văn hoá buổi sáng** → 22 lớp tranh 31 phòng văn hoá buổi sáng (vẫn đủ), nhưng **cùng dồn về 11 xưởng buổi chiều** — đây là nút thắt nặng nhất trong tuần, càng chặt hơn khi mỗi lớp còn phải chia ca theo trần 18 HS.
- **Buổi chiều chỉ khối 11 dùng phòng văn hoá** → 11 lớp trên 31 phòng, dư nhiều.

Hệ thống cần: khai báo ca theo khối (`shift_by_grade`), tự suy ca nghề (`shift_complement`), và cảnh báo nghẽn xưởng khi hai khối cùng ca.

### 2.8 Quy mô thực tế — khảo sát từ 30 file TKB

| Hạng mục | Số lượng | Ghi chú |
|---|---|---|
| **Lớp văn hoá** | **35** | Khối 10: 11 lớp · khối 11: 12 lớp · khối 12: 12 lớp |
| **Nhóm nghề** | **~44** | K43 khối 11: 14 nhóm · K42 khối 12: 16 nhóm · cao đẳng K21+K22: ~14 lớp |
| **Giáo viên** | **~83–85** | ~51 khối nghề/CĐ + ~47 khối văn hoá, sau khi gộp các trường hợp trùng |
| **Phòng** | **54 mã** xuất hiện trong TKB | Gồm cả `DN` (doanh nghiệp) và `P QLĐT` (phòng tổ chức thi) — không phải phòng học |
| **Mô-đun nghề** | **~90** | Trải trên 16 nghề |
| **Môn văn hoá** | **13** | 11 môn chính + Sinh hoạt + Chào cờ; khối 12 thêm 5 môn bổ trợ/tăng cường |

**Ánh xạ khoá ↔ khối** (năm học mới bắt đầu tuần 01, ngày 10/8/2026 — mọi khoá lên một khối):

| Khoá | Tuần 36–46 (tháng 6/2026) | Tuần 01–03 (tháng 8/2026) |
|---|---|---|
| K43 | Khối 10 | Khối 11 |
| K42 | Khối 11 | Khối 12 |

> Hệ thống phải mô hình hoá được **khoá học tiến lên khối** theo năm học, thay vì gắn cứng khoá với khối.

**Phòng cố định của lớp văn hoá** — khối 10 và 11 dùng chung dãy `A6-501…507` và `A6-601…607` nhưng không xung đột vì khác ca. Khối 12 dùng dãy riêng `A6-3xx` và `A6-4xx`. Lưu ý hoán vị: `10A9→A6-603` nhưng `11A9→A6-605` (và ngược lại với A10).

### 2.9 Thông tin còn cần trường cung cấp

1. **Tổng số giáo viên** và phân bổ theo khoa.
2. **Mốc giờ từng tiết 1–10** (mới chỉ biết Chào cờ 7h25).
3. **Sĩ số thực tế** đang học (con số 2.000 là *chỉ tiêu*, không phải quy mô thực).
4. **Phân hiệu Huế** xếp lịch độc lập hay chung, và **giáo viên có dạy chéo hai cơ sở không** — nếu có, đây là ràng buộc lớn với bộ giải.
5. **Nghề nào thuộc diện nặng nhọc, độc hại** (trần thực hành 10 thay vì 18).

---

## 3. Các bên liên quan và vai trò

| Vai trò | Mô tả | Nhu cầu chính |
|---|---|---|
| **Phòng Đào tạo** | Chủ sở hữu nghiệp vụ, chịu trách nhiệm lịch toàn trường | Xếp nhanh, ít xung đột, xuất bản đúng hạn |
| **Cán bộ xếp TKB** | Người vận hành trực tiếp hệ thống | Nhập liệu dễ, hiểu được vì sao bế tắc, sửa tay được |
| **Trưởng khoa / Tổ trưởng bộ môn** | Quản lý phân công giảng dạy trong khoa | Khai báo nguyện vọng giáo viên, kiểm tra tải giảng dạy |
| **Giáo viên** | Người dạy | Xem lịch cá nhân, đăng ký ngày/tiết bận |
| **Sinh viên / học sinh** | Người học | Xem lịch lớp |
| **Quản trị hệ thống** | Vận hành kỹ thuật | Phân quyền, sao lưu, giám sát |

**[THIẾU]** Hệ thống hiện **không có bất kỳ cơ chế phân quyền nào**: mọi người dùng đã đăng nhập đều có toàn quyền trên dữ liệu của tenant, kể cả thao tác huỷ hoại như `POST /api/import/commit` (xoá sạch rồi ghi lại). Xem `FR-1.3`.

---

## 4. Kiến trúc hiện trạng

```
evo-scheduler-service/
├── backend/          Django 5 + django-ninja + OR-Tools CP-SAT + Celery
│   ├── config/       api.py (toàn bộ REST API), settings, celery
│   └── scheduler/    models, solver/, excel_parser, validator, horizon, tasks
├── frontend/         Next.js 16 (App Router) + React 19 + TailwindCSS v4
└── docker-compose*   PostgreSQL + Redis + backend + frontend
```

> **[ĐÃ CÓ] — ưu tiên thấp nhất.** Mục 4 và 5.1 chỉ mô tả nền tảng đang có để biết điểm xuất phát. Việc cần làm nằm ở §5.3 (khoảng trống), §6 (yêu cầu **[THIẾU]** / **[ĐỀ XUẤT]**) và §7.3 (tình huống đặc thù).

**Quyết định kỹ thuật đáng chú ý (đã có, cần giữ nguyên):**

- **Mô hình bộ giải theo khoảng thời gian.** Mỗi buổi có hai nhóm biến: tiết bắt đầu và tài nguyên được chọn. Xung đột diễn đạt bằng `IntervalVar` + `AddNoOverlap`/`AddCumulative`. Cách cũ (bool cho mỗi bộ ba buổi × tiết × phòng) sinh hơn 190 nghìn biến trên dữ liệu một trường thật và chạy 600 giây không kết luận được.
- **Giải hai pha.** Pha 1 dựng mô hình không hàm mục tiêu → dừng ngay khi có phương án đầu tiên. Pha 2 dựng mô hình đầy đủ, lấy nghiệm pha 1 làm gợi ý (`AddHint`) rồi tối ưu. Hết giờ ở pha 2 vẫn giữ được nghiệm pha 1.
- **Tiền kiểm tra số học** trước khi gọi CP-SAT, trả về `DATA_INFEASIBLE` với thực thể cụ thể thay vì `INFEASIBLE` chung chung.
- **Bảng chiếm dụng lười** (`OccupancyTable`): biến `occ` chỉ được tạo khi có ràng buộc thật sự hỏi tới.

---

### 4.1 Cách hệ thống tìm ra thời khoá biểu

Đây là bài toán **lập lịch bằng ràng buộc**: người dùng mô tả luật, hệ thống tự tìm phương án thoả mọi luật — không phải xếp tay có máy hỗ trợ.

| Bước | Nội dung |
|---|---|
| **1. Biến** | Mỗi buổi học có hai ẩn số: *bắt đầu ở tiết nào* và *dùng phòng nào*. Toàn trường ~1.300 buổi/tuần → khoảng 2.600 ẩn số |
| **2. Ràng buộc** | Mỗi luật nghiệp vụ (§7) được diễn đạt thành điều kiện toán học trên các ẩn số đó |
| **3. Bộ giải** | OR-Tools CP-SAT dùng suy luận logic để loại hàng loạt phương án sai cùng lúc, thay vì duyệt từng phương án |
| **4. Hàm mục tiêu** | Trong các phương án hợp lệ, chọn phương án có tổng điểm phạt thấp nhất theo trọng số ràng buộc mềm (§7.2) |

**Phân vai ba chức năng vận hành** — điểm này quan trọng vì quyết định trải nghiệm người dùng:

| Chức năng | Gọi bộ giải? | Thời gian | Vai trò |
|---|---|---|---|
| Kiểm tra khả thi (FR-5) | **Không** — chỉ tính số học | ~3 giây | Bắt mâu thuẫn trước, chỉ đúng thực thể gây lỗi |
| Kế hoạch xếp (FR-6.10) | **Không** — người đặt thứ tự | — | Quyết định trình tự các lớp xếp |
| Xếp lịch (FR-6) | **Có** | 2–10 phút | Thực sự tìm lời giải |

> **Lý do tách Kiểm tra khỏi Xếp lịch:** CP-SAT khi gặp dữ liệu bất khả thi sẽ chạy hết thời gian cho phép rồi trả về `INFEASIBLE` mà **không nêu nguyên nhân**. Với dữ liệu một trường thật đó là 10 phút chờ để nhận một thông báo vô dụng. Tiền kiểm tra số học trả lời trong vài giây và chỉ đúng thực thể mâu thuẫn.

**Giải hai pha** (đã có, cần giữ): pha 1 dựng mô hình không hàm mục tiêu nên dừng ngay khi có phương án đầu tiên; pha 2 dựng lại mô hình đầy đủ, lấy nghiệm pha 1 làm gợi ý rồi tối ưu. Hết giờ hoặc người dùng dừng ở pha 2 thì **nghiệm pha 1 vẫn được giữ**.

### 4.2 Trình tự xếp nhiều chương trình **[ĐỀ XUẤT]**

Ba chương trình dùng chung giáo viên và xưởng, nên không thể giải song song. Đề xuất chia thành **bốn lớp xếp tuần tự**, xong lớp nào thì khoá kết quả làm ràng buộc cho lớp sau:

| Lớp | Nội dung | Bậc tự do | Bị khoá bởi |
|---|---|---|---|
| **0** | Ghim cố định: Chào cờ T2 tiết 1, tuần thực tập CĐ, tiết sinh hoạt | 0 | — |
| **1** | Văn hoá theo khối (ca cố định, phòng gắn theo lớp) | Thấp | Lớp 0 |
| **2** | Nghề hệ song bằng 9+ (nhận ca bù, chia ca trần 18, giành xưởng) | Cao | Lớp 0, 1 |
| **3** | Trung cấp thường + Cao đẳng | Cao | Lớp 0, 1, 2 |

**Nguyên tắc: lớp ít bậc tự do nhất xếp trước.** Văn hoá đi trước vì ca đã cố định và phòng gắn chết theo lớp; nếu xếp sau, giáo viên văn hoá đã bị khối nghề chiếm hết giờ.

> **Cần trường xác nhận:** đây là trình tự đề xuất, chưa phải quy trình trường đang dùng. Một phương án thay thế đáng cân nhắc là đảo lớp 2 lên trước lớp 1 — xếp nghề trước để giành xưởng (nút thắt nặng nhất), rồi nhét văn hoá vào chỗ còn lại. Hệ thống nên **cho phép đổi thứ tự các lớp xếp** để thử cả hai rồi so kết quả.

---

## 5. Mô hình dữ liệu

### 5.1 Thực thể hiện có **[ĐÃ CÓ]**

| Thực thể | Vai trò nghiệp vụ | Trường chính |
|---|---|---|
| `Tenant` | Đơn vị trường (đa đơn vị) | `code`, `name`, `config_json` |
| `Teacher` | Giáo viên | `code`, `name`, `blocks[]`, `quota_standard_hours` |
| `StudentGroup` | Lớp học | `code`, `name`, `enrollment_type`, `size` |
| `Resource` | Phòng / xưởng / bộ dụng cụ | `type`, `capacity`, `quantity`, `available_quantity` |
| `Module` | Môn học / mô-đun | `theory_hours`, `practice_hours`, `student_group` |
| `TeacherModule` | Năng lực giảng dạy | `teacher` × `module` |
| `Session` | Buổi học (đơn vị xếp lịch) | `session_type`, `duration_slots`, `tier`, `assigned_*`, `is_locked` |
| `ConstraintRule` | Ràng buộc khai báo được | `type`, `scope_json`, `params_json`, `hardness`, `weight` |
| `Schedule` | Phương án TKB | `status`, `tier`, `objective_value`, `weights_json` |
| `SolveJob` | Phiên chạy bộ giải | `status`, `phase`, `progress`, `metrics_json` |
| `User` | Tài khoản | `email`, `password_hash`, `tenant` |

### 5.2 Bảng liệt kê giá trị hợp lệ

| Enum | Giá trị | Nhãn tiếng Việt |
|---|---|---|
| `Session.SessionType` | `theory` / `practice` | Lý thuyết / Thực hành |
| `Session.Tier` | `culture` / `vocational` | Văn hoá / Nghề |
| `Resource.ResourceType` | `theory_room` / `workshop` / `tool_set` | Phòng lý thuyết / Xưởng / Bộ dụng cụ |
| `StudentGroup.EnrollmentType` | `dual_degree` / `college` | Song bằng / Cao đẳng |
| `Teacher.Block` | `culture` / `vocational` / `both` | Văn hoá / Nghề / Cả hai |
| `Schedule.Status` | `draft` / `solving` / `solved` / `failed` / `published` | Nháp / Đang giải / Đã giải / Lỗi / Đã xuất bản |
| `SolveJob.Phase` | `building_model` / `solving` / `post_processing` | Đang dựng mô hình / Đang giải / Đang xử lý kết quả |

### 5.3 Khoảng trống mô hình dữ liệu **[THIẾU]**

Đây là những phát hiện quan trọng nhất, ảnh hưởng trực tiếp tới việc hệ thống có dùng được cho trường thật hay không. Cột cuối ánh xạ sang **sáu bài toán trọng tâm** ở §0b:

| Khoảng trống | Thuộc bài toán |
|---|---|
| G-11, **G-18** | ① Lớp tách nhóm và gộp nhóm |
| G-14 | ② Trần sĩ số |
| G-3, G-15, **G-16**, **G-17** | ③ Ca học theo khối + ba luồng lịch |
| G-10 | ④ Đồng giảng |
| G-12 | ⑤ Tuần thực tập |
| G-13 | ⑥ Giờ chuẩn |
| G-1, G-2, G-7 | Nền tảng — chặn mọi bài toán trên |


| # | Khoảng trống | Hệ quả nghiệp vụ | Ưu tiên |
|---|---|---|---|
| G-1 | `Session` **không có khoá ngoại tới `Schedule`** | Mọi phương án TKB của cùng một tenant dùng chung một trạng thái xếp lịch. Không thể có hai phương án song song để so sánh; `/schedule/{id}/sessions` trả về toàn bộ buổi học của tenant bất kể `schedule_id` | **Chặn** |
| G-2 | `Module.theory_hours` / `practice_hours` **không bao giờ được bung thành `Session`** | Người dùng khai số giờ chương trình nhưng hệ thống không sinh buổi học tương ứng; buổi học chỉ đến từ sheet `FixedSessions` | **Chặn** |
| G-3 | Không có mô hình **học kỳ / tuần lịch** (`week_start` khai báo nhưng không bao giờ ghi) | Không xếp được lịch theo tiến độ nhiều tuần — trong khi mô-đun nghề học cuốn chiếu theo tuần | Cao |
| G-4 | Không có thực thể **Khoa / Bộ môn / Ngành nghề** | Không lọc, phân quyền hay báo cáo theo khoa được | Cao |
| G-5 | Không có **cơ sở đào tạo (campus)** | Trường nhiều cơ sở không diễn đạt được ràng buộc di chuyển giữa các cơ sở | Cao |
| G-6 | `Schedule.Status.PUBLISHED` **không bao giờ được gán**, không có endpoint xuất bản | Không phân biệt được bản nháp và bản chính thức đã phát hành | Trung bình |
| G-7 | `User` không có trường vai trò | Không phân quyền được (xem §3) | **Chặn** |
| G-8 | Ba loại ràng buộc solver (`teacher_no_overlap`, `student_no_overlap`, `shared_resource_pool`) **không nằm trong `RuleType.choices`** | Không lưu được vào CSDL, phải tiêm cứng trong mã | Thấp |
| G-9 | `ConstraintRule.hardness` **không ảnh hưởng tới bộ giải** | Cứng/mềm được quyết định bởi việc module có trả về biểu thức mục tiêu hay không, không phải bởi trường dữ liệu. Người dùng đổi `hardness` sẽ không thấy tác dụng | Cao |
| G-10 | Không có **nhóm giáo viên**, **dạy chung tiết**, **lớp ghép** | Không diễn đạt được các tình huống nghiệp vụ ở §7.3 | Cao |
| G-11 | **Không diễn đạt được quan hệ nhiều-nhiều giữa lớp văn hoá và nhóm nghề** | Đã xác nhận từ TKB thật: lớp 11A3 tách thành 3 nhóm nghề (16/17/30 SV). Không có ràng buộc này, hệ thống sẽ xếp tiết văn hoá của 11A3 trùng giờ nhóm nghề của chính lớp đó | **Chặn** |
| G-12 | Không có **khối chặn cả tuần** cho thực tập tốt nghiệp / thực tập sản xuất | Lớp đi thực tập vẫn bị bộ giải xếp tiết; khối thực tập không tiêu tốn phòng và giáo viên nên không mô hình hoá được bằng `Session` thường | Cao |
| G-13 | Không phân biệt **giờ chuẩn** với **giờ thực dạy** | `quota_standard_hours` đang so trực tiếp với số tiết. Theo TT 07/2017, 45 phút lý thuyết = 1 giờ chuẩn nhưng 60 phút thực hành = 1 giờ chuẩn — hệ số khác nhau. Báo cáo tải giảng dạy hiện sẽ sai | Cao |
| G-14 | Không có **trần sĩ số riêng cho lý thuyết và thực hành** | Quy định: lý thuyết ≤ 35, thực hành ≤ 18 (≤ 10 nghề độc hại). Lớp văn hoá thực tế tới 44 SV. `capacity_limit` chỉ so sức chứa phòng, không áp trần theo loại buổi — đây chính là lý do lớp 9+ phải tách nhóm | **Chặn** |
| G-15 | Không có **nhịp phát hành theo tuần** song song với lịch gốc ổn định | Trường phát hành TKB cao đẳng và trung cấp **hằng tuần** (tuần 01–46) nhưng TKB văn hoá **ổn định cả kỳ**. Hệ thống chỉ có một khung `weeks` duy nhất | Cao |
| G-16 | Không có **thuộc tính ca học của khối** | Khối 10 học văn hoá sáng, khối 11 chiều, khối 12 cả ngày; ca nghề là phần bù. Không có ràng buộc này, bộ giải sẽ xếp tiết văn hoá khối 11 vào buổi sáng — sai hoàn toàn thực tế vận hành | **Chặn** |
| G-17 | Không diễn đạt được **phòng dùng chung giữa các khối** | 4 phòng lý thuyết to + 5 nhỏ dùng chung khối văn hoá và khối nghề. Không mô hình hoá thì bộ giải không thấy tranh chấp | Cao |
| G-18 | **Không gộp được nhiều lớp văn hoá vào một nhóm nghề** | Đã xác nhận từ TKB K42: `12A1 + 12A4` → KT lắp đặt điện (44 HS); `12A1 + 12A2` → Thiết kế đồ hoạ (54 HS). Lớp 12A1 vừa gộp với 12A4 ở nghề này, vừa gộp với 12A2 ở nghề kia. Quan hệ lớp ↔ nhóm nghề là **nhiều-nhiều theo cả hai chiều**, không chỉ một chiều tách nhóm | **Chặn** |
| G-19 | Không có **buổi học ngoài chương trình chính** (bổ trợ, tăng cường) | Khối 12 có Văn/Toán/Địa/Sử bổ trợ và Tiếng Anh, Sinh học tăng cường, xếp vào các tiết ngoài bảng chính. Đây là lý do khối 12 chiếm cả hai ca | Cao |
| G-20 | Không có **địa điểm ngoài trường** | TKB dùng mã `DN` (doanh nghiệp) cho các buổi thực tập tại doanh nghiệp; Điều 4 quy chế công nhận doanh nghiệp là địa điểm đào tạo hợp lệ. Cũng cần `ONLINE` — đã xuất hiện một buổi trong TKB K42 | Trung bình |

---

## 6. Yêu cầu chức năng

### FR-1. Quản trị, tài khoản và phân quyền

| Mã | Yêu cầu | Trạng thái |
|---|---|---|
| FR-1.1 | Đăng ký tài khoản, tự động tạo tenant và sinh dữ liệu mẫu | **[ĐÃ CÓ]** |
| FR-1.2 | Đăng nhập bằng email/mật khẩu, cấp JWT HS256 hạn 12 giờ | **[ĐÃ CÓ]** |
| FR-1.3 | **Phân quyền theo vai trò**: Quản trị / Phòng Đào tạo / Trưởng khoa / Giáo viên / Sinh viên. Mỗi endpoint phải khai báo vai trò tối thiểu | **[THIẾU]** |
| FR-1.4 | Giữ phiên đăng nhập qua lần tải lại trang | **[THIẾU]** — token chỉ nằm trong `useState`, tải lại trang là mất phiên |
| FR-1.5 | Nhật ký thao tác (ai xuất bản, ai import, ai sửa tiết) | **[ĐỀ XUẤT]** |
| FR-1.6 | Đăng ký phải được kiểm soát: trường thật không thể để ai đăng ký cũng tạo được tenant mới | **[ĐỀ XUẤT]** |

### FR-2. Quản lý dữ liệu nền

| Mã | Yêu cầu | Trạng thái |
|---|---|---|
| FR-2.1 | Nhập dữ liệu từ Excel với 6 sheet bắt buộc + 1 sheet cấu hình | **[ĐÃ CÓ]** |
| FR-2.2 | Tải file mẫu Excel có sẵn dòng ví dụ, tiêu đề tiếng Việt | **[ĐÃ CÓ]** |
| FR-2.3 | Nhận diện tên sheet/cột không dấu, sai hoa thường, nhiều biến thể | **[ĐÃ CÓ]** |
| FR-2.4 | Kiểm tra dữ liệu trước khi ghi, phân biệt lỗi và cảnh báo, chỉ rõ dòng/cột | **[ĐÃ CÓ]** |
| FR-2.5 | Xem trước kết quả kiểm tra rồi mới xác nhận ghi (3 bước) | **[ĐÃ CÓ]** |
| FR-2.6 | **CRUD trực tiếp trên giao diện** cho giáo viên, lớp, môn, phòng | **[THIẾU]** — chỉ có `GET /teachers`; mọi thay đổi khác phải qua import hoặc Django admin |
| FR-2.7 | **Import không huỷ hoại**: hiện `import/commit` xoá sạch toàn bộ `Session`, `TeacherModule`, `Module`, `Resource`, `StudentGroup`, `Teacher` của tenant rồi ghi lại | **[THIẾU]** — cần chế độ cập nhật/bổ sung |
| FR-2.8 | **Sinh buổi học từ số giờ chương trình** (giải quyết G-2): từ `theory_hours`/`practice_hours` và quy tắc gộp tiết, tự sinh `Session` | **[THIẾU]** |
| FR-2.9 | Quản lý Khoa / Bộ môn / Ngành nghề / Cơ sở đào tạo | **[THIẾU]** (G-4, G-5) |

### FR-3. Khung thời khoá biểu

| Mã | Yêu cầu | Trạng thái |
|---|---|---|
| FR-3.1 | Cấu hình số tuần (1–8), số ngày/tuần (1–7), số tiết/ngày (1–16), số tiết buổi sáng | **[ĐÃ CÓ]** |
| FR-3.2 | Xem trước tổng số tiết khả dụng mỗi tuần khi đang chỉnh | **[ĐÃ CÓ]** |
| FR-3.3 | Cấu hình khung giờ riêng cho từng khối (`culture_horizon`, `vocational_horizon`) | **[ĐÃ CÓ]** ở tầng dữ liệu, **[THIẾU]** ở giao diện |
| FR-3.4 | Khai báo mốc giờ thực tế của từng tiết (07:00–07:45…) để xuất lịch có giờ | **[ĐỀ XUẤT]** — trường mới công bố mốc Chào cờ 7h25 |
| FR-3.5 | Khung mặc định theo thực tế trường: **T2–T6, 10 tiết/ngày** (1–5 sáng, 6–10 chiều); cho phép mở tới T7/CN và 6:00–22:00 theo Điều 3.4.a quy chế | **[ĐỀ XUẤT]** |
| FR-3.6 | **Đánh số tuần theo năm học (tuần 01–46)** và phát hành TKB theo từng tuần, song song với lịch gốc ổn định cả kỳ | **[THIẾU]** (G-15) |
| FR-3.7 | Lịch nghỉ: nghỉ hè, lễ tết, khai giảng, bế giảng (Điều 5 quy chế) | **[ĐỀ XUẤT]** |

### FR-4. Khai báo ràng buộc

| Mã | Yêu cầu | Trạng thái |
|---|---|---|
| FR-4.1 | Điều chỉnh 4 trọng số mục tiêu bằng thanh trượt 0–10 | **[ĐÃ CÓ]** |
| FR-4.2 | **Giao diện tạo/sửa/xoá `ConstraintRule`** | **[THIẾU]** — `ConstraintBuilder` chỉ chỉnh 4 trọng số dù tên gọi là "trình tạo ràng buộc"; không có API CRUD cho ràng buộc, chỉ có Django admin |
| FR-4.3 | Thư viện ràng buộc mẫu đặt sẵn theo thực tiễn tốt (xem §7.4) | **[ĐỀ XUẤT]** |
| FR-4.4 | Đặt độ ưu tiên (Cao/Trung bình/Thấp) và trọng số cho từng ràng buộc, có nút khôi phục mặc định | **[ĐỀ XUẤT]** |
| FR-4.5 | Khai báo ràng buộc bằng lưới tuần trực quan (chọn ô "Không dạy" / "Hạn chế xếp") | **[ĐỀ XUẤT]** |
| FR-4.6 | Làm cho `hardness` thật sự có tác dụng (giải quyết G-9) | **[THIẾU]** |

### FR-5. Kiểm tra khả thi

| Mã | Yêu cầu | Trạng thái |
|---|---|---|
| FR-5.1 | Chạy tiền kiểm tra số học, trả kết quả theo từng khối | **[ĐÃ CÓ]** |
| FR-5.2 | 13 phép kiểm tra cụ thể (xem §8) chỉ đúng thực thể gây mâu thuẫn | **[ĐÃ CÓ]** |
| FR-5.3 | Chặn chạy bộ giải khi còn lỗi chặn, kèm hướng dẫn sửa bằng tiếng Việt | **[ĐÃ CÓ]** |
| FR-5.4 | Gợi ý cách khắc phục cụ thể ("thiếu 2 xưởng hàn" → đề xuất nới khung giờ hoặc tách lớp) | **[ĐỀ XUẤT]** |

### FR-6. Xếp lịch tự động

| Mã | Yêu cầu | Trạng thái |
|---|---|---|
| FR-6.1 | Chạy bộ giải bất đồng bộ qua Celery, trả `202` kèm `solve_job_id` | **[ĐÃ CÓ]** |
| FR-6.2 | Theo dõi tiến độ theo pha, tự động hỏi trạng thái mỗi 2 giây, hết giờ sau 10 phút | **[ĐÃ CÓ]** |
| FR-6.3 | Xếp hai khối tuần tự: văn hoá trước, khoá lại, rồi xếp nghề tránh các tiết đã khoá | **[ĐÃ CÓ]** |
| FR-6.4 | Tự động phân công giáo viên khi buổi học chưa có người dạy | **[ĐÃ CÓ]** |
| FR-6.5 | Giữ nghiệm pha 1 khi pha 2 hết giờ | **[ĐÃ CÓ]** |
| FR-6.6 | **Dừng bộ giải giữa chừng** | **[THIẾU]** — FTKB có nút "Dừng" |
| FR-6.7 | **Xếp trước (ghim tiết)**: ghim Chào cờ, Sinh hoạt, tiết không học, tiết GVCN, hoặc một mô-đun cụ thể vào ô cố định trước khi chạy. Phạm vi áp dụng: toàn trường / theo khối / theo nhóm | **[ĐỀ XUẤT]** |
| FR-6.8 | **Kế thừa lịch cũ**: giữ nguyên phần lớn lịch học kỳ trước, chỉ xếp lại giáo viên có thay đổi phân công | **[ĐỀ XUẤT]** — đây là tính năng khác biệt của FTKB, rất giá trị khi sang học kỳ 2 |
| FR-6.9 | Lưu lịch sử các phiên chạy, so sánh và khôi phục phiên bản | **[ĐỀ XUẤT]** |
| FR-6.10 | **Kế hoạch xếp nhiều lớp**: khai báo trình tự các lớp xếp (§4.2), đổi được thứ tự, chạy tuần tự và khoá dần | **[THIẾU]** — hiện chỉ xếp hai khối văn hoá/nghề cứng trong mã |
| FR-6.11 | Chạy lại **một lớp xếp** mà không phá kết quả các lớp khác | **[ĐỀ XUẤT]** |

### FR-7. Xem và tinh chỉnh thời khoá biểu

| Mã | Yêu cầu | Trạng thái |
|---|---|---|
| FR-7.1 | Lưới TKB cả tuần, xem theo giáo viên / lớp / phòng | **[ĐÃ CÓ]** |
| FR-7.2 | Lọc theo giáo viên, lớp, phòng; làm nổi bật và làm mờ tương ứng | **[ĐÃ CÓ]** |
| FR-7.3 | Kéo thả tiết học giữa các ô, cập nhật lạc quan, tự hoàn tác khi thất bại | **[ĐÃ CÓ]** |
| FR-7.4 | Sửa cục bộ: chỉ giải lại vùng lân cận (cùng giáo viên / lớp / phòng), giữ nguyên phần còn lại | **[ĐÃ CÓ]** |
| FR-7.5 | Cảnh báo xung đột ngay khi rê chuột lên ô đích | **[ĐÃ CÓ]** |
| FR-7.6 | Xem chi tiết buổi học trong hộp thoại | **[ĐÃ CÓ]** |
| FR-7.7 | Thẻ thống kê: tổng tiết, đã xếp, văn hoá, nghề, xung đột | **[ĐÃ CÓ]** |
| FR-7.8 | **Bốn phương pháp tinh chỉnh thủ công** (xem §7.5) | **[ĐỀ XUẤT]** |
| FR-7.9 | **Khay tiết chờ xếp**: kéo tiết ra khỏi lưới, để đó, xếp lại sau; chỉ thả được vào ô trống | **[ĐỀ XUẤT]** |
| FR-7.12 | **Bảng màu vi phạm** khi tinh chỉnh: xanh = đổi được, hồng nhạt = vi phạm ràng buộc, hồng đậm = trùng tiết (chặn), da cam = vi phạm "hạn chế xếp" | **[ĐỀ XUẤT]** |
| FR-7.13 | **Khôi phục TKB gốc** và **lùi từng bước** sau khi tinh chỉnh | **[ĐỀ XUẤT]** |
| FR-7.14 | **Kiểm tra ràng buộc sau khi xếp**: bảng theo 4 nhóm (GV, nhóm GV, môn phổ biến, môn khác), tô xanh/đỏ theo thoả/vi phạm | **[ĐỀ XUẤT]** |
| FR-7.15 | **Bảng giáo viên toàn tuần**: mỗi dòng một GV, mỗi cột một tiết, ô ghi nhóm đang dạy; lọc theo ca; hiện ô "Không dạy" theo ràng buộc; cột tổng tiết | **[ĐỀ XUẤT]** |
| FR-7.16 | Lưu **mọi thao tác tinh chỉnh** tự động, quản lý theo phiên bản, đối chiếu được với phiên bản gốc | **[ĐỀ XUẤT]** |
| FR-7.10 | Khoá/mở khoá từng tiết ngay trên lưới | **[THIẾU]** — `is_locked` có trong dữ liệu nhưng không bật/tắt được từ giao diện |
| FR-7.11 | Phát hiện xung đột phải tính cả độ dài buổi học | **[THIẾU]** — hiện chỉ so tiết bắt đầu, bỏ sót chồng lấn của buổi nhiều tiết |

### FR-8. Xuất bản và phân phối

| Mã | Yêu cầu | Trạng thái |
|---|---|---|
| FR-8.1 | Xuất Excel hai sheet: lưới tổng và bảng chi tiết | **[ĐÃ CÓ]** |
| FR-8.2 | **Xuất PDF** đúng mẫu TKB của trường (xem §9) | **[ĐỀ XUẤT]** |
| FR-8.3 | **Xuất bản chính thức**: chuyển trạng thái `published`, chốt phiên bản (giải quyết G-6) | **[THIẾU]** |
| FR-8.4 | Cổng xem lịch cho giáo viên và sinh viên | **[ĐỀ XUẤT]** |
| FR-8.5 | Chia sẻ lịch bằng đường dẫn công khai | **[ĐỀ XUẤT]** |
| FR-8.6 | Thông báo khi lịch thay đổi | **[ĐỀ XUẤT]** |

### FR-9. Báo cáo

| Mã | Yêu cầu | Trạng thái |
|---|---|---|
| FR-9.1 | Bảng điều khiển: số lượng thực thể, tỉ lệ xếp lịch, tải theo ngày | **[ĐÃ CÓ]** |
| FR-9.2 | So sánh lịch trước/sau khi chạy bộ giải, làm nổi bật tiết đã dời | **[ĐÃ CÓ]** |
| FR-9.3 | **Báo cáo tải giảng dạy** quy đổi đúng **giờ chuẩn** (45 phút LT = 1 giờ chuẩn; 60 phút TH = 1 giờ chuẩn), đối chiếu định mức năm (CĐ 380–450, TC 430–510) | **[ĐỀ XUẤT]** — cần G-13 |
| FR-9.4 | **Báo cáo suất sử dụng phòng/xưởng** | **[ĐỀ XUẤT]** |
| FR-9.5 | Báo cáo tiến độ thực hiện chương trình theo mô-đun, **tách riêng quỹ giờ văn hoá và quỹ giờ nghề** cho học sinh 9+ (BR-11) | **[ĐỀ XUẤT]** |
| FR-9.6 | Báo cáo tỉ lệ lý thuyết/thực hành theo chương trình, đối chiếu ngưỡng quy định (CĐ: TH 50–70%; TC: TH 55–75%) | **[ĐỀ XUẤT]** |

---

## 7. Quy tắc nghiệp vụ và ràng buộc xếp lịch

### 7.1 Ràng buộc cứng — luôn áp dụng, không thương lượng

| Mã | Quy tắc | Cài đặt |
|---|---|---|
| CT-1 | Một giáo viên không dạy hai buổi cùng lúc | `teacher_no_overlap` — `AddNoOverlap` |
| CT-2 | Một lớp không học hai buổi cùng lúc | `student_no_overlap` — `AddNoOverlap` |
| CT-3 | Sức chứa tài nguyên không bị vượt | `shared_resource_pool` — `AddCumulative` theo `available_quantity` |
| CT-4 | Buổi lý thuyết vào phòng lý thuyết; buổi thực hành vào xưởng hoặc bộ dụng cụ | `resource_requirement` |
| CT-5 | Sĩ số lớp không vượt sức chứa phòng (`capacity = 0` nghĩa là không giới hạn) | `capacity_limit` |
| CT-6 | Buổi nhiều tiết phải liền mạch trong cùng một ngày, không vắt qua ngày | Miền giá trị `valid_starts` |
| CT-7 | Tiết đã khoá giữ nguyên vị trí | `_apply_locked` |
| CT-8 | Không xếp vào thời điểm đã khai báo bận | `unavailability` |
| CT-9 | Tổng giờ dạy không vượt định mức giáo viên | `quota_limit` |
| CT-10 | Các buổi trong nhóm phải liền kề nhau | `adjacency` |
| CT-11 | Các buổi loại trừ nhau không trùng tiết | `exclusion` |
| CT-18 | **Tiết văn hoá phải nằm đúng ca của khối** (12 sáng · 11 chiều · 10 sáng) | **[THIẾU]** — `shift_by_grade` |
| CT-19 | **Buổi học nghề nằm ở ca bù của ca văn hoá** | **[THIẾU]** — `shift_complement` |
| CT-20 | **Trần sĩ số theo loại buổi** (LT 35 · TH 18 · độc hại 10), tách khỏi sức chứa phòng | **[THIẾU]** — `capacity_by_type` |
| CT-21 | **Hai nhóm nghề cùng lớp văn hoá không trùng giờ** | **[THIẾU]** — `group_same_class` |
| CT-22 | **Nhóm nghề gộp nhiều lớp thì chặn mọi lớp thành viên** | **[THIẾU]** — `group_multi_class` |
| CT-23 | Buổi tại doanh nghiệp và buổi trực tuyến **không chiếm phòng** | **[THIẾU]** — `offsite_no_room` |

### 7.2 Ràng buộc mềm — mục tiêu tối ưu

| Mã | Tiêu chí | Trọng số mặc định | Đo lường |
|---|---|---|---|
| CT-12 | Giảm giờ trống của giáo viên | 3 | `span − used` trong ngày |
| CT-13 | Giảm số lần đổi phòng của lớp | 2 | Số phòng khác nhau − 1 mỗi ngày |
| CT-14 | Dồn lịch gọn, ít ngày | 5 | Số ngày lớp có tiết |
| CT-15 | Cân bằng tải giáo viên | 4 | `max − min` tải theo ngày |
| CT-16 | Tôn trọng nguyện vọng thời điểm | Theo khai báo | `preference` |
| CT-17 | San đều tải giữa các giáo viên | Theo khai báo | `distribution` |

### 7.3 Tình huống nghiệp vụ đặc thù cần hỗ trợ **[ĐỀ XUẤT]**

Rút ra từ tài liệu *Dạy chung lớp* và thực tế trường nghề — hiện hệ thống **chưa diễn đạt được** các tình huống này (G-10):

| Mã | Tình huống | Yêu cầu mô hình |
|---|---|---|
| BR-1 | **Lớp ghép giảng đường**: nhiều lớp học chung một tiết, một giáo viên, một phòng lớn | Buổi học phải liên kết được với nhiều `StudentGroup` |
| BR-2 | **Tách lớp theo nhóm**: lớp chia đôi, nam học Tin, nữ học May, cùng tiết, hai phòng, hai giáo viên | Cần khái niệm nhóm con của lớp |
| BR-3 | **Dạy chung tiết (đồng giảng)**: hai giáo viên cùng đứng một lớp một tiết; hệ thống phải chặn cả hai khỏi bị xếp trùng ở lớp khác | `assigned_teachers` đã là quan hệ nhiều-nhiều nhưng chưa có giao diện và ràng buộc tương ứng |
| BR-4 | **Giáo viên luân phiên**: môn 3 tiết, 2 giáo viên thay nhau, 1 tiết dạy chung | Cần tách môn thành các buổi có giáo viên khác nhau |
| BR-5 | **Nhóm giáo viên**: đặt ràng buộc chung cho cả tổ bộ môn thay vì từng người | Cần thực thể nhóm giáo viên |
| BR-6 | **Ràng buộc di chuyển giữa cơ sở**: giáo viên dạy ở hai cơ sở trong cùng buổi phải có khoảng nghỉ đủ để di chuyển | Cần thực thể cơ sở (G-5) |
| BR-7 | **Lớp văn hoá tách nhiều nhóm nghề** *(đã xác nhận từ TKB thật)*: 11A3 → 3 nhóm nghề 16/17/30 SV. Khi một nhóm nghề của lớp đang học, cả lớp không thể có tiết văn hoá | Quan hệ nhiều-nhiều `StudentGroup` ↔ nhóm nghề, kèm ràng buộc loại trừ theo lớp gốc (G-11) |
| BR-8 | **Tuần thực tập trọn gói**: lớp đi thực tập tốt nghiệp/sản xuất chiếm cả tuần, không dùng phòng và giáo viên của trường | Loại buổi học đặc biệt, chặn lớp nhưng không tiêu tốn tài nguyên (G-12) |
| BR-9 | **Trần sĩ số theo loại buổi**: lý thuyết ≤ 35, thực hành ≤ 18, nghề độc hại ≤ 10 | Trần cấu hình được theo `session_type` và theo nghề (G-14) |
| BR-10 | **Chào cờ thứ Hai 7h25**: sự kiện chặn toàn trường | Xếp trước, khoá cứng cho mọi lớp (FR-6.7) |
| BR-11 | **Hai quỹ giờ độc lập cho học sinh 9+**: giờ văn hoá không tính vào thời gian đào tạo nghề (Điều 3.5 quy chế trường) | Tách hạch toán tiến độ theo từng khối, không cộng dồn |
| BR-12 | **Ca văn hoá cố định theo khối**: khối 12 sáng, khối 11 chiều, khối 10 sáng | Thuộc tính ca của khối; bộ giải không được tự chọn |
| BR-13 | **Ca nghề là phần bù của ca văn hoá**: học sinh học văn hoá nửa ngày, nghề nửa ngày kia | Suy ra tự động từ BR-12, không khai báo riêng |
| BR-14 | **Phòng lý thuyết nghề dùng chung khối văn hoá** (4 to + 5 nhỏ) | Một nhóm phòng phục vụ nhiều khối; bộ giải phải thấy tranh chấp |
| BR-15 | **Nhiều lớp văn hoá gộp một nhóm nghề** *(đã xác nhận từ TKB K42)*: `12A1+12A4` → 44 HS; `12A1+12A2` → 54 HS | Nhóm nghề liên kết nhiều `StudentGroup`; sĩ số cộng dồn; khi nhóm học thì **mọi lớp thành viên** đều bị chặn (G-18) |
| BR-16 | **Buổi bổ trợ, tăng cường ngoài chương trình chính** — khối 12 có Văn/Toán/Địa/Sử bổ trợ, Tiếng Anh và Sinh học tăng cường | Loại buổi riêng, xếp ngoài bảng chính, vẫn chiếm phòng và giáo viên (G-19) |
| BR-17 | **Địa điểm ngoài trường**: thực tập tại doanh nghiệp (`DN`), buổi học trực tuyến (`ONLINE`) | Không chiếm phòng của trường; `ONLINE` cũng không chiếm phòng nhưng vẫn chặn lớp và tính tải GV (G-20) |

### 7.4 Bộ ràng buộc khuyến nghị **[ĐỀ XUẤT]**

Theo tài liệu *Các ràng buộc nên sử dụng*, cấu hình mặc định nên đặt sẵn để lịch "đẹp và khoa học":

**Với giáo viên:**
- Số tiết dạy ít nhất trong một buổi: **2** (tránh đến trường chỉ dạy 1 tiết)
- Không xếp cách quá 1 tiết trong một buổi (tránh giờ trống rời rạc)
- Số tiết dạy nhiều nhất trong một buổi: **4**
- Số ngày nghỉ trong tuần: **1**

**Với môn học:**
- Chỉ học 1 tiết trong 1 buổi — áp dụng cho môn có 2–3 tiết/tuần
- Môn nhiều tiết nên có cặp tiết xếp liền (ví dụ Toán, Ngữ văn)
- Xếp cách ngày chỉ nên áp dụng cho môn 2 tiết; từ 3–4 tiết trở lên sẽ phá vỡ ràng buộc ngày nghỉ
- Không xếp môn Giáo dục thể chất vào tiết 5 (tiết cuối buổi sáng)

---

### 7.5 Bốn phương pháp tinh chỉnh thủ công **[ĐỀ XUẤT]**

Xếp tự động không bao giờ thay thế hoàn toàn con người: cán bộ đào tạo luôn cần sửa vài chỗ theo tình huống thực tế mà hệ thống không biết. Theo tài liệu FTKB, cần **bốn phương pháp**, tăng dần độ phức tạp:

| Cách | Tên | Cơ chế | Khi nào dùng |
|---|---|---|---|
| **1** | Đổi tiết giữa hai giáo viên cùng nhóm | Chọn một buổi → hệ thống tô màu các ô đổi được → kéo thả → xác nhận | Trường hợp đơn giản nhất, đổi trực tiếp |
| **2** | Đổi qua giáo viên trung gian | Thử cách 1 trước; không được thì tìm **giáo viên trung gian** để đổi vòng, báo số người phải đổi chỗ | Khi không có cặp đổi trực tiếp nào hợp lệ |
| **3** | Đổi giữa hai hàng giáo viên | Chọn một buổi → **tô sáng mọi phân công cùng khung giờ trên toàn trường** → kéo thả | Cần tìm chỗ đổi ngoài phạm vi một nhóm |
| **4** | Xếp tay từ khay chờ | Kéo buổi ra **khay chờ xếp**, rồi thả vào ô trống mong muốn | Khi muốn tự quyết định hoàn toàn |

> **Cách 1 là trường hợp riêng của cách 2** — hệ thống luôn thử đổi trực tiếp trước rồi mới tìm trung gian.

**Bảng màu bắt buộc** khi tinh chỉnh (FR-7.12):

| Màu | Ý nghĩa |
|---|---|
| Xanh | Lựa chọn tốt nhất — thoả mọi ràng buộc |
| Hồng nhạt | Vi phạm ràng buộc cứng hoặc mềm |
| Hồng đậm | **Trùng tiết — không cho phép đổi** |
| Da cam | Vi phạm ràng buộc "hạn chế xếp" của giáo viên hoặc nhóm giáo viên |

**An toàn khi thao tác:** mọi thay đổi được lưu tự động; phải có **lùi từng bước** và **khôi phục TKB gốc**; tiết đã khoá không bị di chuyển.

---

## 8. Chẩn đoán và thông báo lỗi

Hệ thống phát hiện **13 loại mâu thuẫn dữ liệu** trước khi gọi bộ giải **[ĐÃ CÓ]**:

| Mã lỗi | Mức | Ý nghĩa |
|---|---|---|
| `empty_horizon` | Lỗi | Chưa cấu hình khung thời gian |
| `no_resources` | Lỗi | Chưa khai báo phòng/thiết bị nào |
| `no_sessions` | Cảnh báo | Không có buổi học nào để xếp |
| `session_too_long` | Lỗi | Buổi học dài hơn một ngày học |
| `group_overloaded` | Lỗi | Lớp cần nhiều tiết hơn số tiết khả dụng |
| `teacher_overloaded` | Lỗi | Giáo viên bị buộc dạy quá số tiết khả dụng |
| `teacher_pool_overloaded` | Lỗi | Cả nhóm giáo viên cùng dạy một tập môn không đủ năng lực |
| `resource_pool_overloaded` | Lỗi | Tổng nhu cầu vượt tổng cung tài nguyên cùng loại |
| `resource_capacity_shortage` | Lỗi | Thiếu phòng theo từng ngưỡng sức chứa (kiểm tra điều kiện Hall) |
| `no_matching_resource` | Lỗi | Buổi học không có tài nguyên nào phù hợp |
| `locked_slot_invalid` | Lỗi | Tiết khoá nằm ngoài khung hoặc tràn sang ngày sau |
| `locked_resource_missing` | Lỗi | Tài nguyên đã khoá không còn tồn tại |
| `module_without_teacher` | Cảnh báo | Môn chưa có giáo viên đủ năng lực |

**Nguyên tắc thông báo [ĐỀ XUẤT]:** mọi thông báo phải (1) nêu đúng thực thể gây lỗi bằng mã và tên, (2) nêu con số cụ thể (cần bao nhiêu / có bao nhiêu), (3) gợi ý ít nhất một cách khắc phục. Toàn bộ thông báo bằng tiếng Việt có dấu.

---

## 9. Yêu cầu về đầu ra

Mẫu TKB thực tế của trường (tài liệu tham chiếu `img2.jpg` — *Thời khoá biểu nghề khối 11, TC khoá 43*) cho thấy cấu trúc bắt buộc của bản in:

- **Tiêu đề**: tên khối, khoá, số tuần và khoảng ngày cụ thể (*"TUẦN 03 TỪ 24/8/2026 ĐẾN 28/8/2026"*)
- **Trục dọc**: Thứ → Buổi (Sáng/Chiều) → Tiết (1–5)
- **Trục ngang**: mỗi cột là một lớp, tiêu đề gồm **tên nghề**, **mã lớp** và **sĩ số** (*"CNKT ĐIỀU KHIỂN TỰ ĐỘNG (11A3) 16"*)
- **Ô dữ liệu**: tên mô-đun, tên giáo viên (có thể nhiều người), và **mã phòng in dọc ở cột hẹp bên phải** (*A11-204*)
- Một mô-đun chiếm **nhiều tiết liền nhau** được gộp ô (tiết 1–2, tiết 3, …)

**FR-8.2** yêu cầu bản xuất PDF tái hiện đúng bố cục này. Đây là yêu cầu mang tính chấp nhận: cán bộ đào tạo cần bản in dán bảng tin giống hệt mẫu đang dùng.

---

## 10. Yêu cầu phi chức năng

| Mã | Yêu cầu | Chỉ tiêu |
|---|---|---|
| NFR-1 | Thời gian xếp lịch toàn trường | ≤ 10 phút; có phương án khả thi trong ≤ 2 phút |
| NFR-2 | Thời gian sửa cục bộ khi kéo thả | ≤ 5 giây |
| NFR-3 | Thời gian tiền kiểm tra | ≤ 3 giây |
| NFR-4 | Quy mô hỗ trợ | ≥ 200 giáo viên, ≥ 100 lớp, ≥ 150 phòng/thiết bị, ≥ 3000 buổi học |
| NFR-5 | Giao diện | Toàn bộ tiếng Việt có dấu; thuật ngữ đúng chuẩn giáo dục nghề nghiệp |
| NFR-6 | Cô lập dữ liệu giữa các đơn vị | Truy cập chéo tenant trả 404, không rò rỉ sự tồn tại |
| NFR-7 | Khả dụng | ≥ 99% trong kỳ xếp lịch đầu học kỳ |
| NFR-8 | Sao lưu | Hằng ngày, khôi phục được trong 4 giờ |
| NFR-9 | Trình duyệt | Chrome/Edge/Firefox hai phiên bản gần nhất |
| NFR-10 | Đáp ứng thiết bị | Máy tính là chính; cổng xem lịch của giáo viên/sinh viên phải dùng được trên điện thoại |
| NFR-11 | Bảo mật | JWT hạn 12 giờ; mật khẩu băm bằng hasher của Django; khoá ký phải đặt qua biến môi trường |
| NFR-12 | Khả năng lần vết | Mọi thao tác thay đổi lịch phải ghi lại người thực hiện và thời điểm |

**[THIẾU] Rủi ro bảo mật cần xử lý trước khi triển khai thật:**
- `JWT_SIGNING_KEY` mặc định là `"dev-insecure-signing-key-change-me"` — bắt buộc phải đặt lại.
- Đăng ký mở tự do, ai cũng tạo được tenant mới (FR-1.6).
- Không có phân quyền, mọi người dùng đều chạy được thao tác huỷ hoại (FR-1.3).

---

## 11. Lộ trình đề xuất

| Giai đoạn | Nội dung | Kết quả bàn giao |
|---|---|---|
| **GĐ 1 — Chặn** | G-1 (`Session`→`Schedule`), G-2 (sinh buổi học từ giờ chương trình), **G-11 + G-18 (lớp ↔ nhóm nghề, cả hai chiều)**, **G-14 (trần sĩ số theo loại buổi)**, **G-16 (ca học theo khối)**, G-7 (phân quyền), FR-1.4, FR-2.7 | Hệ thống dùng được cho dữ liệu thật của khối 9+ — khối lớn nhất và khó nhất |
| **GĐ 2 — Nghiệp vụ** | Khoa/Bộ môn/Ngành (G-4), cơ sở đào tạo (G-5), **G-15 (nhịp phát hành tuần)**, **G-12 (tuần thực tập)**, **G-19 (buổi bổ trợ)**, **G-20 (địa điểm ngoài trường)**, CRUD dữ liệu nền (FR-2.6), giao diện ràng buộc (FR-4.2) | Triển khai thí điểm toàn trường, cả ba luồng TKB |
| **GĐ 3 — Đặc thù** | Đồng giảng, lớp ghép, nhóm giáo viên (BR-1…BR-6), **G-13 (giờ chuẩn)** | Bao phủ các tình huống thực tế đã quan sát trong TKB |
| **GĐ 4 — Hoàn thiện** | Xuất bản (FR-8.3), PDF đúng mẫu (FR-8.2), cổng giáo viên/sinh viên (FR-8.4), kế thừa lịch cũ (FR-6.8), báo cáo (FR-9.3…9.5) | Vận hành chính thức |
| **GĐ 5 — Mở rộng** | Xếp lịch thi (Điều 12 quy chế: ≥2 tuần, ≤50 thí sinh/phòng, ≥2 giám thị, không ghép môn) | Bài toán xếp lịch thi — phạm vi riêng, cần đặc tả bổ sung |

---

## 12. Tiêu chí chấp nhận

Hệ thống được coi là đạt khi:

1. Nhập được toàn bộ dữ liệu thật của trường mà không phải sửa tay ngoài hệ thống.
2. Xếp được lịch toàn trường cho một học kỳ, **không còn xung đột cứng nào**.
3. **Xếp đúng khối 9+**: lớp văn hoá tách nhiều nhóm nghề không bao giờ bị trùng giờ với chính lớp gốc (BR-7) — kiểm chứng bằng dữ liệu thật của TC khoá 43.
4. **Tôn trọng trần sĩ số** theo loại buổi: lý thuyết ≤ 35, thực hành ≤ 18 (BR-9).
5. Mọi trường hợp bế tắc đều chỉ ra được thực thể cụ thể gây mâu thuẫn.
6. Cán bộ đào tạo tự tinh chỉnh được lịch bằng kéo thả mà không phá vỡ phần còn lại.
7. Bản in PDF đúng mẫu đang dùng của trường (§9).
8. Giáo viên xem được lịch cá nhân trên điện thoại.
9. Toàn bộ giao diện và thông báo bằng tiếng Việt có dấu, đúng thuật ngữ giáo dục nghề nghiệp.

**Phép thử nghiệm thu đề xuất:** nhập dữ liệu thật của **TC khoá 43 khối 11** (5 nghề, 11 lớp văn hoá, đã có bản TKB tuần 02 và 03 do trường phát hành), chạy bộ giải, rồi đối chiếu kết quả với bản trường đã xếp tay. Đây là phép thử tốt nhất vì có sẵn đáp án tham chiếu.

---

## Phụ lục A — Tài liệu tham chiếu

| Tài liệu | Nội dung khai thác |
|---|---|
| `HDSD_FTKB (1).pdf` | Luồng nghiệp vụ đầy đủ của phần mềm đối chiếu: nhập liệu → ràng buộc → xếp tự động → tinh chỉnh |
| `Các ràng buộc nên sử dụng_FTKB.pdf` | Bộ ràng buộc khuyến nghị (§7.4) |
| `Dạy chung lớp_FTKB.pdf` | Tình huống lớp ghép, tách nhóm, đồng giảng (§7.3) |
| `Một số tính năng khác biệt_FTKB.pdf` | Kế thừa lịch cũ, độ ưu tiên ràng buộc, 4 cách tinh chỉnh |
| `img1.jpg` | Lưới TKB lớp dạng cột-ngày |
| `img2.jpg` | **Mẫu TKB in thực tế của trường** — chuẩn đầu ra (§9) |
| Mã nguồn `evo-scheduler-service` | Hiện trạng kỹ thuật |

### Nguồn khảo sát về trường

| Tài liệu | Vai trò |
|---|---|
| Đề án tuyển sinh 2026 (QĐ 63/QĐ-CDT, 30/01/2026) | Định danh, chỉ tiêu, danh mục ngành nghề, thời gian đào tạo |
| **Quy chế tổ chức đào tạo TC–CĐ** (QĐ 245/QĐ-CDT, 06/6/2024) | Ràng buộc pháp lý nội bộ: khung giờ, lịch thi, điểm danh (§2.5) |
| **30 file TKB do trường công bố** (khảo sát toàn bộ) | Nguồn dữ liệu thật chính — xem chi tiết bên dưới |
| TKB nghề K43 tuần 01/02/03 + tuần 36 | **Lớp tách nhóm**, đồng giảng, sĩ số, mã phòng |
| TKB nghề K42 tuần 01/02/03 + tuần 45/46 | **Nhiều lớp gộp một nhóm**, ca nghề buổi chiều khối 12 |
| TKB cao đẳng K21/K22 (10 file) | Nhịp phát hành tuần, tuần thực tập trọn gói, mã `DN` |
| TKB văn hoá khối 10 (2), khối 11 (3), khối 12 (5) | Ca học theo khối, phòng cố định, môn bổ trợ khối 12 |
| TT 01/2024, TT 07/2017 /TT-BLĐTBXH | Tỉ lệ LT/TH, giờ chuẩn, định mức, trần sĩ số |
| Luật GDNN 124/2025/QH15 | Hiệu lực 01/01/2026 |

> Các file TKB gốc do trường công bố tại `cuwc.edu.vn` (mục *Khối cao đẳng*, *Khối trung cấp*, *Khối văn hoá*). Bản trích văn bản dùng cho khảo sát này được lưu kèm trong thư mục làm việc.
