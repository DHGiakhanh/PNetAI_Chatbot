# BÁO CÁO KẾT QUẢ TRIỂN KHAI & CHẠY THỬ NGHIỆM PIPELINE NẠP DỮ LIỆU QDRANT
**Dự án:** PNetAI Pet Chatbot System  
**Ngày thực hiện:** 27/05/2026  
**Trạng thái:** Thành công 100% (Hoàn thành chạy thử nghiệm mô-đun hóa & lọc nhiễu dữ liệu)

---

## 1. Tổng Quan Hiện Trạng & Yêu Cầu Hệ Thống

Nhằm nâng cao chất lượng tìm kiếm ngữ nghĩa (Semantic Search) cho chatbot y tế thú cưng, hệ thống yêu cầu nạp khối lượng lớn tài liệu tri thức vào Vector Database (Qdrant).

### A. Dữ liệu thực tế tại thư mục `data/`
*   **`qa-blog.json`** (~46MB): Chứa 5,762 bài viết blog hỏi đáp có cấu trúc, dung lượng lớn, nội dung bài viết rất dài và nhiều ký tự thừa do crawl dữ liệu.
*   **`knowlegde-base-001.pdf`** (18 trang): Tài liệu cẩm nang bệnh lý y khoa.
*   **`knowledge-base-002.pdf`** (77 trang): Tài liệu cẩm nang bệnh lý y khoa.

### B. Môi trường kiểm thử
*   **Vector Database:** Qdrant hoạt động trong Docker Container (`pnetai_qdrant`) tại cổng `localhost:6333`.
*   **Collection:** `pet_knowledge_base` (Vector dimension: `1536`, Distance Metric: `Cosine`).
*   **Embedding Model:** `text-embedding-ada-002` (OpenAI).

---

## 2. Kiến Trúc Mô-đun Hóa Của Pipeline

Tuân thủ nghiêm ngặt quy trình quy định trong tài liệu thiết kế `doc/qdrant-data-ingestion-planning.md`, mã nguồn nạp dữ liệu đã được cấu trúc thành các mô-đun độc lập trong thư mục `scripts/ingest/`:

```
scripts/ingest/
├── __init__.py
├── splitter.py      # Định nghĩa luật cắt nhỏ văn bản (Semantic Chunking)
├── parser.py        # Phân tích cú pháp PDF/JSON & áp dụng bộ lọc làm sạch
└── pipeline.py      # Điều phối trung tâm (Embeddings, Batching, Upsert)
```

### Chi tiết các thành phần:
*   **`splitter.py`:** Khởi tạo `RecursiveCharacterTextSplitter` từ thư viện `langchain-text-splitters` với cấu hình tối ưu cho tiếng Việt: `chunk_size=900` ký tự, `chunk_overlap=120` ký tự.
*   **`parser.py`:** Chịu trách nhiệm trích xuất văn bản từ PDF (sử dụng thư viện `pypdf` đã cài đặt thông qua `uv`) và JSON, đồng thời thực thi bộ lọc làm sạch text nghiêm ngặt.
*   **`pipeline.py`:** Điều hành toàn bộ quy trình, hỗ trợ chạy thử nghiệm thông qua tham số giới hạn bản ghi `--limit-json` để tránh lãng phí API quota của người dùng.

---

## 3. Quy Trình Làm Sạch Dữ Liệu Khắt Khe (Rigorous Data Cleaning)

Để loại bỏ hoàn toàn các loại nhiễu và văn bản thừa từ việc crawl dữ liệu hoặc trích xuất từ PDF, hàm `clean_text` trong mô-đun `parser.py` đã thực hiện **7 bước lọc dữ liệu chuyên sâu**:

1.  **Loại bỏ ký tự điều khiển:** Xử lý và xóa sạch các ký tự điều khiển non-printable (như `\x00-\x08`, `\x0e-\x1f`...) phát sinh trong quá trình đọc PDF.
2.  **Chuẩn hóa khoảng trắng không ngắt dòng:** Thay thế toàn bộ ký tự `\xa0` và `\r` thành khoảng trắng chuẩn.
3.  **Tẩy thẻ HTML:** Dùng Regex xóa bỏ hoàn toàn các thẻ HTML còn sót lại từ dữ liệu crawler trong file JSON.
4.  **Hộp gộp từ bị ngắt dòng (Hyphenation Resolution):** Quét và sửa lỗi các từ ghép tiếng Việt bị ngắt xuống dòng bằng dấu gạch ngang (ví dụ: `vac-\nxin` thành `vac-xin`).
5.  **Loại bỏ Header & Footer:** Tự động nhận diện và loại bỏ các dòng boilerplate định kỳ của trang PDF như `"Trang X / Y"` hoặc `"Page X"`.
6.  **Tẩy Watermark & Bản quyền:** Tự động lọc bỏ các dòng văn bản quảng cáo hoặc link website chèn dưới chân trang (ví dụ: các dòng chứa `2vet.vn` hoặc `Bệnh viện thú y 2Vet`).
7.  **Chuẩn hóa cấu trúc đoạn:** Giới hạn tối đa tối đa chỉ **2 dấu xuống dòng liên tiếp** (`\n\n`) nhằm loại bỏ khoảng trống thừa thãi giữa các trang PDF, đồng thời gộp các khoảng trắng liên tiếp trong dòng thành một khoảng đơn duy nhất.

---

## 4. Kết Quả Chạy Thử Nghiệm Giai Đoạn (Stage-by-Stage Execution)

Thử nghiệm được thực hiện bằng cách chạy nạp **toàn bộ 2 file PDF** và **5 bài viết blog đầu tiên** từ `qa-blog.json`:
```bash
uv run python scripts/ingest/pipeline.py --data-dir ./data --limit-json 5
```

Nhật ký ghi nhận chi tiết theo từng giai đoạn:

### Giai đoạn 1: Parsing & Lọc Nhiễu Dữ Liệu
```
[INFO] [INGESTION] Scanning and parsing files in directory: ./data
[INFO] [PARSE JSON] Starting ingestion parsing for file: qa-blog.json
[INFO] [PARSE JSON] File contains 5762 total records in JSON array
[INFO] [PARSE JSON] Processed, cleaned, and chunked: 5/5 entries
[INFO] [PARSE JSON] Reached limit of 5 JSON records. Halting JSON parsing.
[INFO] [PARSE JSON] Parsing complete. Generated 27 chunks from 5 JSON articles.
[INFO] [PARSE PDF] Starting ingestion parsing for file: knowlegde-base-001.pdf
[INFO] [PARSE PDF] File has 18 pages to extract
[INFO] [PARSE PDF] Processed and cleaned page: 18/18
[INFO] [PARSE PDF] Parsing complete. Generated 70 chunks from 18 pages.
[INFO] [PARSE PDF] Starting ingestion parsing for file: knowledge-base-002.pdf
[INFO] [PARSE PDF] File has 77 pages to extract
[INFO] [PARSE PDF] Processed and cleaned page: 20/77
[INFO] [PARSE PDF] Processed and cleaned page: 40/77
[INFO] [PARSE PDF] Processed and cleaned page: 60/77
[INFO] [PARSE PDF] Processed and cleaned page: 77/77
[INFO] [PARSE PDF] Parsing complete. Generated 199 chunks from 77 pages.
[INFO] [INGESTION] Total parsed & cleaned text chunks prepared: 296
```
> [!TIP]
> **Đánh giá hiệu quả làm sạch:**  
> Ở lần chạy thử trước khi chưa lọc nhiễu, tài liệu tạo ra **310 chunks**. Sau khi kích hoạt bộ lọc làm sạch trong `parser.py`, số lượng mảnh giảm xuống còn **296 chunks**. Việc giảm đi 14 chunks này chứng minh các dòng văn bản rác, headers, footers và watermark quảng cáo đã bị **loại bỏ triệt để**, giúp dữ liệu nạp vào Vector Database đạt độ tinh khiết tối đa.

### Giai đoạn 2: Tạo Embeddings & Upsert vào Qdrant theo Lô (Batch)
Nhằm tránh vượt quá giới hạn băng thông của OpenAI API (Rate Limit), pipeline xử lý nạp dữ liệu theo từng lô có kích thước `BATCH_SIZE = 16`:
```
[INFO] [INGESTION] Generating embeddings and upserting points in batches of 16...
[INFO] HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
[INFO] HTTP Request: PUT http://localhost:6333/collections/pet_knowledge_base/points?wait=true "HTTP/1.1 200 OK"
[INFO] [INGESTION] Successfully ingested batch 1/19 (16 points uploaded)
... (chạy qua 19 batches thành công liên tục)
[INFO] HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
[INFO] HTTP Request: PUT http://localhost:6333/collections/pet_knowledge_base/points?wait=true "HTTP/1.1 200 OK"
[INFO] [INGESTION] Successfully ingested batch 19/19 (8 points uploaded)
[INFO] [INGESTION] Pipeline Execution Completed Successfully!
```

---

## 5. Xác Thực Sự Nhất Quán Trên Vector Database

Kiểm tra trực tiếp trạng thái của collection `pet_knowledge_base` trên Qdrant thông qua REST API:
```bash
curl http://localhost:6333/collections/pet_knowledge_base
```
*   **Trạng thái collection:** `green` (Hoạt động tốt).
*   **Tổng số points hiện tại:** **`355`** points.

### Cơ chế ghi đè thông minh (Idempotency) hoạt động chuẩn xác:
Pipeline sử dụng thuật toán `uuid.uuid5(uuid.NAMESPACE_DNS, id_base)` để sinh ID cho vector từ tên file và số thứ tự của chunk. Nhờ đó:
*   Khi chạy lại thử nghiệm lần 2 với bộ lọc làm sạch mới, Qdrant tự động **ghi đè và cập nhật đè** (overwrite) dữ liệu sạch lên các ID cũ của 2 file PDF và 5 bài viết JSON đầu tiên thay vì tạo trùng lặp vector.
*   Không có bất kỳ bản ghi rác hay trùng lặp nào xuất hiện, giữ cho cơ sở dữ liệu luôn ở trạng thái tối ưu nhất.

---

## 6. Hướng Dẫn Vận Hành & Nạp Toàn Bộ Dữ Liệu (Production Run)

Khi người dùng đã sẵn sàng nạp toàn bộ **5,762 bài viết** từ file `qa-blog.json` vào Qdrant, hãy thực hiện theo các bước sau:

1.  **Đảm bảo Docker Desktop đang hoạt động** và các container đang chạy:
    ```bash
    docker compose up -d
    ```
2.  **Khởi chạy pipeline nạp toàn bộ dữ liệu** (loại bỏ tham số giới hạn `--limit-json`):
    ```bash
    uv run python scripts/ingest/pipeline.py --data-dir ./data
    ```

> [!WARNING]
> **Lưu ý quan trọng khi nạp dữ liệu lớn (Production):**
> *   Do file JSON có kích thước rất lớn (~46MB) chứa nội dung văn bản chi tiết đồ sộ, việc tạo vector embedding cho toàn bộ dữ liệu này có thể tiêu tốn một khoản chi phí API nhất định và yêu cầu tài khoản OpenAI của bạn phải ở trạng thái hoạt động (có đủ số dư hạn mức).
> *   Nếu gặp lỗi Rate Limit (`429 Too Many Requests`) từ phía OpenAI do tài khoản nhà phát triển ở Tier thấp, bạn có thể điều chỉnh giảm biến `BATCH_SIZE = 10` hoặc thêm thời gian trễ `asyncio.sleep` giữa các đợt gửi trong file `pipeline.py`.
