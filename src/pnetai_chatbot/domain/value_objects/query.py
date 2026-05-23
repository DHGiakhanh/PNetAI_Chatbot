"""UserQuery value object."""

from datetime import datetime

from pydantic import BaseModel, Field

from pnetai_chatbot.domain.entities.user import User
from pnetai_chatbot.domain.value_objects.session_id import SessionId


class UserQuery(BaseModel):
    """Value object representing a user's query to the chatbot."""

    raw_text: str = Field(..., min_length=1, description="The raw query text")
    session_id: SessionId = Field(description="Session this query belongs to")
    user: User = Field(description="The user who sent the query")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the query was received",
    )

    model_config = {"arbitrary_types_allowed": True}
