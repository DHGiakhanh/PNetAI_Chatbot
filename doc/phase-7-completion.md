# Báo Cáo Hoàn Thành — Phase 7: Testing & Hardening

Tài liệu này tổng hợp chi tiết kết quả thiết kế, bộ kiểm thử tích hợp thực tế, giải pháp giới hạn tần suất yêu cầu và cấu hình đóng gói tối ưu (**Phase 7: Testing & Hardening**) cho PetBot AI Chatbot.

---

## 🧪 1. Hệ Thống Kiểm Thử Toàn Diện (118 Tests Passed)
Chúng tôi triển khai song song hai mô hình kiểm thử tự động để bảo đảm mã nguồn luôn vận hành chính xác:
- **Unit Tests (115 Tests)**:
  - Phủ rộng toàn bộ Domain entities, Value Objects, Use Cases ứng dụng, LLM adapters (giả lập HTTP calls) và bộ lọc bảo mật cơ sở dữ liệu `MongoQueryValidator`.
- **Integration Tests (3 Tests)**:
  - Khởi dựng môi trường kiểm thử tích hợp thực tế kết nối trực tiếp đến MongoDB cục bộ thông qua Database Fixture cách ly thông minh (`pnetai_chat_test`):
    - `test_session_persistence.py`: Kiểm tra toàn diện chuỗi tích hợp database từ lúc khởi tạo session, ghi lịch sử, tăng đếm tin nhắn, AI tóm tắt cho tới khi xóa cascade sạch sẽ dữ liệu.
    - `test_chat_flow.py`: Kiểm thử tích hợp toàn bộ luồng gọi REST API (cả JSON và SSE Stream) đi từ HTTP Request qua Middleware, xác thực, điều phối Agent gọi thực thi các tool và lưu trữ thành công lịch sử vào database thực tế.

---

## 🛡️ 2. Rate Limiting Middleware (ASGI Middleware)
Nhằm triệt tiêu nguy cơ máy chủ bị tấn công từ chối dịch vụ (DDoS) hoặc spam tiêu thụ tài nguyên API LLM đắt đỏ, chúng tôi tự phát triển một Middleware giới hạn tần suất yêu cầu gọn nhẹ trực tiếp bằng ASGI mà không sử dụng các thư viện ngoài cồng kềnh:
- **Thuật toán**: Sử dụng cấu trúc dữ liệu lưu trữ in-memory dựa trên thuật toán **Token Bucket** (xác định định danh thông qua IP khách vãng lai hoặc ID của thành viên đăng nhập).
- **Phân tách giới hạn linh hoạt qua biến môi trường (.env)**:
  - **Guest (Khách ẩn danh)**: Ngưỡng mặc định đề xuất là **30 requests/phút**.
  - **Member (Thành viên xác thực)**: Ngưỡng mặc định đề xuất là **100 requests/phút**.
- **HTTP Header tiêu chuẩn**: Khi vượt quá ngưỡng cho phép, hệ thống chặn đứng yêu cầu và trả về mã lỗi `429 Too Many Requests` đi kèm các trường header quy chuẩn gồm `Retry-After` (thời gian chờ thử lại), `X-RateLimit-Limit` (giới hạn tối đa) và `X-RateLimit-Remaining` (lượt yêu cầu còn lại).

---

## 📊 3. Structured Logging với `structlog`
Để dễ dàng đồng bộ hóa nhật ký hệ thống lên các nền tảng giám sát tập trung như ELK Stack, Datadog hay Loki, chúng tôi đã cấu hình tập trung hóa logging sử dụng `structlog`:
- **Production Mode (JSON)**: In toàn bộ log dưới dạng JSON một dòng phẳng (single-line JSON) đính kèm các metadata quan trọng như `request_id` (mã định danh yêu cầu), `session_id`, `user_id`, `latency_ms` (thời gian phản hồi) và tên tool thực thi.
- **Development Mode (Console)**: Định dạng log console sắc nét, màu sắc trực quan giúp nhà phát triển dễ dàng theo dõi.
- Loại bỏ hoàn toàn các log dư thừa từ các thư viện bên thứ ba (Uvicorn, HTTPX) để giữ cho log ghi nhận luôn tập trung vào tiến trình nghiệp vụ cốt lõi.

---

## 🐳 4. Đóng Gói Phân Phối Tối Ưu (Dockerfile & Compose Production)
- **`Dockerfile`**: 
  - Áp dụng kỹ thuật đóng gói Multi-stage build kết hợp với trình quản lý dependency siêu tốc **`uv`** của Astral giúp tối ưu hóa thời gian build và giảm dung lượng image đáng kể.
  - Sử dụng base image siêu nhẹ `python:3.11-slim` và tự động kích hoạt tính năng nén mã bytecode (`UV_COMPILE_BYTECODE=1`).
  - **Hardened Security**: Tạo và cấu hình chạy container hoàn toàn dưới quyền của user hệ thống không đặc quyền (`appuser`) nhằm triệt tiêu các lỗ hổng leo thang đặc quyền root.
  - Tích hợp sẵn cơ chế tự giám sát sức khỏe container thông qua cổng `/api/v1/health`.
- **`docker-compose.prod.yml`**:
  - Cấu hình môi trường Production hoàn chỉnh, thiết lập giới hạn cứng dung lượng bộ nhớ RAM và CPU (ví dụ: RAM 1024M cho DB, 1536M cho App) ngăn ngừa sự cố rò rỉ bộ nhớ gây sập hệ điều hành.
  - Đồng bộ độc lập các volume dữ liệu quan trọng cho MongoDB và Qdrant để bảo toàn dữ liệu.
  - Sử dụng Healthcheck để đồng bộ thứ tự khởi động dịch vụ (chỉ chạy App khi các database đã hoàn toàn sẵn sàng nhận kết nối).
