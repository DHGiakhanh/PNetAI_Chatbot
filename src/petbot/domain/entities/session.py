from dataclasses import dataclass
from datetime import datetime

@dataclass
class ChatSession:
    id: str
    user_id: str | None
    is_authenticated: bool
    created_at: datetime
    updated_at: datetime
