# 🐾 PetBot — Chatbot Server System Specification

> **Version:** 1.0.0  
> **Status:** Draft  
> **Stack:** Python · LangGraph · FastAPI · MongoDB · Qdrant · Tavily  
> **Architecture:** Clean Architecture (Domain-Driven Design)

---

## 1. Tổng Quan Hệ Thống

### 1.1 Mô Tả

PetBot là chatbot server phục vụ website thú cưng, cung cấp khả năng hỏi đáp thông minh đa bước (multi-step reasoning). Hệ thống tổng hợp thông tin từ ba nguồn: internet thời gian thực (Tavily), cơ sở tri thức nội bộ (Vector DB), và cơ sở dữ liệu nghiệp vụ (MongoDB của website). LLM được triển khai theo pattern Adapter để dễ dàng hoán đổi giữa các provider (OpenAI, Anthropic, Gemini, Ollama, ...).

### 1.2 Luồng Hoạt Động Tổng Quan

```
Client (Website)
    │
    ▼
[POST /api/v1/chat]
    │  payload: {query, session_id?, user_id?, token?}
    ▼
┌──────────────────────────────────────────────────────┐
│                  CHATBOT SERVER                      │
│                                                      │
│  Auth & Session Guard                                │
│      │                                               │
│      ▼                                               │
│  Session Manager ──► MongoDB (chat history)          │
│      │                                               │
│      ▼                                               │
│  Agent Orchestrator (LangGraph ReAct Agent)          │
│      │                                               │
│      ├──► [Tool: Tavily Web Search]                  │
│      ├──► [Tool: Vector DB Search]   ──► Qdrant      │
│      ├──► [Tool: MongoDB Query Gen]  ──► MongoDB     │
│      └──► [Tool: LLM Adapter]        ──► Provider    │
│                                                      │
│  Response Formatter                                  │
│      │                                               │
│      ▼                                               │
│  History Writer ──► MongoDB                          │
└──────────────────────────────────────────────────────┘
    │
    ▼
Client Response (SSE / JSON)
```

---

## 2. Kiến Trúc Clean Architecture

### 2.1 Nguyên Tắc Thiết Kế

| Layer | Vai trò | Phụ thuộc vào |
|---|---|---|
| **Domain** | Entities, business rules thuần túy | Không phụ thuộc gì |
| **Application** | Use cases, interfaces (ports) | Domain |
| **Infrastructure** | Adapters, DB, external APIs | Application interfaces |
| **Interface** | API routes, request/response | Application |

> ⚠️ **Caution:** Dependency chỉ đi từ ngoài vào trong. Infrastructure KHÔNG bao giờ được import trực tiếp vào Domain hay Application logic.

### 2.2 Dependency Injection Flow

```
FastAPI Router
    │ injects
    ▼
Use Case (Application Layer)
    │ depends on interfaces (ports)
    ▼
Concrete Adapters (Infrastructure Layer)
    │
    ▼
External Services (MongoDB, Qdrant, Tavily, LLM APIs)
```

---

## 3. Project Structure

```
pnetai-chatbot/
│
├── pyproject.toml                  # deps: uv/poetry
├── .env.example
├── docker-compose.yml              # MongoDB + Qdrant
├── Makefile
│
├── src/
│   └── petbot/
│       │
│       ├── domain/                         # ── LAYER 1: DOMAIN ──
│       │   ├── __init__.py
│       │   ├── entities/
│       │   │   ├── message.py              # Entity: Message (role, content, timestamp)
│       │   │   ├── session.py              # Entity: ChatSession
│       │   │   ├── user.py                 # Entity: User (id, is_authenticated)
│       │   │   └── tool_result.py          # Entity: ToolCallResult
│       │   ├── value_objects/
│       │   │   ├── query.py                # VO: UserQuery (text, intent)
│       │   │   └── session_id.py           # VO: SessionId (UUID)
│       │   ├── enums/
│       │   │   ├── role.py                 # Enum: MessageRole (user/assistant/system/tool)
│       │   │   ├── tool_type.py            # Enum: ToolType (tavily/vector/mongo/llm)
│       │   │   └── user_permission.py      # Enum: UserPermission (guest/member/admin)
│       │   └── exceptions/
│       │       ├── session.py              # SessionNotFoundException, etc.
│       │       └── tool.py                 # ToolExecutionError, etc.
│       │
│       ├── application/                    # ── LAYER 2: APPLICATION ──
│       │   ├── __init__.py
│       │   │
│       │   ├── ports/                      # Interfaces (Abstract Base Classes)
│       │   │   ├── llm_port.py             # ILLMAdapter
│       │   │   ├── vector_store_port.py    # IVectorStore
│       │   │   ├── mongo_query_port.py     # IMongoQueryExecutor
│       │   │   ├── web_search_port.py      # IWebSearchTool
│       │   │   ├── session_repo_port.py    # ISessionRepository
│       │   │   └── history_repo_port.py    # IHistoryRepository
│       │   │
│       │   ├── use_cases/
│       │   │   ├── chat/
│       │   │   │   ├── process_chat.py         # UC: ProcessChatUseCase (main orchestrator)
│       │   │   │   ├── create_session.py       # UC: CreateSessionUseCase
│       │   │   │   └── get_session_history.py  # UC: GetSessionHistoryUseCase
│       │   │   └── session/
│       │   │       ├── summarize_session.py    # UC: SummarizeSessionUseCase
│       │   │       └── resolve_user_context.py # UC: ResolveUserContextUseCase
│       │   │
│       │   ├── services/
│       │   │   ├── agent_service.py        # Wraps LangGraph agent execution
│       │   │   ├── context_builder.py      # Builds context từ history + summary
│       │   │   └── permission_service.py   # Kiểm tra quyền user/guest
│       │   │
│       │   └── dto/                        # Data Transfer Objects
│       │       ├── chat_request.py         # ChatRequestDTO
│       │       ├── chat_response.py        # ChatResponseDTO
│       │       └── session_dto.py          # SessionDTO
│       │
│       ├── infrastructure/                 # ── LAYER 3: INFRASTRUCTURE ──
│       │   ├── __init__.py
│       │   │
│       │   ├── llm/
│       │   │   ├── base_adapter.py         # Abstract LLMAdapter (implements ILLMAdapter)
│       │   │   ├── openai_adapter.py       # OpenAI GPT-4o, GPT-4-mini
│       │   │   ├── anthropic_adapter.py    # Claude 3.5 Sonnet, Haiku
│       │   │   ├── gemini_adapter.py       # Gemini 1.5 Pro/Flash
│       │   │   ├── ollama_adapter.py       # Local Ollama models
│       │   │   └── llm_factory.py          # Factory: tạo adapter từ config
│       │   │
│       │   ├── tools/
│       │   │   ├── tavily_tool.py          # TavilyWebSearch (implements IWebSearchTool)
│       │   │   ├── vector_search_tool.py   # QdrantVectorSearch (implements IVectorStore)
│       │   │   ├── mongo_query_tool.py     # MongoQueryTool (implements IMongoQueryExecutor)
│       │   │   └── tool_registry.py        # ToolRegistry: đăng ký và map tools
│       │   │
│       │   ├── agent/
│       │   │   ├── graph_builder.py        # LangGraph StateGraph builder
│       │   │   ├── nodes/
│       │   │   │   ├── intent_analyzer.py  # Node: Phân tích intent + chọn tools
│       │   │   │   ├── tool_executor.py    # Node: Execute tool calls
│       │   │   │   ├── context_merger.py   # Node: Merge tool results vào context
│       │   │   │   └── response_gen.py     # Node: Generate final response
│       │   │   ├── state.py                # AgentState (TypedDict cho LangGraph)
│       │   │   └── prompts/
│       │   │       ├── system_prompt.py
│       │   │       ├── intent_prompt.py
│       │   │       └── mongo_gen_prompt.py # Prompt để gen MongoDB query từ schema
│       │   │
│       │   ├── persistence/
│       │   │   ├── mongodb/
│       │   │   │   ├── client.py           # MongoClient singleton
│       │   │   │   ├── session_repo.py     # SessionRepository (implements ISessionRepository)
│       │   │   │   ├── history_repo.py     # HistoryRepository (implements IHistoryRepository)
│       │   │   │   └── schemas/
│       │   │   │       ├── session_schema.py
│       │   │   │       └── message_schema.py
│       │   │   └── qdrant/
│       │   │       ├── client.py           # QdrantClient singleton
│       │   │       └── vector_repo.py      # VectorRepository
│       │   │
│       │   └── config/
│       │       ├── settings.py             # Pydantic BaseSettings
│       │       └── mongo_db_schema.py      # Website MongoDB schema definitions
│       │
│       └── interface/                      # ── LAYER 4: INTERFACE ──
│           ├── __init__.py
│           ├── api/
│           │   ├── v1/
│           │   │   ├── router.py           # APIRouter tổng hợp
│           │   │   ├── endpoints/
│           │   │   │   ├── chat.py         # POST /chat, GET /chat/history
│           │   │   │   ├── session.py      # GET/DELETE /sessions
│           │   │   │   └── health.py       # GET /health
│           │   │   └── dependencies.py     # FastAPI Depends() injection
│           │   └── middleware/
│           │       ├── auth_middleware.py   # JWT validation (optional user)
│           │       └── cors_middleware.py
│           └── schemas/                    # Pydantic request/response schemas
│               ├── chat_schema.py
│               └── session_schema.py
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   └── integration/
│       ├── test_chat_flow.py
│       └── test_mongo_query_tool.py
│
└── scripts/
    ├── seed_vector_db.py           # Seed dữ liệu vào Qdrant
    └── create_mongo_indexes.py     # Tạo indexes cho chat MongoDB
```

---

## 4. Domain Layer — Entities & Value Objects

### 4.1 Entity: `ChatSession`

```python
@dataclass
class ChatSession:
    id: SessionId
    user_id: str | None          # None nếu là guest
    is_authenticated: bool
    created_at: datetime
    updated_at: datetime
    message_count: int
    summary: str | None          # Được cập nhật định kỳ
    metadata: dict               # source_page, device, etc.
```

### 4.2 Entity: `Message`

```python
@dataclass
class Message:
    id: str                      # UUID
    session_id: SessionId
    role: MessageRole            # user | assistant | system | tool
    content: str
    tool_calls: list[ToolCallResult] | None
    timestamp: datetime
    tokens_used: int | None
```

### 4.3 Entity: `UserQuery`

```python
@dataclass
class UserQuery:
    raw_text: str
    session_id: SessionId
    user: User
    timestamp: datetime
```

---

## 5. Application Layer — Ports (Interfaces)

### 5.1 `ILLMAdapter`

```python
class ILLMAdapter(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse: ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...
```

### 5.2 `IMongoQueryExecutor`

```python
class IMongoQueryExecutor(ABC):
    @abstractmethod
    async def execute_generated_query(
        self,
        collection: str,
        filter_query: dict,
        projection: dict | None,
        limit: int = 20,
    ) -> list[dict]: ...

    @abstractmethod
    async def get_schema_context(self, collection: str) -> str: ...
```

### 5.3 `IVectorStore`

```python
class IVectorStore(ABC):
    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[VectorSearchResult]: ...
```

### 5.4 `ISessionRepository`

```python
class ISessionRepository(ABC):
    @abstractmethod
    async def create(self, session: ChatSession) -> ChatSession: ...

    @abstractmethod
    async def get_by_id(self, session_id: SessionId) -> ChatSession | None: ...

    @abstractmethod
    async def update_summary(self, session_id: SessionId, summary: str) -> None: ...

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[ChatSession]: ...

    @abstractmethod
    async def delete(self, session_id: SessionId) -> None: ...
```

---

## 6. Infrastructure Layer — Chi Tiết Implement

### 6.1 LLM Adapter System

#### Pattern: Factory + Strategy

```python
# llm_factory.py
class LLMFactory:
    _registry: dict[str, type[ILLMAdapter]] = {
        "openai":    OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "gemini":    GeminiAdapter,
        "ollama":    OllamaAdapter,
    }

    @classmethod
    def create(cls, provider: str, model: str, **kwargs) -> ILLMAdapter:
        adapter_cls = cls._registry.get(provider)
        if not adapter_cls:
            raise ValueError(f"Unknown provider: {provider}")
        return adapter_cls(model=model, **kwargs)
```

#### Config-driven switching (`.env`)

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048
# Fallback provider nếu primary fail
LLM_FALLBACK_PROVIDER=anthropic
LLM_FALLBACK_MODEL=claude-haiku-4-5
```

#### Mỗi Adapter implement

```python
class OpenAIAdapter(ILLMAdapter):
    def __init__(self, model: str, api_key: str, **kwargs):
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def chat(self, messages, tools=None, **kwargs) -> LLMResponse:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools,
            **kwargs,
        )
        return LLMResponse.from_openai(response)

    async def embed(self, text: str) -> list[float]:
        resp = await self._client.embeddings.create(
            model="text-embedding-3-small", input=text
        )
        return resp.data[0].embedding
```

---

### 6.2 Agent Orchestrator — LangGraph ReAct

#### Agent State

```python
class AgentState(TypedDict):
    # Input
    query: str
    session_id: str
    user_id: str | None
    is_authenticated: bool

    # Context
    conversation_history: list[dict]    # last N messages
    session_summary: str | None         # summary từ sessions cũ

    # Reasoning
    messages: Annotated[list, add_messages]  # LangGraph messages
    tool_calls_made: list[str]           # track tools đã dùng
    tool_results: dict[str, Any]         # kết quả từng tool

    # Output
    final_response: str | None
    error: str | None
    iterations: int
```

#### LangGraph StateGraph

```
START
  │
  ▼
[intent_analyzer_node]          # Phân tích query → quyết định tools cần dùng
  │
  ▼
[tool_selector_node]            # Chọn và sắp xếp thứ tự tool execution
  │
  ▼
[tool_executor_node] ◄─────┐   # Thực thi từng tool
  │                        │
  ├─► nếu cần tool tiếp ───┘
  │
  ▼
[context_merger_node]           # Merge tất cả tool results → unified context
  │
  ▼
[response_generator_node]       # LLM tổng hợp → final response
  │
  ▼
[history_writer_node]           # Ghi lịch sử vào MongoDB
  │
  ▼
END
```

#### Tool Selection Logic (trong `intent_analyzer_node`)

LLM được giao nhiệm vụ phân tích query và trả về JSON:

```json
{
  "reasoning": "User hỏi về giá sản phẩm thức ăn cho chó → cần query MongoDB products collection",
  "tools_needed": [
    {
      "tool": "mongodb_query",
      "priority": 1,
      "reason": "Cần lấy giá sản phẩm từ DB website",
      "params_hint": {
        "collection": "products",
        "query_intent": "tìm sản phẩm thức ăn cho chó theo tên/giá"
      }
    },
    {
      "tool": "vector_search",
      "priority": 2,
      "reason": "Bổ sung thông tin dinh dưỡng từ knowledge base",
      "params_hint": {
        "query": "dog food nutrition requirements"
      }
    }
  ]
}
```

---

### 6.3 MongoDB Query Tool — Mongo Query Generation

#### Flow chi tiết

```
User Query: "Thức ăn cho chó poodle giá dưới 300k"
    │
    ▼
[mongo_gen_prompt.py]
    Prompt = system_schema_context + user_query
    → LLM generates:
    {
      "collection": "products",
      "filter": {
        "category": "dog_food",
        "tags": { "$in": ["poodle", "small_breed"] },
        "price": { "$lte": 300000 },
        "is_active": true
      },
      "projection": {
        "name": 1, "price": 1, "description": 1,
        "images": 1, "stock": 1, "_id": 1
      },
      "sort": { "price": 1 },
      "limit": 10
    }
    │
    ▼
[MongoQueryValidator]
    - Validate collection name nằm trong whitelist
    - Validate không có operators nguy hiểm ($where, $eval)
    - Validate projection hợp lệ
    │
    ▼
[MongoQueryExecutor.execute()]
    → Kết quả: list[dict] products
    │
    ▼
[Result Serializer]
    → Chuyển ObjectId → str, datetime → ISO string
    → Truncate fields quá dài (description > 500 chars)
```

#### Schema Context cho MongoDB Query Generation

```python
# mongo_db_schema.py — Website DB schema (readonly, context-only)
WEBSITE_DB_SCHEMA = {
    "products": {
        "description": "Sản phẩm thú cưng",
        "fields": {
            "_id": "ObjectId",
            "name": "str — Tên sản phẩm",
            "slug": "str — URL-friendly name",
            "category": "str — Enum: dog_food|cat_food|accessories|medicine|...",
            "tags": "list[str] — Tags phân loại",
            "price": "int — Giá VNĐ",
            "sale_price": "int | None — Giá khuyến mãi",
            "description": "str — Mô tả",
            "brand": "str",
            "images": "list[str] — URLs ảnh",
            "stock": "int — Tồn kho",
            "is_active": "bool",
            "rating": "float",
            "review_count": "int",
            "created_at": "datetime",
        },
        "indexes": ["category", "tags", "price", "brand", "is_active"],
        "sample_queries": [
            "Tìm sản phẩm theo category + price range",
            "Tìm sản phẩm theo brand",
            "Tìm sản phẩm theo tags (loài thú, kích cỡ, ...)",
        ]
    },
    "pets": {
        "description": "Thú cưng đang bán",
        "fields": {
            "_id": "ObjectId",
            "name": "str — Tên thú",
            "species": "str — Enum: dog|cat|bird|fish|rabbit|...",
            "breed": "str — Giống",
            "age_months": "int",
            "gender": "str — male|female",
            "price": "int",
            "health_status": "str",
            "vaccinated": "bool",
            "images": "list[str]",
            "is_available": "bool",
            "description": "str",
        },
        "indexes": ["species", "breed", "price", "is_available"],
    },
    "orders": {
        "description": "Đơn hàng — CHỈ query khi user là authenticated và hỏi về đơn hàng CỦA HỌ",
        "fields": {
            "_id": "ObjectId",
            "user_id": "str — ObjectId of user",
            "items": "list[{product_id, quantity, price}]",
            "total": "int",
            "status": "str — pending|confirmed|shipping|delivered|cancelled",
            "created_at": "datetime",
        },
        "security_note": "ALWAYS filter by user_id khi query collection này",
    },
    "articles": {
        "description": "Bài viết, hướng dẫn chăm sóc thú cưng",
        "fields": {
            "_id": "ObjectId",
            "title": "str",
            "content": "str",
            "category": "str",
            "tags": "list[str]",
            "published_at": "datetime",
        }
    }
}

# Whitelist — chỉ cho query các collection này
ALLOWED_COLLECTIONS = {"products", "pets", "orders", "articles", "reviews"}

# Operators bị cấm
FORBIDDEN_OPERATORS = {"$where", "$eval", "$function", "$accumulator"}
```

---

### 6.4 Vector Search Tool

```python
class QdrantVectorSearchTool(IVectorStore):
    """
    Collection: pet_knowledge_base
    - Nội dung: bài viết chăm sóc, FAQ, hướng dẫn dinh dưỡng
    - Embedding model: text-embedding-3-small (1536 dims)
    """
    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[VectorSearchResult]:
        results = await self._client.search(
            collection_name="pet_knowledge_base",
            query_vector=query_embedding,
            limit=top_k,
            query_filter=filters,
            with_payload=True,
        )
        return [VectorSearchResult.from_qdrant(r) for r in results]
```

---

### 6.5 Session & History Management

#### Data Models trong Chat MongoDB

**Collection: `chat_sessions`**

```json
{
  "_id": "uuid-v4",
  "user_id": "string | null",
  "is_authenticated": true,
  "created_at": "ISODate",
  "updated_at": "ISODate",
  "message_count": 12,
  "total_tokens": 8420,
  "summary": "User hỏi về chế độ dinh dưỡng cho chó Poodle 3 tháng tuổi...",
  "summary_updated_at": "ISODate",
  "metadata": {
    "source_page": "/products",
    "user_agent": "...",
    "ip_hash": "sha256(...)"
  }
}
```

**Collection: `chat_messages`**

```json
{
  "_id": "uuid-v4",
  "session_id": "uuid-v4",
  "role": "user | assistant | tool",
  "content": "string",
  "tool_calls": [
    {
      "tool_name": "mongodb_query",
      "input": {"collection": "products", "filter": {...}},
      "output_summary": "Tìm được 5 sản phẩm thức ăn cho Poodle",
      "execution_time_ms": 120
    }
  ],
  "timestamp": "ISODate",
  "tokens_used": 342,
  "model": "gpt-4o-mini"
}
```

**Indexes:**

```js
db.chat_sessions.createIndex({ "user_id": 1 })
db.chat_sessions.createIndex({ "created_at": -1 })
db.chat_messages.createIndex({ "session_id": 1, "timestamp": 1 })
db.chat_messages.createIndex({ "session_id": 1, "role": 1 })
```

---

### 6.6 Session Summarization Strategy

Kích hoạt khi: `message_count % 10 == 0` hoặc khi session đạt `5000 tokens`.

```python
class SummarizeSessionUseCase:
    async def execute(self, session_id: SessionId) -> str:
        messages = await self._history_repo.get_all(session_id)

        # Lấy summary cũ (nếu có) làm context
        session = await self._session_repo.get_by_id(session_id)
        existing_summary = session.summary or ""

        prompt = f"""
        Previous summary: {existing_summary}

        New messages to incorporate:
        {format_messages_for_summary(messages[-20:])}

        Tạo một bản tóm tắt ngắn gọn (< 300 từ) về:
        - Chủ đề chính người dùng quan tâm
        - Thông tin cá nhân đã chia sẻ (tên thú, loài, vấn đề)
        - Các sản phẩm/dịch vụ đã hỏi
        - Trạng thái vấn đề (đã giải quyết / đang xử lý)
        """

        summary = await self._llm.chat([{"role": "user", "content": prompt}])
        await self._session_repo.update_summary(session_id, summary.text)
        return summary.text
```

**Context Building cho mỗi request:**

```python
class ContextBuilder:
    def build(
        self,
        session: ChatSession,
        recent_messages: list[Message],  # last 10 messages
    ) -> list[dict]:
        context = []

        # 1. System prompt
        context.append({"role": "system", "content": SYSTEM_PROMPT})

        # 2. Session summary làm context nền
        if session.summary:
            context.append({
                "role": "system",
                "content": f"[SESSION CONTEXT]\n{session.summary}"
            })

        # 3. Recent conversation history
        for msg in recent_messages:
            context.append({"role": msg.role.value, "content": msg.content})

        return context
```

---

## 7. Interface Layer — API Endpoints

### 7.1 Endpoint: `POST /api/v1/chat`

**Request:**

```json
{
  "query": "Thức ăn nào tốt cho chó Poodle 3 tháng?",
  "session_id": "optional-uuid",
  "stream": true
}
```

**Headers:**
- `Authorization: Bearer <jwt>` — Optional. Nếu có → authenticated user.

**Response (SSE stream):**

```
data: {"type": "thinking", "content": "Đang phân tích câu hỏi..."}
data: {"type": "tool_call", "tool": "mongodb_query", "status": "running"}
data: {"type": "tool_result", "tool": "mongodb_query", "summary": "Tìm được 5 sản phẩm"}
data: {"type": "tool_call", "tool": "vector_search", "status": "running"}
data: {"type": "answer", "content": "Dựa trên thông tin..."}
data: {"type": "done", "session_id": "uuid", "tokens_used": 850}
```

**Response (JSON non-stream):**

```json
{
  "answer": "...",
  "session_id": "uuid",
  "sources": [
    {"type": "mongodb", "collection": "products", "count": 5},
    {"type": "vector", "documents": 3}
  ],
  "tools_used": ["mongodb_query", "vector_search"],
  "tokens_used": 850
}
```

### 7.2 Endpoint: `GET /api/v1/sessions`

> **Auth required.** Trả về danh sách sessions của user.

```json
{
  "sessions": [
    {
      "id": "uuid",
      "created_at": "ISO",
      "message_count": 12,
      "summary": "Hỏi về chó Poodle...",
      "last_message_at": "ISO"
    }
  ]
}
```

### 7.3 Endpoint: `GET /api/v1/sessions/{session_id}/history`

> **Auth required + ownership check.**

```json
{
  "session_id": "uuid",
  "messages": [
    {"role": "user", "content": "...", "timestamp": "ISO"},
    {"role": "assistant", "content": "...", "timestamp": "ISO"}
  ],
  "summary": "..."
}
```

### 7.4 Endpoint: `DELETE /api/v1/sessions/{session_id}`

> **Auth required + ownership check.** Xóa session và toàn bộ messages.

---

## 8. Permission & Session Logic

### 8.1 User Classification

| Loại | Điều kiện | Session lưu? | History lưu? | Query orders? |
|---|---|---|---|---|
| **Guest** | Không có JWT | ❌ | ❌ | ❌ |
| **Authenticated** | JWT hợp lệ | ✅ | ✅ | ✅ (chỉ của họ) |

### 8.2 Session Resolution Flow

```python
async def resolve_session(
    session_id: str | None,
    user: User,
) -> ChatSession | None:
    if not user.is_authenticated:
        # Guest: tạo in-memory session, không persist
        return ChatSession.create_ephemeral()

    if session_id:
        session = await session_repo.get_by_id(session_id)
        if session and session.user_id == user.id:
            return session
        # session không tồn tại hoặc không phải của user → tạo mới

    # Tạo session mới cho authenticated user
    new_session = ChatSession.create(user_id=user.id)
    return await session_repo.create(new_session)
```

### 8.3 MongoDB Query Security

```python
class MongoQueryTool:
    def _validate_query(self, collection: str, filter_query: dict, user: User):
        # 1. Collection whitelist check
        if collection not in ALLOWED_COLLECTIONS:
            raise ToolExecutionError(f"Collection {collection} not allowed")

        # 2. Forbidden operators check
        query_str = json.dumps(filter_query)
        for op in FORBIDDEN_OPERATORS:
            if op in query_str:
                raise ToolExecutionError(f"Forbidden operator: {op}")

        # 3. Orders collection: MUST have user_id filter
        if collection == "orders":
            if not user.is_authenticated:
                raise ToolExecutionError("Orders require authentication")
            # Force inject user_id filter
            filter_query["user_id"] = user.id
```

---

## 9. Docker & Infrastructure Setup

### 9.1 `docker-compose.yml`

```yaml
version: "3.9"

services:
  mongodb-chat:
    image: mongo:7.0
    container_name: petbot_chat_db
    ports:
      - "27018:27017"          # Port 27018 để tránh conflict với website MongoDB
    environment:
      MONGO_INITDB_ROOT_USERNAME: petbot
      MONGO_INITDB_ROOT_PASSWORD: petbot_secret
      MONGO_INITDB_DATABASE: petbot_chat
    volumes:
      - mongo_chat_data:/data/db
    networks:
      - petbot_net

  qdrant:
    image: qdrant/qdrant:v1.9.0
    container_name: petbot_qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - petbot_net

  petbot-server:
    build: .
    container_name: petbot_server
    ports:
      - "8000:8000"
    environment:
      - MONGODB_CHAT_URI=mongodb://petbot:petbot_secret@mongodb-chat:27017/petbot_chat
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
    depends_on:
      - mongodb-chat
      - qdrant
    networks:
      - petbot_net
    volumes:
      - ./src:/app/src

volumes:
  mongo_chat_data:
  qdrant_data:

networks:
  petbot_net:
    driver: bridge
```

### 9.2 `.env.example`

```env
# App
APP_ENV=development
LOG_LEVEL=INFO

# LLM
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# Tavily
TAVILY_API_KEY=tvly-...

# MongoDB (Chat DB - Docker)
MONGODB_CHAT_URI=mongodb://petbot:petbot_secret@localhost:27018/petbot_chat

# MongoDB (Website DB - existing)
MONGODB_WEBSITE_URI=mongodb://...@localhost:27017/pet_website

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=pet_knowledge_base

# Auth
JWT_SECRET=...
JWT_ALGORITHM=HS256

# Session
MAX_HISTORY_MESSAGES=20         # Số messages đưa vào context
SUMMARY_TRIGGER_EVERY=10        # Summary sau mỗi N messages
MAX_TOOL_ITERATIONS=5           # Giới hạn vòng lặp agent
```

---

## 10. Tech Stack & Dependencies

### 10.1 Core Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.11"

# API Framework
fastapi = "^0.115"
uvicorn = {extras = ["standard"], version = "^0.30"}

# AI / Agent
langchain = "^0.3"
langgraph = "^0.2"
langchain-openai = "^0.2"
langchain-anthropic = "^0.2"
langchain-google-genai = "^2.0"
langchain-ollama = "^0.2"
tavily-python = "^0.5"

# Vector DB
qdrant-client = "^1.9"

# Database
motor = "^3.5"                  # Async MongoDB driver
pymongo = "^4.8"

# Config & Validation
pydantic = "^2.8"
pydantic-settings = "^2.4"
python-dotenv = "^1.0"

# Auth
python-jose = {extras = ["cryptography"], version = "^3.3"}

# Utilities
httpx = "^0.27"
tenacity = "^8.5"               # Retry logic
structlog = "^24.4"             # Structured logging
```

---

## 11. Implementation Plan

### Phase 1 — Foundation

**Mục tiêu:** Khung dự án + kết nối cơ sở hạ tầng hoạt động.

| Task | Chi tiết |
|---|---|
| 1.1 | Setup project với Poetry/uv, cấu trúc thư mục |
| 1.2 | Viết `Settings` (Pydantic BaseSettings), load `.env` |
| 1.3 | Docker Compose: MongoDB (chat) + Qdrant up & running |
| 1.4 | Implement `MongoClient` singleton (motor async) |
| 1.5 | Implement `QdrantClient` singleton |
| 1.6 | Tạo tất cả Domain Entities + Value Objects |
| 1.7 | Định nghĩa tất cả Ports (abstract interfaces) |
| 1.8 | Tạo MongoDB indexes cho chat collections |
| 1.9 | Script seed dữ liệu vào Qdrant (pet knowledge base) |

**Deliverable:** `docker compose up` → MongoDB + Qdrant online. DB connections pass health check.

---

### Phase 2 — LLM Adapter System

**Mục tiêu:** LLM pluggable, có thể swap provider qua config.

| Task | Chi tiết |
|---|---|
| 2.1 | Implement `OpenAIAdapter` (chat + embed) |
| 2.2 | Implement `AnthropicAdapter` |
| 2.3 | Implement `GeminiAdapter` |
| 2.4 | Implement `OllamaAdapter` (local dev/testing) |
| 2.5 | Implement `LLMFactory` với registry pattern |
| 2.6 | Unit tests cho mỗi adapter (mock API calls) |
| 2.7 | Implement retry logic với tenacity (3 retries, exponential backoff) |
| 2.8 | Implement `LLMResponse` dataclass chuẩn hóa output |

**Deliverable:** `LLMFactory.create("openai", "gpt-4o-mini").chat([...])` hoạt động.

---

### Phase 3 — Tools Implementation

**Mục tiêu:** Ba tools chính hoạt động độc lập và có thể test riêng.

| Task | Chi tiết |
|---|---|
| 3.1 | Implement `TavilyWebSearchTool` (async, result formatting) |
| 3.2 | Implement `QdrantVectorSearchTool` (embed → search → format) |
| 3.3 | Implement `MongoDBSchemaContext` — load schema để inject vào prompt |
| 3.4 | Implement `MongoQueryGenerator` — LLM gen filter/projection từ schema + query |
| 3.5 | Implement `MongoQueryValidator` — whitelist + forbidden operator check |
| 3.6 | Implement `MongoQueryExecutor` — chạy query thực tế lên website MongoDB |
| 3.7 | Implement `ToolRegistry` — map tool_name → tool instance |
| 3.8 | Integration tests: mỗi tool với real data |

**Deliverable:** Có thể gọi từng tool trực tiếp, nhận kết quả đúng.

---

### Phase 4 — Agent Orchestrator

**Mục tiêu:** LangGraph agent multi-step reasoning hoạt động end-to-end.

| Task | Chi tiết |
|---|---|
| 4.1 | Thiết kế `AgentState` TypedDict đầy đủ |
| 4.2 | Implement `intent_analyzer_node` — phân tích query → tool selection JSON |
| 4.3 | Implement `tool_executor_node` — dispatch tới ToolRegistry, gọi tool |
| 4.4 | Implement `context_merger_node` — merge tool results → unified context |
| 4.5 | Implement `response_generator_node` — LLM final answer |
| 4.6 | Build LangGraph `StateGraph` kết nối các nodes |
| 4.7 | Implement conditional edges (có cần tool thêm không?) |
| 4.8 | Add iteration limit guard (MAX_TOOL_ITERATIONS) |
| 4.9 | Viết system prompt + intent prompt |
| 4.10 | Viết mongo_gen_prompt với schema injection |

**Deliverable:** Agent nhận query → chạy multi-step → trả final answer (chưa có API).

---

### Phase 5 — Session & History System

**Mục tiêu:** Lưu trữ, truy vấn, và tóm tắt lịch sử hội thoại.

| Task | Chi tiết |
|---|---|
| 5.1 | Implement `SessionRepository` (CRUD với Motor) |
| 5.2 | Implement `HistoryRepository` (insert/query messages) |
| 5.3 | Implement `CreateSessionUseCase` |
| 5.4 | Implement `GetSessionHistoryUseCase` |
| 5.5 | Implement `ContextBuilder` (history + summary → messages list) |
| 5.6 | Implement `SummarizeSessionUseCase` (async background task) |
| 5.7 | Implement `PermissionService` (guest vs authenticated) |
| 5.8 | Implement `ResolveUserContextUseCase` |
| 5.9 | Wire history writer vào agent graph (post-response node) |
| 5.10 | Background task: auto-summarize khi đủ điều kiện |

**Deliverable:** Authenticated user → sessions persist → history queryable → summary tự động cập nhật.

---

### Phase 6 — API Layer

**Mục tiêu:** REST API + SSE streaming hoạt động, connect đến agent.

| Task | Chi tiết |
|---|---|
| 6.1 | Setup FastAPI app, router v1 |
| 6.2 | Implement `AuthMiddleware` — validate JWT (optional header) |
| 6.3 | Implement `POST /api/v1/chat` (streaming SSE + JSON mode) |
| 6.4 | Implement `GET /api/v1/sessions` |
| 6.5 | Implement `GET /api/v1/sessions/{id}/history` |
| 6.6 | Implement `DELETE /api/v1/sessions/{id}` |
| 6.7 | Implement `GET /api/v1/health` |
| 6.8 | Setup CORS middleware cho website domain |
| 6.9 | Implement Dependency Injection toàn bộ với FastAPI `Depends()` |
| 6.10 | Error handling global (HTTPException mapper) |

**Deliverable:** `curl POST /api/v1/chat` → nhận SSE stream với tool_calls + final answer.

---

### Phase 7 — Testing & Hardening

| Task | Chi tiết |
|---|---|
| 7.1 | Unit tests: Domain entities + Value Objects |
| 7.2 | Unit tests: Use Cases (mock repositories) |
| 7.3 | Unit tests: LLM Adapters (mock HTTP) |
| 7.4 | Unit tests: MongoQueryValidator |
| 7.5 | Integration tests: Full chat flow (test MongoDB + Qdrant) |
| 7.6 | Integration tests: Session persistence |
| 7.7 | Performance: đảm bảo response < 5s (P95) |
| 7.8 | Add structured logging với structlog |
| 7.9 | Rate limiting (slowapi hoặc middleware tự viết) |
| 7.10 | Final Docker build + production config |

---

## 12. Các Điểm Quan Trọng Cần Lưu Ý

### Security

- MongoDB query generator **LUÔN** validate output trước khi chạy. LLM output là untrusted input.
- `orders` collection **LUÔN** inject `user_id` filter từ JWT, không tin vào LLM-generated filter.
- Giới hạn `limit` tối đa 50 documents mỗi query MongoDB.
- JWT secret không bao giờ đặt trong code, chỉ `.env`.

### Performance

- Dùng `motor` (async MongoDB driver) — không bao giờ block event loop.
- Tool calls chạy **parallel** khi không phụ thuộc nhau (dùng `asyncio.gather`).
- Embedding được cache trong request scope để tránh duplicate API calls.
- MongoDB chat queries nên cover bởi indexes (session_id + timestamp).

### Extensibility

- Thêm LLM provider mới: chỉ cần tạo file `xxx_adapter.py`, đăng ký vào `LLMFactory._registry`.
- Thêm tool mới: implement interface `ITool`, đăng ký vào `ToolRegistry`, cập nhật intent prompt.
- Thêm collection MongoDB mới: cập nhật `WEBSITE_DB_SCHEMA` và `ALLOWED_COLLECTIONS`.

### Observability

- Mỗi request log: `session_id`, `user_id`, `tools_used`, `token_count`, `latency_ms`.
- Tool execution log: `tool_name`, `input_summary`, `result_count`, `execution_time_ms`.
- Structured JSON logs để dễ đẩy lên ELK/Datadog sau này.

---

*Document này là living spec — cập nhật khi requirements thay đổi hoặc khi implementation phát hiện edge cases mới.*