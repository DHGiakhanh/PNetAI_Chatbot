# 📘 Hướng Dẫn Kỹ Thuật Dành Cho Nhà Phát Triển Tiếp Quản Dự Án

Tài liệu này được biên soạn dành riêng cho các nhà phát triển (Developers) tiếp quản, duy trì và tiếp tục phát triển hệ thống **PetBot AI Chatbot**. Tài liệu cung cấp cái nhìn chi tiết về luồng vận hành, sơ đồ cấu trúc và hướng dẫn từng bước để mở rộng hệ thống một cách chuẩn mực.

---

## 🏗️ 1. Triết Lý Thiết Kế & Luồng Vận Hành Lõi

Hệ thống được phát triển theo mô hình **Clean Architecture (Domain-Driven Design - DDD)**. Quy tắc tối cao là **Domain Layer độc lập hoàn toàn**, các Layer bên ngoài phụ thuộc vào Layer bên trong, giao tiếp qua các **Ports (Interfaces)**.

### Sơ đồ Pipeline xử lý Request:

```
[HTTP Request]
      │
      ▼
┌──────────────┐
│  Middleware  │ ──► 1. RateLimitMiddleware (Kiểm tra IP/Member Token Bucket)
└──────────────┘ ──► 2. AuthMiddleware (Giải mã JWT, nhúng User Context)
      │
      ▼
┌──────────────┐
│  Controller  │ ──► endpoints/chat.py (Nhận query, session_id, stream cờ)
└──────────────┘
      │
      ▼
┌──────────────┐
│   Use Case   │ ──► ResolveUserContextUseCase (Nạp session cũ và tóm tắt AI)
└──────────────┘ ──► ChatOrchestratorUseCase (Gọi đồ thị Agent điều phối)
      │
      ▼
┌──────────────┐
│  Agent Graph │ ──► LangGraph StateGraph (Chạy tuần hoàn Intent -> Tools -> Response)
└──────────────┘
      │
      ▼
┌──────────────┐
│  Persistence │ ──► Ghi lịch sử bất đồng bộ vào MongoDB chat_messages
└──────────────┘ ──► (Kích hoạt Background Task tóm tắt hội thoại nếu msg_count % 10 == 0)
      │
      ▼
[HTTP Response]  ──► Trả về câu trả lời cuối cùng (JSON hoặc SSE Stream từng chữ)
```

---

## 🔌 2. Hướng Dẫn Mở Rộng Tính Năng Hệ Thống (How-To)

Kiến trúc Clean Architecture giúp việc mở rộng hệ thống cực kỳ dễ dàng mà không phá vỡ cấu trúc cũ. Dưới đây là hướng dẫn cho các kịch bản thực tế:

### 2.1 Thêm Nhà Cung Cấp LLM Mới (Ví dụ: Cohere hoặc DeepSeek)
1. **Tạo Adapter File**: Tạo file `cohere_adapter.py` tại `src/pnetai_chatbot/infrastructure/llm/`.
2. **Kế thừa Interface**: Viết class `CohereAdapter` kế thừa từ `ILLMAdapter` (trong `src/pnetai_chatbot/application/ports/llm_port.py`).
3. **Cài đặt các phương thức**:
   * Triển khai hàm `chat(self, messages, temperature, max_tokens)` sử dụng API của nhà cung cấp mới.
   * Triển khai hàm `embed(self, texts)` nếu mô hình hỗ trợ tạo vector nhúng.
4. **Đăng ký vào Factory**: Mở file `src/pnetai_chatbot/infrastructure/llm/llm_factory.py` và đăng ký provider mới vào `_registry`:
   ```python
   from pnetai_chatbot.infrastructure.llm.cohere_adapter import CohereAdapter
   LLMFactory.register("cohere", CohereAdapter)
   ```
5. **Cấu hình cấu trúc**: Cập nhật file `.env` chỉnh sửa `LLM_PROVIDER=cohere`.

---

### 2.2 Thêm Công Cụ (Tool) Tra Cứu Mới (Ví dụ: Tra cứu lịch khám thú y)
1. **Định nghĩa Interface (nếu cần)**: Tạo port interface mới tại `src/pnetai_chatbot/application/ports/`.
2. **Viết Tool Class**: Tạo file tool tương ứng tại `src/pnetai_chatbot/infrastructure/tools/` (kế thừa port và cài đặt logic tra cứu API/DB thực tế).
3. **Đăng ký vào ToolRegistry**: Mở file `src/pnetai_chatbot/infrastructure/tools/tool_registry.py`:
   * Nhận instance của tool trong phương thức `__init__`.
   * Đăng ký tên ánh xạ và mô tả tool để Agent nhận diện.
4. **Cấu hình trong DI System**: Cập nhật hàm `get_tool_registry()` trong file `src/pnetai_chatbot/interface/api/v1/dependencies.py` để khởi tạo tool mới.
5. **Cập nhật Prompts**: Mở `src/pnetai_chatbot/infrastructure/agent/prompts.py` và bổ sung mô tả công cụ mới vào hướng dẫn phân tích ý định (`INTENT_SYSTEM_PROMPT`) giúp Agent biết khi nào nên gọi công cụ này.

---

### 2.3 Thêm Collection MongoDB Tra Cứu Mới
Khi website phát triển thêm thực thể dữ liệu mới (ví dụ: `veterinarians` - Danh sách bác sĩ thú y) và bạn muốn Chatbot tra cứu được dữ liệu này:
1. **whitelist Collection**: Mở `src/pnetai_chatbot/infrastructure/tools/mongo_query_tool.py` và bổ sung `"veterinarians"` vào danh sách `ALLOWED_COLLECTIONS`.
2. **Cập nhật Schema Context**: Mở file schema `src/pnetai_chatbot/infrastructure/config/mongo_db_schema.py`, mô tả cấu trúc các trường của collection mới để Agent hiểu khi sinh câu lệnh:
   ```python
   "veterinarians": {
       "name": "Tên bác sĩ",
       "specialty": "Chuyên môn điều trị",
       "rating": "Đánh giá sao (1-5)"
   }
   ```

---

### 2.4 Thay Đổi Cấu Trúc Đồ Thị Agent (LangGraph)
Nếu bạn muốn bổ sung một bước duyệt kết quả bảo mật bằng AI trước khi trả về (Guardrail Node):
1. **Viết Node Method**: Mở file `src/pnetai_chatbot/infrastructure/agent/orchestrator.py` và định nghĩa node mới:
   ```python
   async def guardrail_node(self, state: AgentState) -> dict:
       # Logic kiểm duyệt nội dung nhạy cảm ở đây...
       return {"final_response": moderated_response}
   ```
2. **Kết nối Node vào Đồ thị**: Cập nhật hàm `build_agent_graph()`:
   ```python
   builder.add_node("guardrails", self.guardrail_node)
   # Điều chỉnh các cạnh kết nối (edges) để luồng đi qua node này trước khi kết thúc
   builder.add_edge("guardrails", END)
   ```

---

## 🧪 3. Quy Trình Phát Triển & Bảo Trì Code

Để đảm bảo hệ thống luôn trong trạng thái ổn định nhất khi phát triển tiếp:

* **Chạy Ruff kiểm tra tĩnh**: Luôn chạy kiểm tra cú pháp và format trước khi commit:
  ```bash
  uv run ruff format src/ tests/
  uv run ruff check src/ tests/ --fix
  ```
* **Bổ sung và chạy Tests tự động**:
  * Khi viết Use Case mới, bắt buộc viết Unit Test mock repository tương ứng đặt tại `tests/unit/application/use_cases/`.
  * Chạy toàn bộ test suite để đảm bảo các thay đổi mới không làm sập các tính năng cũ:
    ```bash
    uv run pytest
    ```

---

## 🔮 4. Gợi Ý Các Cải Tiến Cho Tương Lai (Roadmap)

Dưới đây là một số hướng đi giá trị bạn có thể tiếp tục phát triển để cải tiến sản phẩm:
1. **Tích hợp Reranking (Cross-Encoders) cho RAG**: Thêm bước Rerank các bài viết trích xuất từ Qdrant trước khi đưa vào LLM để tăng độ liên quan ngữ cảnh và độ chính xác của câu trả lời.
2. **Tối ưu hóa Long-Term Memory**: Tích hợp lưu trữ hồ sơ đặc trưng thú cưng của người dùng vào một collection riêng để Agent luôn ghi nhớ thông tin thú cưng (giống mèo, độ tuổi) xuyên suốt các session khác nhau mà không cần tóm tắt lại.
3. **Phân tích hình ảnh thú cưng (Multimodal)**: Nâng cấp API tiếp nhận hình ảnh, sử dụng mô hình Gemini/GPT-4o Vision để chẩn đoán sơ bộ triệu chứng bệnh ngoài da hoặc loại thức ăn qua ảnh chụp thú cưng.
