# Báo Cáo Hoàn Thành — Phase 6: API Layer

Tài liệu này tổng hợp chi tiết kết quả thiết kế, cài đặt cổng kết nối dịch vụ API và cơ chế truyền nhận dữ liệu thời gian thực SSE (**Phase 6: API Layer**) cho PetBot AI Chatbot.

---

## 🏗️ 1. Cấu Trúc API & Định Tuyến V1
Xây dựng máy chủ FastAPI hiệu năng cao, tổ chức các router phân tách mạch lạc tại `interface/api/v1/endpoints/`:
- **`GET /api/v1/health`**: Cung cấp API giám sát trạng thái hệ thống, trả về `{"status": "healthy"}` khi tất cả các kết nối DB và Qdrant hoạt động bình thường.
- **`GET /api/v1/sessions`**: Liệt kê danh sách các phiên chat mà người dùng đã tạo trong quá khứ sắp xếp theo thời gian hoạt động gần nhất.
- **`GET /api/v1/sessions/{id}/history`**: Trích xuất chi tiết lịch sử tin nhắn của một phiên chat chỉ định kèm phân trang dữ liệu theo con trỏ thời gian (`before_timestamp`).
- **`DELETE /api/v1/sessions/{id}`**: Xóa vĩnh viễn một phiên chat và kích hoạt tự động xóa dây chuyền (Cascade Delete) toàn bộ các tin nhắn lịch sử thuộc phiên chat đó để dọn dẹp cơ sở dữ liệu.

---

## 🔒 2. JWT Authentication Middleware
- Triển khai `AuthMiddleware` kế thừa từ `BaseHTTPMiddleware`.
- Tự động đánh chặn tất cả các yêu cầu gửi đến cổng API, trích xuất mã JWT Token nằm ở Header `Authorization: Bearer <token>`.
- Sử dụng thuật toán mã hóa `HS256` để giải mã và kiểm chứng tính hợp lệ của Token:
  - Nếu Token hợp lệ: Đọc thông tin định danh và gán thực thể `User.authenticated(user_id)` vào trạng thái yêu cầu (`request.state.user`).
  - Nếu Token bị hết hạn hoặc không đúng cấu trúc: Trả về lập tức mã lỗi `401 Unauthorized`.
  - Nếu không có Token: Mặc định gán thực thể `User.guest()` ẩn danh để cho phép trải nghiệm dùng thử nhanh.

---

## 🌊 3. Server-Sent Events (SSE) Streaming
Đối với cổng dịch vụ trò chuyện `/api/v1/chat`, ngoài cơ chế trả phản hồi JSON một lần truyền thống, hệ thống hỗ trợ tối đa cơ chế truyền dẫn **SSE (Server-Sent Events)** thời gian thực khi cấu hình cờ `stream: true`:
- Đồng bộ hóa trực tiếp với trình sinh bất đồng bộ `astream` của LangGraph.
- Liên tục đẩy các gói tin dạng text/event-stream mã hóa UTF-8 thẳng về phía giao diện người dùng ngay khi Agent chuyển đổi các node lập luận:
  1. `thinking`: Hiển thị trạng thái Agent đang suy nghĩ suy luận trên giao diện.
  2. `tool_call`: Báo hiệu Agent đang thực hiện truy vấn cơ sở dữ liệu hoặc tìm kiếm web.
  3. `tool_result`: Trả thông tin rút gọn về kết quả tra cứu của công cụ.
  4. `answer`: Truyền phát từng từ (word-by-word streaming) của câu trả lời cuối cùng từ LLM.
  5. `done`: Kết thúc phiên truyền stream, đính kèm đầy đủ ID phiên chat phục vụ lưu trữ phía client.
- Tự động cấu hình `ensure_ascii=False` trong trình mã hóa JSON để giữ trọn vẹn hiển thị tiếng Việt có dấu mà không bị biến đổi thành các ký tự unicode khó đọc.

---

## 🔌 4. Dependency Injection System
- Quản lý và cung cấp toàn bộ các Repository, Use Cases và đồ thị Agent LangGraph thông qua cơ chế Dependency Injection mạnh mẽ của FastAPI (`Depends`).
- Giúp dễ dàng cấu hình hoán đổi (override) các dependency này trong môi trường kiểm thử tự động mà không cần can thiệp hay sửa đổi trực tiếp vào code lõi xử lý endpoint.
