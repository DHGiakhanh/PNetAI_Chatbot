from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    id: str
    session_id: str
    role: str
    content: str
    timestamp: datetime
