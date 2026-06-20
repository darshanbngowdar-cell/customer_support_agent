from __future__ import annotations

from pydantic import BaseModel, Field, constr

UserMessage = constr(strip_whitespace=True, min_length=1, max_length=2000)
SessionId = constr(
    strip_whitespace=True,
    min_length=1,
    max_length=100,
    pattern=r"^[A-Za-z0-9_-]+$",
)


class SupportRequest(BaseModel):
    message: UserMessage
    session_id: SessionId = Field(default="default")
    conversation_history: list[UserMessage] = Field(default_factory=list)
