
# DOI Checker — Hệ thống Xác thực Tài liệu Tham khảo

## 📖 Tổng quan dự án
**DOI Checker** là một luồng xử lý (pipeline) tự động được thiết kế để trích xuất, cấu trúc hóa và xác thực các tài liệu tham khảo học thuật từ các tệp tài liệu (PDF, DOCX hoặc ảnh quét). Bằng cách chuyển đổi văn bản thô thành các mô hình dữ liệu JSON chuẩn và đối soát với **Crossref API**, hệ thống đóng vai trò như một công cụ phân tích trích dẫn tin cậy. Hệ thống có khả năng nhận diện thông minh các định dạng trích dẫn (như PLOS, IEEE, APA), loại bỏ "rác" văn bản và tối ưu hóa giới hạn gọi API bằng cách lọc bỏ các tài nguyên web không cần thiết.

---

## 🏗️ Kiến trúc Hệ thống & Luồng công việc

Hệ thống được chia thành hai luồng xử lý chính: **Trích xuất Tài liệu tham khảo** và **Xác thực & Làm giàu dữ liệu qua API**.

### 1. Luồng Trích xuất Tài liệu tham khảo (`preprocessing.py` & `masking.py`)
Giai đoạn này tập trung vào việc phân tích tệp thô và trích xuất trích dẫn một cách thông minh.
- **Nạp tài liệu (Document Ingestion):** Chuyển đổi layout PDF sang định dạng Markdown bằng `pymupdf4llm` và cô lập phần "References".
- **Nhận diện định dạng (Format Detection):** Phân tích khối văn bản để xác định kiểu trích dẫn (đánh số trong ngoặc, số in đậm, v.v.).
- **Phân đoạn trích dẫn (Reference Segmentation):** Chia khối văn bản thành một mảng các chuỗi trích dẫn riêng lẻ, làm sạch các tiền tố số và dấu đầu dòng.
- **Vòng lặp Masking & Trích xuất dữ liệu:** Mỗi chuỗi sẽ đi qua một vòng lặp Regex nâng cao để đổ dữ liệu vào mô hình cấu trúc:
    - **Loại bỏ nhiễu (Noise Removal):** Làm sạch ngày truy cập, số tạp chí thừa và các URL không liên quan.
    - **Trích xuất thực thể (Entity Extraction):** Phân tách Năm, DOI, Tác giả và Tiêu đề. Có logic thông minh để tránh nhầm lẫn tên hội nghị/tạp chí thành tiêu đề bài báo.
    - **Định danh Website:** Kiểm tra xem trích dẫn có thuộc danh sách các tên miền học thuật hay không để gắn cờ các tài nguyên web thông thường.

```mermaid
flowchart TD
    A[Tài liệu PDF] --> B[Trích xuất Markdown bằng pymupdf4llm]
    B --> C{Tìm phần 'References'}
    C -- Không thấy --> D[Trả về danh sách rỗng]
    C -- Tìm thấy --> E[Cô lập khối trích dẫn]
    E --> F[Nhận diện định dạng trích dẫn]
    F --> G[Tách thành các trích dẫn đơn lẻ]
    G --> H[Làm sạch & Loại bỏ chỉ số]
    H --> I[Vòng lặp Masking]
    
    subgraph Quy trình Masking cấu trúc
        I --> J[Tiền xử lý & Loại bỏ nhiễu]
        J --> K[Trích xuất Năm]
        K --> L[Trích xuất DOI]
        L --> M[Trích xuất Tiêu đề & Tác giả]
        M --> N{Có phải Website?}
        N -- Có --> O[Gán is_web = True]
        N -- Không --> P[Gán is_web = False]
    end
    
    O --> Q[Khởi tạo JSON trích dẫn]
    P --> Q
```

### 2. Luồng Xác thực & Làm giàu dữ liệu API (`doi_validator.py` & `tasks.py`)
Đóng vai trò là công cụ "làm giàu" thông tin, tương tác với API Crossref để xác minh DOI hiện có hoặc tìm kiếm các DOI còn thiếu.
- **Bộ điều hướng xác thực (Validation Router):**
    - **Kiểm tra DOI trực tiếp:** Nếu đã trích xuất được DOI, hệ thống sẽ gửi yêu cầu GET để kiểm tra, đánh dấu là `"valid_doi"`, `"invalid_doi"`, hoặc `"unverified"`.
    - **Bộ lọc tài nguyên Web:** Nếu là web và không có DOI, hệ thống sẽ bỏ qua bước check API để tiết kiệm quota, đánh dấu là `"web_resource"`.
    - **Tìm kiếm sâu bằng Metadata:** Với các trích dẫn học thuật thiếu DOI, hệ thống xây dựng câu truy vấn tìm kiếm dựa trên tiêu đề. Nếu năm xuất bản từ Crossref khớp với năm trích xuất được, hệ thống sẽ lấy DOI đó và đánh dấu `"found_doi"`.
- **Tổng hợp kết quả:** Tập hợp tất cả các thông tin tìm được, cập nhật số liệu thống kê và xuất mô hình JSON hoàn chỉnh.

```mermaid
flowchart TD
    A[JSON trích dẫn đã phân tách] --> B[Khởi tạo bộ đếm tổng hợp]
    B --> C[Duyệt qua từng trích dẫn]
    
    C --> F{Có DOI không?}
    F -- Có --> G["Crossref API: /works/{doi}"]
    G -- 200 OK --> H[Đánh dấu 'valid_doi']
    G -- 404/Timeout --> I[Đánh dấu 'invalid_doi' / 'unverified']
    
    F -- Không --> D{Là tài nguyên Web?}
    D -- Có --> E[Đánh dấu 'web_resource']
    
    D -- Không --> K{Có Tiêu đề khả dụng?}
    K -- Không --> L[Đánh dấu 'no_doi']
    K -- Có --> M[Crossref API: Search query]
    
    M --> N{Tìm thấy kết quả & Khớp năm?}
    N -- Có --> O[Đánh dấu 'found_doi' & Gán DOI mới]
    N -- Không --> P[Đánh dấu 'no_doi']
    
    E --> Q[Cập nhật trạng thái tổng hợp]
    H --> Q
    I --> Q
    L --> Q
    O --> Q
    P --> Q
    
    Q --> R{Còn trích dẫn không?}
    R -- Còn --> C
    R -- Hết --> S[Xuất kết quả ra file JSON]
```

---

## 📂 Cấu trúc Thư mục

```text
doi_checker/
├── frontend/                  # Ứng dụng React Single-Page
│   ├── src/
│   │   ├── components/        # UI dùng chung
│   │   ├── pages/             # Các trang chính
│   │   ├── hooks/             # Custom hooks quản lý state
│   │   └── utils/             # Axios API clients
│   └── package.json
│
└── backend/                   # Backend Python FastAPI
    ├── core/                  # Logic xử lý chính
    │   ├── preprocessing.py   # PDF I/O, nhận diện định dạng
    │   ├── masking.py         # Nhân của Masking: Regex, trích xuất dữ liệu
    │   └── doi_validator.py   # Xác thực API Crossref
    ├── api/                   # Web routes và schemas
    │   └── routes.py          # Các Endpoint API
    ├── ocr/                   # Module/Thư mục xử lý ảnh quét (Image Picture OCR)
    ├── temporary/             # Thư mục tạm xử lý file
    ├── result/                # Thư mục chứa kết quả JSON
    └── tasks.py               # Điều phối pipeline chính
```

---

## 📊 Trạng thái Dự án & Lộ trình (Roadmap)

**Đã hoàn thành:**
- [x] Tái cấu trúc pipeline cốt lõi, tách biệt `preprocessing.py` và `masking.py`.
- [x] Tích hợp xác thực API Crossref và luồng suy luận DOI thông minh.
- [x] Khắc phục các lỗi lớn về trích xuất tiêu đề.
- [x] Xử lý các trường hợp thiếu năm và cách phân tách tác giả trên PLOS.
- [x] Triển khai bộ lọc tài nguyên web thông minh.

**Việc cần làm / Lộ trình sắp tới:**
- [ ] **Kết nối Full-stack:** Hoàn thiện website và FastAPI.
- [ ] **Dockerization:** Đóng gói ứng dụng vào Docker containers.
- [ ] **Nâng cấp OCR:** Hỗ trợ tốt hơn cho PDF dạng ảnh quét bằng Tesseract / LayoutLM.
- [ ] **Xử lý hàng loạt (Batch Processing):** Tải lên nhiều tài liệu cùng lúc.
- [ ] **Tích hợp Database:** Lưu lịch sử xử lý vào SQLite / MongoDB.
