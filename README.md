# 🐾 PetBot — AI Chatbot Server for Pet Social Network

> **Phiên bản:** 0.2.0  
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
* **Dual-LLM Architecture**: Tách biệt hoàn toàn hai vai trò LLM trong pipeline:
  * **Reasoning LLM** (OpenAI, Gemini, Anthropic...): Chịu trách nhiệm phân tích ý định, lựa chọn tool, và sinh câu truy vấn MongoDB — các tác vụ đòi hỏi khả năng tuân theo JSON schema nghiêm ngặt.
  * **Response LLM** (Self-hosted / Finetune hoặc cloud): Chịu trách nhiệm sinh câu trả lời cuối cùng thân thiện cho người dùng — thích hợp để gắn mô hình finetune chuyên ngành thú cưng.
* **Self-Hosted Model Gateway**: Hỗ trợ tích hợp mô hình tự host tương thích OpenAI API (vLLM, LM Studio, LMDeploy, text-generation-webui) thông qua biến `RESPONSE_LLM_PROVIDER=selfhosted` — chuyển đổi tức thì, không cần sửa mã nguồn.
* **LLM Adapter linh hoạt**: Thiết kế theo *Adapter Pattern* kết hợp *Registry Pattern* (`LLMFactory`), hỗ trợ **OpenAI**, **Anthropic**, **Gemini**, **Ollama**, và **Self-Hosted** (OpenAI-compatible).
* **Quản lý Phiên chat & Lịch sử**: Lưu trữ bất đồng bộ an toàn qua `motor` (MongoDB driver). Hỗ trợ chế độ ẩn danh không ghi dữ liệu cho khách vãng lai (`Guest`) và lưu trữ bảo mật trọn vẹn lịch sử có phân quyền sở hữu cho thành viên (`Member`).
* **AI Auto-Summarization**: Tự động phát động tiến trình ngầm (`FastAPI.BackgroundTasks`) nén lịch sử cuộc trò chuyện khi số lượng tin nhắn đạt bội số của 10 để bảo vệ bộ nhớ ngữ cảnh của LLM.
* **Hội thoại theo Phiên ngắn hạn (Transient Session)**: Người dùng chat trong phiên hiện tại; khi tải lại trang hoặc đăng nhập lại, phiên mới được tạo. Lịch sử lưu ẩn phía server cho mục đích phân tích và cá nhân hóa, không hiển thị lại giao diện.
* **Truy vấn Ngôn ngữ tự nhiên → MongoDB**: Hệ thống tự động dịch câu hỏi Tiếng Việt sang truy vấn MongoDB với ánh xạ Enum chuẩn hóa (ví dụ: "chó" → `"Dog"`, "mèo" → `"Cat"`) và lọc cứng `user_id` từ JWT để chống IDOR.
* **Cơ chế Bảo mật nghiêm ngặt**:
  * `MongoQueryValidator`: Whitelist các collection được truy cập, chặn đứng tất cả toán tử ghi/xóa độc hại và giới hạn cứng số lượng bản ghi tối đa 50 dòng để ngăn ngừa chèn câu lệnh truy vấn (Query Injection).
  * **JWT Auth Gate**: Chèn ép cứng bộ lọc `user_id` từ JWT Token của người dùng khi truy cập lịch sử mua hàng, chặn đứng hoàn toàn lỗi phân quyền ngang (IDOR).
* **ASGI Rate Limiting Middleware**: Tự phát triển Middleware giới hạn tần suất yêu cầu bằng thuật toán **Token Bucket** (IP khách vãng lai tối đa 30 requests/phút, thành viên đăng nhập tối đa 100 requests/phút).
* **Structured JSON Logging**: Cấu hình `structlog` tự động xuất JSON log một dòng phẳng chuyên nghiệp ở Production và định dạng Console tô màu trực quan ở Development.
* **Đóng gói tối ưu**: Dockerfile multi-stage siêu nhẹ chạy dưới user hệ thống không có đặc quyền (`appuser`) kết hợp cùng Docker Compose giới hạn cứng RAM/CPU tránh rò rỉ bộ nhớ.

---

## 🏗️ 3. Kiến Trúc Pipeline Agent

```
Câu hỏi người dùng
       │
       ▼
 ┌─────────────────┐
 │ intent_analyzer │  ← Reasoning LLM (OpenAI / Gemini / Anthropic)
 │  Phân tích ý    │    Phân tích intent, chọn tool phù hợp
 │  định & tool    │
 └────────┬────────┘
          │ Có tool?
     ┌────┴─────┐
  Có │          │ Không
     ▼          ▼
 ┌───────────┐  ┌────────────────┐
 │tool_exec  │  │ context_merger │
 │MongoDB /  │  │ Gộp kết quả    │
 │Vector /   │→ │ từ các tool    │
 │Web Search │  └───────┬────────┘
 └───────────┘          │
                        ▼
               ┌─────────────────┐
               │response_generator│  ← Response LLM (Self-hosted / Cloud)
               │ Sinh câu trả    │    Tổng hợp context → câu trả lời cuối
               │ lời cuối cùng   │
               └─────────────────┘
```

---

## 📂 4. Cấu Trúc Thư Mục Dự Án

Mã nguồn được tổ chức theo tiêu chuẩn **Clean Architecture** nghiêm ngặt để đảm bảo khả năng kiểm thử độc lập:

```
src/pnetai_chatbot/
├── domain/                  # Layer 1: Lõi nghiệp vụ (Entities, Value Objects, Enums, Exceptions)
├── application/             # Layer 2: Quy trình ứng dụng (Use Cases, Ports/Interfaces, DTOs)
├── infrastructure/          # Layer 3: Hạ tầng kỹ thuật
│   ├── llm/                 #   LLM Adapters: openai, anthropic, gemini, ollama, selfhosted
│   ├── agent/               #   LangGraph Nodes, Orchestrator, Prompts, State
│   ├── tools/               #   Tool implementations (Vector, MongoDB, Web Search)
│   ├── persistence/         #   MongoDB repositories (Session, History)
│   └── config/              #   Settings, DB Schema, Seed data
└── interface/               # Layer 4: Cổng giao tiếp ngoài (FastAPI routers, Middlewares, Schemas)
```

---

## 🚀 5. Hướng Dẫn Khởi Động Nhanh

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

## 🤖 6. Cấu Hình Self-Hosted / Finetune Model

PetBot hỗ trợ tích hợp mô hình finetune tự host để sinh câu trả lời cuối cùng, trong khi giữ nguyên model cloud mạnh hơn cho các bước reasoning.

### Cách hoạt động

| Bước | LLM sử dụng | Lý do |
|------|------------|-------|
| `intent_analyzer` | Reasoning LLM (cloud) | Cần follow JSON schema nghiêm ngặt |
| `tool_executor` | Reasoning LLM (cloud) | Sinh câu truy vấn MongoDB chính xác |
| `context_merger` | Không cần LLM | Chỉ gộp dữ liệu |
| `response_generator` | **Response LLM** (self-hosted ✅) | Sinh câu trả lời tự nhiên |

### Kích hoạt Self-Hosted Model

Chỉnh `.env` — không cần sửa mã nguồn:

```env
# Bật self-hosted model cho bước sinh câu trả lời
RESPONSE_LLM_PROVIDER=selfhosted
RESPONSE_LLM_MODEL=pet-bot-v1          # Tên model trong server của bạn

SELFHOSTED_BASE_URL=http://localhost:8080/v1
SELFHOSTED_API_KEY=not-required        # Nhiều server local không cần API key
SELFHOSTED_TIMEOUT=60.0                # Cao hơn vì local inference chậm hơn cloud
```

> **Để trống `RESPONSE_LLM_PROVIDER`** → Hệ thống tự động fallback về `LLM_PROVIDER` (mặc định).

### Framework tương thích

| Framework | Tương thích | Ghi chú |
|-----------|------------|---------|
| **vLLM** | ✅ Hoàn toàn | `--served-model-name pet-bot-v1` |
| **LM Studio** | ✅ Hoàn toàn | Bật "Local Server" mode |
| **LMDeploy** | ✅ Hoàn toàn | OpenAI-compatible server |
| **text-generation-webui** | ✅ | Cần bật OpenAI extension |
| **Ollama** | ✅ | Dùng `RESPONSE_LLM_PROVIDER=ollama` thay thế |

---

## 🧪 7. Kiểm Thử & Định Dạng Code

Dự án áp dụng tiêu chuẩn mã nguồn cực kỳ nghiêm ngặt nhằm tránh lỗi cú pháp và đảm bảo tính đồng bộ:

```bash
# 1. Tự động kiểm tra và sửa định dạng code bằng Ruff
uv run ruff format src/ tests/
uv run ruff check src/ tests/ --fix

# 2. Chạy toàn bộ suite kiểm thử (Unit & Integration)
uv run pytest
```

---

## 🐳 8. Triển Khai Trên Môi Trường Production

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

## 📚 9. Nhật Ký Nghiệm Thu Từng Phase

Chi tiết báo cáo nghiệm thu kỹ thuật và thiết kế của từng giai đoạn phát triển dự án được lưu trữ trực tiếp trong thư mục [doc/](doc/):

* 🔗 **Phase 1**: [Tài liệu Nghiệm thu Nền tảng Cơ sở](doc/phase-1-completion.md)
* 🔗 **Phase 2**: [Tài liệu Nghiệm thu LLM Adapter](doc/phase-2-completion.md)
* 🔗 **Phase 3**: [Tài liệu Nghiệm thu Công cụ (Tools)](doc/phase-3-completion.md)
* 🔗 **Phase 4**: [Tài liệu Nghiệm thu Agent Orchestrator](doc/phase-4-completion.md)
* 🔗 **Phase 5**: [Tài liệu Nghiệm thu Lịch sử & Phiên Chat](doc/phase-5-completion.md)
* 🔗 **Phase 6**: [Tài liệu Nghiệm thu API Layer](doc/phase-6-completion.md)
* 🔗 **Phase 7**: [Tài liệu Nghiệm thu Kiểm Thử & Hardening](doc/phase-7-completion.md)

---

## 📝 10. Bản Quyền & Giảng Viên Hướng Dẫn

* **Dự án tốt nghiệp**: Đại học FPT (FPT University Capstone Project).
* **Quyền sở hữu**: Bản quyền thuộc về Nhóm Nghiên Cứu và Đại học FPT.
* **Liên hệ phát triển**: [Huylao-gia](https://github.com/Huylao-gia) & Đội ngũ Phát triển PetBot.