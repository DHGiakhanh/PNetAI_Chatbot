# 🐾 PetBot — AI Chatbot Server for Pet Social Network

> **Phiên bản:** 0.1.0  
> **Kiến trúc:** Clean Architecture (Domain-Driven Design)  
> **Công nghệ lõi:** Python 3.11+ · FastAPI · LangGraph · MongoDB · Qdrant · Tavily · `uv`  
> **Mục tiêu:** Hệ thống Chatbot AI có khả năng lập luận đa bước (Multi-step Reasoning) và tổng hợp tri thức đa nguồn phục vụ Mạng xã hội Thú cưng.

---

## 📖 1. Tổng Quan Hệ Thống

**PetBot** là máy chủ dịch vụ Chatbot AI thông minh, hỗ trợ người dùng tra cứu thông tin sản phẩm, sức khỏe và đời sống thú cưng theo thời gian thực. Bằng việc áp dụng mô hình **RAG (Retrieval-Augmented Generation) đa nguồn**, hệ thống tự động tổng hợp thông tin từ 3 kênh tri thức đáng tin cậy:

| Kênh tri thức | Công nghệ tích hợp | Mục đích sử dụng |
|---|---|---|
| **Internet** (Thời gian thực) | **Tavily Search API** | Cập nhật tin tức, sản phẩm mới, xu hướng chăm sóc thú cưng hiện hành. |
| **Cơ sở tri thức nội bộ** | **Qdrant Vector DB** | Truy xuất chính xác các bài viết học thuật, cẩm nang chăm sóc và câu hỏi thường gặp (FAQs). |
| **Cơ sở dữ liệu Website** | **MongoDB (website_db)** | Tra cứu thực tế thông tin sản phẩm, thú cưng, dịch vụ và trạng thái đơn hàng của người dùng. |

---

## ✨ 2. Tính Năng Nổi Bật

* **Đồ thị Lập luận LangGraph**: Trái tim của chatbot là một bộ điều phối Agent tuần hoàn, cho phép phân tích câu hỏi để tự động quyết định gọi công cụ (tool) phù hợp, chạy song song các tool độc lập (`asyncio.gather`) và lập luận câu trả lời chính xác.
* **LLM Adapter linh hoạt**: Thiết kế theo *Adapter Pattern* kết hợp *Registry Pattern* (`LLMFactory`), cho phép cấu hình hoán đổi linh hoạt giữa các nhà cung cấp mô hình lớn như **OpenAI**, **Anthropic**, **Gemini** và **Ollama** (chạy local offline) chỉ bằng cách sửa đổi biến môi trường mà không cần sửa đổi mã nguồn.
* **Quản lý Phiên chat & Lịch sử**: Lưu trữ bất đồng bộ an toàn qua `motor` (MongoDB driver). Hỗ trợ chế độ ẩn danh không ghi dữ liệu cho khách vãng lai (`Guest`) và lưu trữ bảo mật trọn vẹn lịch sử có phân quyền sở hữu cho thành viên (`Member`).
* **AI Auto-Summarization**: Tự động phát động tiến trình ngầm (`FastAPI.BackgroundTasks`) nén lịch sử cuộc trò chuyện khi số lượng tin nhắn đạt bội số của 10 để bảo vệ bộ nhớ ngữ cảnh của LLM.
* **Cơ chế Bảo mật nghiêm ngặt**:
  * `MongoQueryValidator`: Whitelist các collection được truy cập, chặn đứng tất cả toán tử ghi/xóa độc hại và giới hạn cứng số lượng bản ghi tối đa 50 dòng để ngăn ngừa chèn câu lệnh truy vấn (Query Injection).
  * **JWT Auth Gate**: Chèn ép cứng bộ lọc `user_id` từ JWT Token của người dùng khi truy cập lịch sử mua hàng, chặn đứng hoàn toàn lỗi phân quyền ngang (IDOR).
* **ASGI Rate Limiting Middleware**: Tự phát triển Middleware giới hạn tần suất yêu cầu bằng thuật toán **Token Bucket** (IP khách vãng lai tối đa 30 requests/phút, thành viên đăng nhập tối đa 100 requests/phút).
* **Structured JSON Logging**: Cấu hình `structlog` tự động xuất JSON log một dòng phẳng chuyên nghiệp ở Production và định dạng Console tô màu trực quan ở Development.
* **Đóng gói tối ưu**: Dockerfile multi-stage siêu nhẹ chạy dưới user hệ thống không có đặc quyền (`appuser`) kết hợp cùng Docker Compose giới hạn cứng RAM/CPU tránh rò rỉ bộ nhớ.

---

## 📂 3. Cấu Trúc Thư Mục Dự Án

Mã nguồn được tổ chức theo tiêu chuẩn **Clean Architecture** nghiêm ngặt để đảm bảo khả năng kiểm thử độc lập:

```
src/pnetai_chatbot/
├── domain/                  # Layer 1: Lõi nghiệp vụ (Entities, Value Objects, Enums, Exceptions)
├── application/             # Layer 2: Quy trình ứng dụng (Use Cases, Ports/Interfaces, DTOs)
├── infrastructure/          # Layer 3: Hạ tầng kỹ thuật (LLM Adapters, Tools, Persistence Repos, Agent Graph)
└── interface/               # Layer 4: Cổng giao tiếp ngoài (FastAPI routers, Middlewares, Schemas)
```

---

## 🚀 4. Hướng Dẫn Khởi Động Nhanh

### Yêu Cầu Hệ Thống
* Python 3.11+
* [uv](https://docs.astral.sh/uv/) (Trình quản lý gói siêu tốc)
* Docker & Docker Compose

### Bước 1: Thiết lập môi trường
```bash
# 1. Cài đặt các thư viện phụ thuộc đồng bộ
uv sync

# 2. Tạo file cấu hình môi trường từ mẫu
cp .env.example .env

# 3. Mở file .env và điền đầy đủ các thông tin API Keys (OPENAI_API_KEY, TAVILY_API_KEY, v.v.)
```

### Bước 2: Khởi động cơ sở hạ tầng cơ sở dữ liệu
```bash
docker compose up -d
```
Lệnh này sẽ khởi chạy môi trường local bao gồm:
* **MongoDB** (cổng `27017`) — Lưu trữ phiên và tin nhắn lịch sử.
* **Qdrant** (cổng `6333` & `6334`) — Công cụ tìm kiếm vector.

### Bước 3: Nạp dữ liệu tri thức mẫu (Seed Qdrant)
```bash
uv run python src/pnetai_chatbot/infrastructure/config/seed_data.py
```
Kịch bản sẽ tự động tạo bộ vector tri thức cẩm nang chăm sóc thú cưng mẫu và chèn vào bộ nhớ Qdrant Vector Store.

### Bước 4: Khởi chạy máy chủ API phát triển
```bash
make run
# Hoặc: uv run uvicorn pnetai_chatbot.main:app --host 0.0.0.0 --port 8000 --reload
```
Máy chủ dịch vụ sẽ vận hành tại địa chỉ: **http://localhost:8000**  
Bạn có thể truy cập tài liệu API trực quan tại: **http://localhost:8000/docs**

---

## 🧪 5. Kiểm Thử & Định Dạng Code

Dự án áp dụng tiêu chuẩn mã nguồn cực kỳ nghiêm ngặt nhằm tránh lỗi cú pháp và đảm bảo tính đồng bộ:

```bash
# 1. Tự động kiểm tra và sửa định dạng code bằng Ruff
uv run ruff format src/ tests/
uv run ruff check src/ tests/ --fix

# 2. Chạy toàn bộ suite kiểm thử (118 bài test tự động gồm Unit & Integration)
uv run pytest
```

---

## 🐳 6. Triển Khai Trên Môi Trường Production

Khi đưa hệ thống lên môi trường thực tế, sử dụng cấu hình Production tối ưu và gia cố bảo mật:

```bash
# Khởi chạy Stack Production bao gồm ứng dụng, MongoDB và Qdrant có giới hạn tài nguyên
docker compose -f docker-compose.prod.yml up -d --build
```
Cấu hình Production cam kết:
* Ứng dụng chạy dưới dạng non-root bảo mật cao.
* Tự động khởi động lại container nếu có sự cố (`unless-stopped`).
* Giới hạn RAM cứng cho từng service (MongoDB 1024M, Qdrant 1024M, API App 1536M).
* Chỉ khởi động máy chủ API sau khi MongoDB và Qdrant đã vượt qua Healthcheck thành công.

---

## 📚 7. Nhật Ký Nghiệm Thu Từng Phase

Chi tiết báo cáo nghiệm thu kỹ thuật và thiết kế của từng giai đoạn phát triển dự án được lưu trữ trực tiếp trong thư mục [doc/](file:///Users/anhnn/Documents/lectures/mentor-fptu/support/sem-09/capstone-QN-pet-chatbot/PNetAI_Chatbot/doc):

* 🔗 **Phase 1**: [Tài liệu Nghiệm thu Nền tảng Cơ sở](file:///Users/anhnn/Documents/lectures/mentor-fptu/support/sem-09/capstone-QN-pet-chatbot/PNetAI_Chatbot/doc/phase-1-completion.md)
* 🔗 **Phase 2**: [Tài liệu Nghiệm thu LLM Adapter](file:///Users/anhnn/Documents/lectures/mentor-fptu/support/sem-09/capstone-QN-pet-chatbot/PNetAI_Chatbot/doc/phase-2-completion.md)
* 🔗 **Phase 3**: [Tài liệu Nghiệm thu Công cụ (Tools)](file:///Users/anhnn/Documents/lectures/mentor-fptu/support/sem-09/capstone-QN-pet-chatbot/PNetAI_Chatbot/doc/phase-3-completion.md)
* 🔗 **Phase 4**: [Tài liệu Nghiệm thu Agent Orchestrator](file:///Users/anhnn/Documents/lectures/mentor-fptu/support/sem-09/capstone-QN-pet-chatbot/PNetAI_Chatbot/doc/phase-4-completion.md)
* 🔗 **Phase 5**: [Tài liệu Nghiệm thu Lịch sử & Phiên Chat](file:///Users/anhnn/Documents/lectures/mentor-fptu/support/sem-09/capstone-QN-pet-chatbot/PNetAI_Chatbot/doc/phase-5-completion.md)
* 🔗 **Phase 6**: [Tài liệu Nghiệm thu API Layer](file:///Users/anhnn/Documents/lectures/mentor-fptu/support/sem-09/capstone-QN-pet-chatbot/PNetAI_Chatbot/doc/phase-6-completion.md)
* 🔗 **Phase 7**: [Tài liệu Nghiệm thu Kiểm Thử & Hardening](file:///Users/anhnn/Documents/lectures/mentor-fptu/support/sem-09/capstone-QN-pet-chatbot/PNetAI_Chatbot/doc/phase-7-completion.md)

---

## 📝 8. Bản Quyền & Giảng Viên Hướng Dẫn

* **Dự án tốt nghiệp**: Đại học FPT (FPT University Capstone Project).
* **Quyền sở hữu**: Bản quyền thuộc về Nhóm Nghiên Cứu và Đại học FPT.
* **Liên hệ phát triển**: [Huylao-gia](https://github.com/Huylao-gia) & Đội ngũ Phát triển PetBot.