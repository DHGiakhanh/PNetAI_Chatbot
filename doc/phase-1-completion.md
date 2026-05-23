# Báo Cáo Hoàn Thành — Phase 1: Foundation

Tài liệu này tổng hợp chi tiết kết quả thiết kế, cấu trúc thư mục, thiết lập cấu hình và cơ sở hạ tầng khởi tạo (**Phase 1: Foundation**) cho PetBot AI Chatbot theo đúng tiêu chuẩn thiết kế trong dự án.

---

## 🏗️ 1. Cấu Trúc Thư Mục Clean Architecture
Hệ thống được tổ chức chặt chẽ theo nguyên lý **Clean Architecture**, phân chia rõ ràng trách nhiệm giữa các Layer nhằm tối ưu hóa tính độc lập, khả năng kiểm thử và mở rộng:

```
src/pnetai_chatbot/
├── domain/                  # Lõi nghiệp vụ (Entities, Value Objects, Enums)
├── application/             # Quy trình nghiệp vụ chính (Use Cases, Ports/Interfaces)
├── infrastructure/          # Chi tiết kỹ thuật (Database clients, LLM Adapters, Config)
└── interface/               # Cổng giao tiếp ngoại vi (API controllers, Middlewares)
```

---

## ⚙️ 2. Hệ Thống Cấu Hình `Settings`
- Triển khai lớp `Settings` kế thừa từ `BaseSettings` của thư viện `pydantic-settings`.
- Tự động tải các biến môi trường trực tiếp từ file `.env` và hỗ trợ kiểm tra kiểu dữ liệu tĩnh nghiêm ngặt.
- Cấu hình phân tách rõ ràng các tham số môi trường của:
  - Cổng chạy ứng dụng (`APP_HOST`, `APP_PORT`, `APP_ENV`).
  - Cấu hình API Keys của các mô hình LLM (OpenAI, Anthropic, Gemini) và Tavily.
  - Tham số kết nối MongoDB (Chat DB & Website DB) và Qdrant Vector DB.
  - Các hằng số điều khiển nghiệp vụ (ngưỡng rate limit, chu kỳ tự động tóm tắt).

---

## 🐳 3. Cơ Sở Hạ Tầng Docker Compose
Thiết lập file `docker-compose.yml` để khởi chạy nhanh chóng môi trường phát triển cục bộ:
- **MongoDB (chat_db)**: Khởi chạy Mongo 7.0 làm cơ sở dữ liệu lưu trữ phiên chat và lịch sử hội thoại. Tích hợp sẵn cơ chế kiểm tra trạng thái sức khỏe (`healthcheck`).
- **Qdrant (vector_db)**: Khởi chạy Qdrant engine để làm Vector Database lưu trữ tri thức chăm sóc thú cưng phục vụ RAG.
- Dữ liệu được đồng bộ hóa ra ngoài máy vật lý thông qua các volume độc lập để tránh mất mát dữ liệu khi container bị dừng.

---

## 🗄️ 4. Domain Entities & Database Ports
- **Domain Entities**:
  - `User`: Phân tách giữa Guest (người dùng vãng lai ẩn danh) và Member (người dùng đã đăng nhập hệ thống).
  - `ChatSession`: Quản lý trạng thái phiên chat, số lượng tin nhắn, và nội dung tóm tắt hội thoại bằng AI.
  - `Message`: Lưu trữ chi tiết nội dung tin nhắn, vai trò gửi (User, Assistant, System, Tool), metadata thẻ và token tiêu thụ.
- **Ports / Interfaces**:
  - Khai báo hoàn chỉnh các interface trừu tượng như `ISessionRepository`, `IHistoryRepository`, `ILLMAdapter` và `IVectorStorePort` tại Application Layer làm hợp đồng giao tiếp cho Infrastructure Layer.

---

## 📈 5. MongoDB Indexes & Qdrant Seeding
- **MongoDB Indexes**:
  - Đăng ký chỉ mục hỗn hợp `(session_id, timestamp)` trên chat messages collection để tối ưu hóa tốc độ truy vấn lịch sử hội thoại theo thứ tự thời gian.
  - Đăng ký chỉ mục `user_id` trên chat sessions collection để truy vấn nhanh danh sách phiên hội thoại của người dùng.
- **Qdrant Seeding Script**:
  - Xây dựng file `seed_data.py` để trích xuất dữ liệu cẩm nang tri thức thú cưng (dinh dưỡng, sức khỏe, hành vi), tự động chuyển đổi thành vector embedding độ chiều 1536 và nạp vào Qdrant collection phục vụ tìm kiếm ngữ nghĩa.
